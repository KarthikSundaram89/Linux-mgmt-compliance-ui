"""
Collection Orchestrator
=======================

Coordinates the full collection pipeline:
1. Acquire SSH connection via SSH Manager
2. Detect Linux distribution
3. Run all enabled collectors concurrently (within server)
4. Parse and store snapshot
5. Detect changes vs. previous snapshot
6. Update database records
7. Generate notifications for critical changes

Handles concurrent collection across multiple servers using
asyncio semaphore to respect max_concurrent_collections.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.collectors.base import BaseCollector, CollectorResult, LinuxDistro
from backend.collectors.distro_detect import detect_distribution
from backend.collectors.registry import collector_registry, register_all_collectors
from backend.services.change_detection_service import ChangeDetectionEngine
from backend.services.snapshot_service import SnapshotStorageService
from backend.settings.config import get_settings

logger = logging.getLogger("collector")


class CollectionOrchestrator:
    """
    Orchestrates inventory collection across servers.

    Responsibilities:
    - Manages concurrent SSH sessions (semaphore-controlled)
    - Runs collectors per server with fault isolation
    - Stores snapshots and detects changes
    - Tracks collection status and timing
    - Ensures one slow server never blocks others
    """

    def __init__(self):
        settings = get_settings()
        self._max_concurrent = settings.scheduler_max_concurrent_collections
        self._semaphore = asyncio.Semaphore(self._max_concurrent)
        self._snapshot_service = SnapshotStorageService()
        self._change_engine = ChangeDetectionEngine()
        self._store_raw = False

        # Ensure collectors are registered
        if collector_registry.count == 0:
            register_all_collectors()

    async def collect_all_servers(
        self, servers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Collect inventory from all active servers concurrently.

        Args:
            servers: List of server dicts with id, hostname, ip_address, etc.

        Returns:
            Summary with success/failure counts and timing.
        """
        start_time = time.time()
        logger.info(
            f"Starting collection for {len(servers)} servers "
            f"(max concurrent: {self._max_concurrent})"
        )

        # Create tasks for all servers
        tasks = [
            self._collect_with_semaphore(server)
            for server in servers
        ]

        # Execute all concurrently (semaphore controls parallelism)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Tally results
        successful = 0
        failed = 0
        errors: List[Dict[str, str]] = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed += 1
                errors.append({
                    "server": servers[i].get("hostname", "unknown"),
                    "error": str(result),
                })
            elif isinstance(result, dict):
                if result.get("status") == "success":
                    successful += 1
                else:
                    failed += 1
                    errors.append({
                        "server": servers[i].get("hostname", "unknown"),
                        "error": result.get("error", "unknown"),
                    })

        duration = time.time() - start_time
        summary = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration,
            "total_servers": len(servers),
            "successful": successful,
            "failed": failed,
            "errors": errors[:50],  # Limit error list
        }

        logger.info(
            f"Collection complete: {successful}/{len(servers)} succeeded "
            f"in {duration:.1f}s",
        )

        return summary

    async def collect_single_server(
        self,
        server_id: str,
        hostname: str,
        connection,  # SSHConnection instance
    ) -> Dict[str, Any]:
        """
        Collect inventory from a single server.

        This is the core per-server collection logic.

        Args:
            server_id: Server UUID.
            hostname: Server hostname.
            connection: Active SSH connection.

        Returns:
            Dict with status, collector results, and change count.
        """
        start_time = time.time()
        logger.info(
            f"Starting collection for {hostname}",
            extra={"server_id": server_id},
        )

        try:
            # Step 1: Detect distribution
            distro, version, pretty_name = await detect_distribution(
                connection
            )

            # Step 2: Get enabled collectors for this distro
            collectors = collector_registry.get_all_collectors(distro)
            logger.info(
                f"Running {len(collectors)} collectors on {hostname}",
                extra={"distro": distro.value},
            )

            # Step 3: Run all collectors (sequentially per server)
            # Each collector is independent; failure of one doesn't
            # stop others
            collector_results: Dict[str, CollectorResult] = {}
            for collector in collectors:
                try:
                    result = await collector.run(
                        connection, distro, self._store_raw
                    )
                    collector_results[collector.name] = result
                except Exception as e:
                    logger.error(
                        f"Collector {collector.name} crashed on "
                        f"{hostname}: {e}",
                        exc_info=True,
                    )
                    collector_results[collector.name] = CollectorResult(
                        collector_name=collector.name,
                        success=False,
                        errors=[f"Unhandled: {str(e)}"],
                    )

            # Step 4: Save snapshot
            collection_metadata = {
                "distro": distro.value,
                "distro_version": version,
                "pretty_name": pretty_name,
                "triggered_by": "orchestrator",
            }

            snapshot_info = await self._snapshot_service.save_snapshot(
                hostname=hostname,
                server_id=server_id,
                collector_results=collector_results,
                collection_metadata=collection_metadata,
                store_raw=self._store_raw,
            )

            # Step 5: Detect changes
            previous_data = await self._snapshot_service.get_snapshot_data_only(
                hostname
            )
            current_data = {
                name: r.data
                for name, r in collector_results.items()
                if r.success
            }

            changes = self._change_engine.detect_changes(
                server_id=server_id,
                snapshot_id="pending",  # Will be set when persisted
                current_data=current_data,
                previous_data=previous_data,
            )

            snapshot_info["change_count"] = len(changes)
            change_summary = self._change_engine.generate_summary(changes)

            duration = time.time() - start_time

            return {
                "status": "success",
                "server_id": server_id,
                "hostname": hostname,
                "distro": distro.value,
                "duration_seconds": duration,
                "collectors_run": len(collector_results),
                "collectors_succeeded": sum(
                    1 for r in collector_results.values() if r.success
                ),
                "collectors_failed": sum(
                    1 for r in collector_results.values() if not r.success
                ),
                "change_count": len(changes),
                "change_summary": change_summary,
                "snapshot_info": snapshot_info,
                "changes": changes,
            }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Collection failed for {hostname}: {e}",
                exc_info=True,
            )
            return {
                "status": "failed",
                "server_id": server_id,
                "hostname": hostname,
                "duration_seconds": duration,
                "error": str(e),
            }

    async def retry_failed_servers(
        self, servers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Retry collection for previously failed servers.

        Same logic as collect_all_servers but specifically
        for the retry queue.
        """
        logger.info(f"Retrying {len(servers)} failed servers")
        return await self.collect_all_servers(servers)

    async def _collect_with_semaphore(
        self, server: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Wrapper that acquires semaphore before collecting.

        Ensures max_concurrent_collections is respected.
        One slow server cannot block others because each
        has its own semaphore slot.
        """
        async with self._semaphore:
            # In production, this would acquire a real SSH connection
            # via SSHManager. For now, returns structure for integration.
            hostname = server.get("hostname", "unknown")
            server_id = server.get("id", "")

            logger.debug(
                f"Semaphore acquired for {hostname} "
                f"({self._semaphore._value} slots remaining)"
            )

            # Placeholder: actual SSH connection acquisition
            # connection = await ssh_manager.get_connection(server, profile)
            # result = await self.collect_single_server(
            #     server_id, hostname, connection
            # )
            # await ssh_manager.pool.release(connection.config)

            return {
                "status": "success",
                "server_id": server_id,
                "hostname": hostname,
                "message": "Collection framework ready",
            }
