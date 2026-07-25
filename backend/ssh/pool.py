"""
SSH Connection Pool
===================

Manages a pool of SSH connections with automatic cleanup
of idle connections and connection reuse.
"""

import asyncio
import logging
import time
from typing import Dict, Optional

from backend.ssh.connection import SSHConnection, SSHConnectionConfig

logger = logging.getLogger("collector")


class SSHConnectionPool:
    """
    Pool of SSH connections with automatic lifecycle management.
    
    Features:
    - Connection reuse for the same host
    - Automatic cleanup of idle connections
    - Configurable maximum pool size
    - Thread-safe connection acquisition
    
    Attributes:
        max_size: Maximum number of connections in the pool.
        idle_timeout: Seconds after which idle connections are closed.
    """
    
    def __init__(
        self,
        max_size: int = 50,
        idle_timeout: int = 300,
    ):
        self._max_size = max_size
        self._idle_timeout = idle_timeout
        self._connections: Dict[str, SSHConnection] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
    
    @property
    def size(self) -> int:
        """Current number of connections in the pool."""
        return len(self._connections)
    
    @property
    def max_size(self) -> int:
        """Maximum pool size."""
        return self._max_size
    
    def _connection_key(self, config: SSHConnectionConfig) -> str:
        """Generate a unique key for a connection configuration."""
        return f"{config.hostname}:{config.port}:{config.username}"
    
    async def acquire(
        self, config: SSHConnectionConfig
    ) -> SSHConnection:
        """
        Acquire a connection from the pool or create a new one.
        
        If a healthy connection for the same host exists in the pool,
        it is reused. Otherwise, a new connection is created.
        
        Args:
            config: SSH connection configuration.
        
        Returns:
            SSHConnection: An active SSH connection.
        
        Raises:
            RuntimeError: If pool is at capacity.
        """
        key = self._connection_key(config)
        
        async with self._lock:
            # Check for existing connection
            if key in self._connections:
                conn = self._connections[key]
                if conn.is_connected:
                    return conn
                else:
                    # Remove dead connection
                    del self._connections[key]
            
            # Check pool capacity
            if len(self._connections) >= self._max_size:
                # Try to evict idle connections
                await self._evict_idle()
                if len(self._connections) >= self._max_size:
                    raise RuntimeError(
                        f"SSH connection pool exhausted "
                        f"(max={self._max_size})"
                    )
            
            # Create new connection
            conn = SSHConnection(config)
            await conn.connect()
            self._connections[key] = conn
            
            logger.debug(
                "Connection acquired from pool",
                extra={
                    "hostname": config.hostname,
                    "pool_size": len(self._connections),
                },
            )
            
            return conn
    
    async def release(self, config: SSHConnectionConfig) -> None:
        """
        Release a connection back to the pool.
        
        The connection remains in the pool for reuse.
        It will be cleaned up when idle timeout expires.
        
        Args:
            config: SSH connection configuration.
        """
        # Connection stays in pool for reuse
        # Idle cleanup will handle removal
        key = self._connection_key(config)
        logger.debug(
            "Connection released to pool",
            extra={"hostname": config.hostname, "key": key},
        )
    
    async def remove(self, config: SSHConnectionConfig) -> None:
        """
        Remove and close a specific connection from the pool.
        
        Args:
            config: SSH connection configuration.
        """
        key = self._connection_key(config)
        async with self._lock:
            if key in self._connections:
                conn = self._connections.pop(key)
                await conn.disconnect()
    
    async def _evict_idle(self) -> None:
        """Remove connections that have been idle too long."""
        now = time.time()
        to_remove = []
        
        for key, conn in self._connections.items():
            if conn.idle_time > self._idle_timeout:
                to_remove.append(key)
        
        for key in to_remove:
            conn = self._connections.pop(key)
            await conn.disconnect()
            logger.debug(
                "Evicted idle connection",
                extra={"key": key},
            )
    
    async def start_cleanup_loop(self) -> None:
        """Start the background cleanup task."""
        self._cleanup_task = asyncio.create_task(
            self._cleanup_loop()
        )
    
    async def _cleanup_loop(self) -> None:
        """Periodically clean up idle connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                async with self._lock:
                    await self._evict_idle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"Connection pool cleanup error: {e}"
                )
    
    async def close_all(self) -> None:
        """Close all connections and shut down the pool."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        async with self._lock:
            for key, conn in list(self._connections.items()):
                await conn.disconnect()
            self._connections.clear()
        
        logger.info("SSH connection pool closed")
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all pooled connections.
        
        Returns:
            Dict mapping connection keys to health status.
        """
        health = {}
        async with self._lock:
            for key, conn in self._connections.items():
                health[key] = conn.is_connected
        return health
