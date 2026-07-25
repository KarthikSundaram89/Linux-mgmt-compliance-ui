"""
Snapshot Storage Service
========================

Enhanced snapshot management with collection metadata,
compression, integrity verification, and retention policies.

Snapshots are stored as:
  storage/snapshots/{hostname}/{YYYY-MM-DD_HH-MM-SS}.json.gz
"""

import gzip
import hashlib
import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.collectors.base import CollectorResult
from backend.settings.config import get_settings

logger = logging.getLogger("collector")


class SnapshotStorageService:
    """
    Manages inventory snapshot files on disk.

    Features:
    - Compressed storage (gzip level 6)
    - SHA-256 checksums for integrity
    - Full metadata envelope (collection info + results)
    - Configurable raw output storage
    - Retention policy enforcement
    """

    def __init__(self):
        settings = get_settings()
        self._base_path = settings.snapshots_path
        self._retention_days = settings.snapshot_retention_days
        self._base_path.mkdir(parents=True, exist_ok=True)

    def get_snapshot_path(
        self, hostname: str, collected_at: datetime
    ) -> Path:
        """Get the file path for a snapshot."""
        ts = collected_at.strftime("%Y-%m-%d_%H-%M-%S")
        return self._base_path / hostname / f"{ts}.json.gz"

    async def save_snapshot(
        self,
        hostname: str,
        server_id: str,
        collector_results: Dict[str, CollectorResult],
        collection_metadata: Dict[str, Any],
        store_raw: bool = False,
    ) -> Dict[str, Any]:
        """
        Save a complete inventory snapshot.

        Args:
            hostname: Server hostname.
            server_id: Server UUID.
            collector_results: Map of collector_name -> CollectorResult.
            collection_metadata: Additional collection metadata.
            store_raw: Whether to include raw command outputs.

        Returns:
            Dict with file_path, file_size, checksum, and metadata.
        """
        collected_at = datetime.now(timezone.utc)

        # Build snapshot envelope
        snapshot = {
            "_metadata": {
                "server_id": server_id,
                "hostname": hostname,
                "collected_at": collected_at.isoformat(),
                "snapshot_version": "2.0",
                "collectors_run": [],
                "collectors_succeeded": [],
                "collectors_failed": [],
                "total_duration_seconds": 0.0,
                "total_commands_run": 0,
                **collection_metadata,
            },
            "_summary": {
                "total_collectors": len(collector_results),
                "successful": 0,
                "failed": 0,
                "warnings": 0,
            },
        }

        total_duration = 0.0
        total_commands = 0

        for name, result in collector_results.items():
            # Metadata tracking
            snapshot["_metadata"]["collectors_run"].append(name)
            total_duration += result.duration_seconds
            total_commands += result.commands_run

            if result.success:
                snapshot["_metadata"]["collectors_succeeded"].append(name)
                snapshot["_summary"]["successful"] += 1
            else:
                snapshot["_metadata"]["collectors_failed"].append(name)
                snapshot["_summary"]["failed"] += 1

            snapshot["_summary"]["warnings"] += len(result.warnings)

            # Store collector data
            snapshot[name] = {
                "data": result.data,
                "success": result.success,
                "duration_seconds": result.duration_seconds,
                "commands_run": result.commands_run,
                "warnings": result.warnings,
                "errors": result.errors,
                "metadata": result.metadata,
            }

            # Optionally store raw outputs
            if store_raw and result.raw_outputs:
                snapshot[name]["raw_outputs"] = result.raw_outputs

        snapshot["_metadata"]["total_duration_seconds"] = total_duration
        snapshot["_metadata"]["total_commands_run"] = total_commands

        # Write to disk
        file_path = self.get_snapshot_path(hostname, collected_at)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        json_bytes = json.dumps(
            snapshot, indent=2, default=str
        ).encode("utf-8")

        compressed = gzip.compress(json_bytes, compresslevel=6)
        checksum = hashlib.sha256(compressed).hexdigest()

        with open(file_path, "wb") as f:
            f.write(compressed)

        file_size = os.path.getsize(file_path)
        relative_path = str(file_path.relative_to(self._base_path.parent))

        logger.info(
            "Snapshot saved",
            extra={
                "hostname": hostname,
                "file_path": relative_path,
                "file_size": file_size,
                "checksum": checksum[:12],
                "collectors": len(collector_results),
            },
        )

        return {
            "file_path": relative_path,
            "file_size_bytes": file_size,
            "checksum": checksum,
            "collected_at": collected_at,
            "collectors_run": list(collector_results.keys()),
            "os_family": self._extract_os_family(collector_results),
            "os_version": self._extract_os_version(collector_results),
            "kernel_version": self._extract_kernel(collector_results),
            "change_count": 0,  # Set by caller after detection
        }

    async def load_snapshot(
        self, hostname: str, collected_at: datetime
    ) -> Optional[Dict[str, Any]]:
        """Load a snapshot by hostname and timestamp."""
        file_path = self.get_snapshot_path(hostname, collected_at)
        if not file_path.exists():
            return None
        with gzip.open(file_path, "rb") as f:
            return json.loads(f.read().decode("utf-8"))

    async def load_latest_snapshot(
        self, hostname: str
    ) -> Optional[Dict[str, Any]]:
        """Load the most recent snapshot for a server."""
        server_dir = self._base_path / hostname
        if not server_dir.exists():
            return None

        snapshot_files = sorted(
            server_dir.glob("*.json.gz"), reverse=True
        )
        if not snapshot_files:
            return None

        with gzip.open(snapshot_files[0], "rb") as f:
            return json.loads(f.read().decode("utf-8"))

    async def get_snapshot_data_only(
        self, hostname: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load only the data portions of the latest snapshot.

        Returns a dict of {collector_name: data} for comparison.
        """
        snapshot = await self.load_latest_snapshot(hostname)
        if not snapshot:
            return None

        data = {}
        for key, value in snapshot.items():
            if key.startswith("_"):
                continue
            if isinstance(value, dict) and "data" in value:
                data[key] = value["data"]
        return data

    async def verify_integrity(
        self, file_path: str, expected_checksum: str
    ) -> bool:
        """Verify a snapshot file's SHA-256 checksum."""
        full_path = self._base_path.parent / file_path
        if not full_path.exists():
            return False
        with open(full_path, "rb") as f:
            actual = hashlib.sha256(f.read()).hexdigest()
        return actual == expected_checksum

    async def list_snapshots(
        self, hostname: str
    ) -> List[Dict[str, Any]]:
        """List all snapshots for a server with metadata."""
        server_dir = self._base_path / hostname
        if not server_dir.exists():
            return []

        snapshots = []
        for f in sorted(server_dir.glob("*.json.gz"), reverse=True):
            snapshots.append({
                "filename": f.name,
                "file_size": f.stat().st_size,
                "timestamp": f.stem,  # YYYY-MM-DD_HH-MM-SS
            })
        return snapshots

    async def cleanup_old_snapshots(self) -> int:
        """Remove snapshots older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(
            days=self._retention_days
        )
        removed = 0

        if not self._base_path.exists():
            return 0

        for server_dir in self._base_path.iterdir():
            if not server_dir.is_dir():
                continue
            for snapshot_file in server_dir.glob("*.json.gz"):
                try:
                    ts_str = snapshot_file.stem  # YYYY-MM-DD_HH-MM-SS
                    file_dt = datetime.strptime(
                        ts_str, "%Y-%m-%d_%H-%M-%S"
                    ).replace(tzinfo=timezone.utc)
                    if file_dt < cutoff:
                        snapshot_file.unlink()
                        removed += 1
                except (ValueError, OSError):
                    continue

        if removed:
            logger.info(f"Cleaned up {removed} old snapshots")
        return removed

    def _extract_os_family(self, results: Dict[str, CollectorResult]) -> str:
        """Extract OS family from collector results."""
        os_result = results.get("operating_system")
        if os_result and os_result.success:
            return os_result.data.get("distribution", "")
        return ""

    def _extract_os_version(self, results: Dict[str, CollectorResult]) -> str:
        """Extract OS version from collector results."""
        os_result = results.get("operating_system")
        if os_result and os_result.success:
            return os_result.data.get("distribution_version", "")
        return ""

    def _extract_kernel(self, results: Dict[str, CollectorResult]) -> str:
        """Extract kernel version from collector results."""
        os_result = results.get("operating_system")
        if os_result and os_result.success:
            return os_result.data.get("kernel_release", "")
        return ""
