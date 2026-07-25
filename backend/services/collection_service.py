"""
Collection Service
==================

Orchestrates the inventory collection process.
Coordinates between SSH, collectors, parsers, and storage.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List

from backend.settings.config import get_settings

logger = logging.getLogger("collector")


class CollectionService:
    """
    Orchestrates inventory collection across servers.
    
    Manages concurrent collection sessions, delegates to
    individual collectors, and coordinates storage.
    
    This is the central entry point that the scheduler calls.
    Full implementation in Phase 2 when collectors are built.
    """
    
    def __init__(self):
        self._settings = get_settings()
        self._max_concurrent = (
            self._settings.scheduler_max_concurrent_collections
        )
    
    async def collect_all_servers(self) -> dict:
        """
        Collect inventory from all active servers.
        
        Uses a semaphore to limit concurrent SSH sessions.
        One slow server never blocks others.
        
        Returns:
            Summary dict with success/failure counts.
        """
        logger.info("Starting full collection run")
        
        # Phase 2: Get active servers from repository
        # Phase 2: Create semaphore for concurrency control
        # Phase 2: Run collectors for each server
        
        return {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "total_servers": 0,
            "successful": 0,
            "failed": 0,
        }
    
    async def retry_failed_servers(self) -> dict:
        """
        Retry collection for servers that previously failed.
        
        Only retries servers with last_collection_status == "failed".
        
        Returns:
            Summary dict with retry results.
        """
        logger.info("Starting retry of failed servers")
        
        # Phase 2: Get failed servers
        # Phase 2: Retry each with semaphore control
        
        return {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "retried": 0,
            "successful": 0,
            "still_failed": 0,
        }
    
    async def collect_single_server(
        self, server_id: str
    ) -> dict:
        """
        Collect inventory from a single server.
        
        Args:
            server_id: Server to collect.
        
        Returns:
            Collection result dict.
        """
        logger.info(
            "Collecting single server",
            extra={"server_id": server_id},
        )
        
        # Phase 2: Full implementation
        return {
            "server_id": server_id,
            "status": "pending",
            "message": "Collection framework ready - "
                       "collectors to be implemented in Phase 2",
        }
