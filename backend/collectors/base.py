"""
Base Collector
==============

Abstract base class for all Linux inventory collectors.
Every collector must implement the collect() method.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.ssh.connection import CommandResult, SSHConnection

logger = logging.getLogger("collector")


@dataclass
class CollectorResult:
    """
    Standardized result returned by every collector.
    
    Attributes:
        collector_name: Name of the collector that produced this result.
        success: Whether collection completed successfully.
        data: Collected structured data (JSON-serializable).
        errors: Any errors encountered during collection.
        commands_run: Number of SSH commands executed.
        duration_seconds: Total collection time.
        metadata: Additional metadata about the collection.
    """
    
    collector_name: str
    success: bool = False
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    commands_run: int = 0
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseCollector(ABC):
    """
    Abstract base class for inventory collectors.
    
    Every collector must:
    1. Be independent (no dependencies on other collectors)
    2. Return structured JSON data
    3. Never directly update the database
    4. Handle errors gracefully (never crash the collection)
    
    Usage:
        class PackageCollector(BaseCollector):
            name = "packages"
            
            async def collect(self, connection):
                result = await connection.execute("rpm -qa")
                return self.parse_output(result)
    """
    
    # Subclasses must define these
    name: str = "base"
    description: str = "Base collector"
    version: str = "1.0.0"
    
    def __init__(self):
        self._logger = logging.getLogger(f"collector.{self.name}")
    
    async def run(self, connection: SSHConnection) -> CollectorResult:
        """
        Execute the collector with error handling and timing.
        
        This is the public method called by the collection
        orchestrator. It wraps collect() with timing and
        error handling.
        
        Args:
            connection: Active SSH connection to the target server.
        
        Returns:
            CollectorResult with collected data or error info.
        """
        start_time = time.time()
        result = CollectorResult(collector_name=self.name)
        
        try:
            self._logger.info(f"Starting {self.name} collection")
            
            data = await self.collect(connection)
            
            result.success = True
            result.data = data
            result.metadata = {
                "collector_version": self.version,
                "collector_description": self.description,
            }
            
            self._logger.info(
                f"{self.name} collection completed successfully"
            )
            
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            self._logger.error(
                f"{self.name} collection failed: {e}",
                exc_info=True,
            )
        
        result.duration_seconds = time.time() - start_time
        return result
    
    @abstractmethod
    async def collect(
        self, connection: SSHConnection
    ) -> Dict[str, Any]:
        """
        Perform the actual data collection.
        
        Subclasses must implement this method to execute
        SSH commands and parse the output into structured data.
        
        Args:
            connection: Active SSH connection to target server.
        
        Returns:
            Dictionary of collected data (JSON-serializable).
        """
        ...
    
    async def execute_command(
        self,
        connection: SSHConnection,
        command: str,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        """
        Helper to execute a command and log it.
        
        Args:
            connection: SSH connection.
            command: Command to execute.
            timeout: Optional timeout override.
        
        Returns:
            CommandResult from the SSH execution.
        """
        self._logger.debug(f"Executing: {command[:100]}")
        result = await connection.execute(command, timeout=timeout)
        
        if result.exit_code != 0 and result.stderr:
            self._logger.warning(
                f"Command returned non-zero exit code",
                extra={
                    "command": command[:100],
                    "exit_code": result.exit_code,
                    "stderr": result.stderr[:200],
                },
            )
        
        return result
