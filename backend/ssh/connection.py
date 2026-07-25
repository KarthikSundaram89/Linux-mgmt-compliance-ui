"""
SSH Connection Wrapper
======================

Encapsulates a Paramiko SSH connection with timeout management,
command execution, and automatic cleanup.
"""

import asyncio
import io
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Tuple

import paramiko

logger = logging.getLogger("collector")


@dataclass
class SSHConnectionConfig:
    """Configuration for establishing an SSH connection."""
    
    hostname: str
    port: int = 22
    username: str = "root"
    private_key: Optional[str] = None
    passphrase: Optional[str] = None
    connection_timeout: int = 30
    command_timeout: int = 60
    banner_timeout: int = 30
    auth_timeout: int = 30


@dataclass
class CommandResult:
    """Result of executing an SSH command."""
    
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    duration_seconds: float = 0.0
    timed_out: bool = False


class SSHConnection:
    """
    Wrapper around a Paramiko SSH client connection.
    
    Provides:
    - Connection establishment with key-based authentication
    - Command execution with configurable timeouts
    - Connection health checking
    - Automatic cleanup of resources
    
    Attributes:
        config: SSH connection configuration.
        client: Underlying Paramiko SSH client.
        connected_at: Timestamp when connection was established.
        last_used_at: Timestamp of last command execution.
    """
    
    def __init__(self, config: SSHConnectionConfig):
        self._config = config
        self._client: Optional[paramiko.SSHClient] = None
        self._connected_at: Optional[float] = None
        self._last_used_at: Optional[float] = None
        self._lock = asyncio.Lock()
    
    @property
    def config(self) -> SSHConnectionConfig:
        """Get the connection configuration."""
        return self._config
    
    @property
    def is_connected(self) -> bool:
        """Check if the connection is active."""
        if self._client is None:
            return False
        transport = self._client.get_transport()
        return transport is not None and transport.is_active()
    
    @property
    def connected_at(self) -> Optional[float]:
        """Timestamp when connection was established."""
        return self._connected_at
    
    @property
    def last_used_at(self) -> Optional[float]:
        """Timestamp of last command execution."""
        return self._last_used_at
    
    @property
    def idle_time(self) -> float:
        """Seconds since last use."""
        if self._last_used_at is None:
            return 0.0
        return time.time() - self._last_used_at
    
    async def connect(self) -> None:
        """
        Establish the SSH connection.
        
        Uses key-based authentication with the private key
        retrieved from the secrets provider.
        
        Raises:
            paramiko.AuthenticationException: If auth fails.
            paramiko.SSHException: For SSH protocol errors.
            TimeoutError: If connection times out.
        """
        async with self._lock:
            if self.is_connected:
                return
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._connect_sync)
    
    def _connect_sync(self) -> None:
        """Synchronous connection establishment (runs in executor)."""
        self._client = paramiko.SSHClient()
        
        # Host key policy - use known hosts file if available
        self._client.set_missing_host_key_policy(
            paramiko.RejectPolicy()
        )
        # Load system host keys
        try:
            self._client.load_system_host_keys()
        except Exception:
            pass
        
        # Parse private key
        pkey = self._parse_private_key()
        
        self._client.connect(
            hostname=self._config.hostname,
            port=self._config.port,
            username=self._config.username,
            pkey=pkey,
            timeout=self._config.connection_timeout,
            banner_timeout=self._config.banner_timeout,
            auth_timeout=self._config.auth_timeout,
            allow_agent=False,
            look_for_keys=False,
        )
        
        self._connected_at = time.time()
        self._last_used_at = time.time()
        
        logger.info(
            "SSH connection established",
            extra={
                "hostname": self._config.hostname,
                "port": self._config.port,
                "username": self._config.username,
            },
        )
    
    def _parse_private_key(self) -> paramiko.PKey:
        """
        Parse the SSH private key from string.
        
        Supports RSA, ECDSA, and Ed25519 key types.
        
        Returns:
            paramiko.PKey: Parsed private key object.
        
        Raises:
            ValueError: If key format is not recognized.
        """
        if not self._config.private_key:
            raise ValueError("No private key provided")
        
        key_data = io.StringIO(self._config.private_key)
        passphrase = self._config.passphrase
        
        # Try each key type
        key_classes = [
            paramiko.RSAKey,
            paramiko.ECDSAKey,
            paramiko.Ed25519Key,
        ]
        
        for key_class in key_classes:
            try:
                key_data.seek(0)
                return key_class.from_private_key(
                    key_data, password=passphrase
                )
            except (paramiko.SSHException, ValueError):
                continue
        
        raise ValueError(
            "Unable to parse private key. "
            "Supported types: RSA, ECDSA, Ed25519."
        )
    
    async def execute(
        self, command: str, timeout: Optional[int] = None
    ) -> CommandResult:
        """
        Execute a command on the remote server.
        
        Args:
            command: Shell command to execute.
            timeout: Command timeout override (uses config default if None).
        
        Returns:
            CommandResult: Command output, exit code, and timing.
        """
        if not self.is_connected:
            raise RuntimeError(
                f"Not connected to {self._config.hostname}"
            )
        
        cmd_timeout = timeout or self._config.command_timeout
        loop = asyncio.get_event_loop()
        
        result = await loop.run_in_executor(
            None, self._execute_sync, command, cmd_timeout
        )
        
        self._last_used_at = time.time()
        return result
    
    def _execute_sync(
        self, command: str, timeout: int
    ) -> CommandResult:
        """Synchronous command execution (runs in executor)."""
        start_time = time.time()
        result = CommandResult()
        
        try:
            stdin, stdout, stderr = self._client.exec_command(
                command, timeout=timeout
            )
            
            # Read output
            result.stdout = stdout.read().decode("utf-8", errors="replace")
            result.stderr = stderr.read().decode("utf-8", errors="replace")
            result.exit_code = stdout.channel.recv_exit_status()
            
        except TimeoutError:
            result.timed_out = True
            result.exit_code = -1
            logger.warning(
                "SSH command timed out",
                extra={
                    "hostname": self._config.hostname,
                    "command": command[:100],
                    "timeout": timeout,
                },
            )
        except Exception as e:
            result.stderr = str(e)
            result.exit_code = -1
            logger.error(
                "SSH command execution failed",
                extra={
                    "hostname": self._config.hostname,
                    "error": str(e),
                },
            )
        
        result.duration_seconds = time.time() - start_time
        return result
    
    async def disconnect(self) -> None:
        """Close the SSH connection and release resources."""
        async with self._lock:
            if self._client:
                try:
                    self._client.close()
                except Exception:
                    pass
                finally:
                    self._client = None
                    logger.debug(
                        "SSH connection closed",
                        extra={"hostname": self._config.hostname},
                    )
    
    async def __aenter__(self) -> "SSHConnection":
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
