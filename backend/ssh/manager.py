"""
SSH Manager
===========

High-level SSH management service that integrates connection pooling,
credential resolution, and retry logic.
"""

import asyncio
import logging
from typing import Optional

from backend.models.credential_profile import CredentialProfile
from backend.models.server import Server
from backend.ssh.connection import (
    CommandResult,
    SSHConnection,
    SSHConnectionConfig,
)
from backend.ssh.pool import SSHConnectionPool
from backend.security.secrets import SecretsProvider
from backend.settings.config import Settings

logger = logging.getLogger("collector")


class SSHManager:
    """
    High-level SSH management service.
    
    Orchestrates:
    - Credential resolution from secrets provider
    - Connection pooling and reuse
    - Retry logic with exponential backoff
    - Command execution with timeout management
    
    This is the primary interface for collectors to execute
    commands on remote servers.
    """
    
    def __init__(
        self,
        settings: Settings,
        secrets_provider: SecretsProvider,
    ):
        self._settings = settings
        self._secrets_provider = secrets_provider
        self._pool = SSHConnectionPool(
            max_size=settings.ssh_max_pool_size,
            idle_timeout=settings.ssh_idle_timeout,
        )
    
    @property
    def pool(self) -> SSHConnectionPool:
        """Access the underlying connection pool."""
        return self._pool
    
    async def start(self) -> None:
        """Start the SSH manager and its cleanup loop."""
        await self._pool.start_cleanup_loop()
        logger.info("SSH Manager started")
    
    async def shutdown(self) -> None:
        """Shut down the SSH manager and close all connections."""
        await self._pool.close_all()
        logger.info("SSH Manager shut down")
    
    async def get_connection(
        self,
        server: Server,
        profile: CredentialProfile,
    ) -> SSHConnection:
        """
        Get an SSH connection for a server using its credential profile.
        
        Resolves the private key from the secrets provider and
        acquires a connection from the pool.
        
        Args:
            server: Target server.
            profile: Credential profile with secret references.
        
        Returns:
            SSHConnection: Active connection to the server.
        """
        # Resolve secrets (never stored on disk or in DB)
        private_key = await self._secrets_provider.get_secret(
            profile.secret_arn
        )
        passphrase = None
        if profile.passphrase_secret_arn:
            passphrase = await self._secrets_provider.get_secret(
                profile.passphrase_secret_arn
            )
        
        # Build connection config
        config = SSHConnectionConfig(
            hostname=server.ip_address,
            port=server.port or profile.ssh_port,
            username=profile.ssh_username,
            private_key=private_key,
            passphrase=passphrase,
            connection_timeout=profile.connection_timeout,
            command_timeout=profile.command_timeout,
        )
        
        return await self._pool.acquire(config)
    
    async def execute_command(
        self,
        server: Server,
        profile: CredentialProfile,
        command: str,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        """
        Execute a command on a remote server with retry logic.
        
        Args:
            server: Target server.
            profile: Credential profile.
            command: Shell command to execute.
            timeout: Command timeout override.
        
        Returns:
            CommandResult: Command output and status.
        """
        max_retries = profile.max_retries
        retry_delay = profile.retry_delay_seconds
        last_error: Optional[Exception] = None
        
        for attempt in range(max_retries + 1):
            try:
                conn = await self.get_connection(server, profile)
                result = await conn.execute(command, timeout=timeout)
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(
                    "SSH command failed, retrying",
                    extra={
                        "hostname": server.hostname,
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "error": str(e),
                    },
                )
                
                # Remove failed connection from pool
                if server.ip_address:
                    config = SSHConnectionConfig(
                        hostname=server.ip_address,
                        port=server.port or profile.ssh_port,
                        username=profile.ssh_username,
                    )
                    await self._pool.remove(config)
                
                if attempt < max_retries:
                    # Exponential backoff
                    delay = retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        logger.error(
            "SSH command failed after all retries",
            extra={
                "hostname": server.hostname,
                "error": str(last_error),
            },
        )
        return CommandResult(
            stderr=str(last_error),
            exit_code=-1,
        )
    
    async def test_connection(
        self,
        server: Server,
        profile: CredentialProfile,
    ) -> bool:
        """
        Test SSH connectivity to a server.
        
        Executes a simple command to verify the connection works.
        
        Args:
            server: Target server.
            profile: Credential profile.
        
        Returns:
            bool: True if connection and command succeeded.
        """
        result = await self.execute_command(
            server, profile, "echo ok", timeout=10
        )
        return result.exit_code == 0
