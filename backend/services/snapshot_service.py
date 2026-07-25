"""
Snapshot Storage Service
========================

Manages compressed JSON snapshot storage on disk.
Handles writing, reading, and retention of snapshot files.
"""

import gzip
import hashlib
import json
import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from backend.settings.config import get_settings

logger = logging.getLogger("collector")


class SnapshotStorageService:
    """
    Manages inventory snapshot files on disk.
    
    Snapshots are stored as compressed JSON files:
    storage/snapshots/{hostname}/{date}.json.gz
    
    Features:
    - Compressed storage (gzip)
    - SHA-256 checksums for integrity
    - Automatic directory creation
    - Retention policy enforcement
    """
    
    def __init__(self):
        settings = get_settings()
        self._base_path = settings.snapshots_path
        self._retention_days = settings.snapshot_retention_days
    
    def get_snapshot_path(
        self, hostname: str, collection_date: date
    ) -> Path:
        """
        Get the file path for a snapshot.
        
        Args:
            hostname: Server hostname.
            collection_date: Date of collection.
        
        Returns:
            Path to the snapshot file.
        """
        date_str = collection_date.isoformat()
        return self._base_path / hostname / f"{date_str}.json.gz"
    
    async def save_snapshot(
        self,
        hostname: str,
        data: Dict[str, Any],
        collection_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Save inventory data as a compressed JSON file.
        
        Args:
            hostname: Server hostname.
            data: Inventory data dictionary.
            collection_date: Date of collection (defaults to today).
        
        Returns:
            Dict with file_path, file_size, and checksum.
        """
        if collection_date is None:
            collection_date = date.today()
        
        file_path = self.get_snapshot_path(hostname, collection_date)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Serialize and compress
        json_bytes = json.dumps(
            data, indent=2, default=str
        ).encode("utf-8")
        
        compressed = gzip.compress(json_bytes)
        
        # Calculate checksum
        checksum = hashlib.sha256(compressed).hexdigest()
        
        # Write to disk
        with open(file_path, "wb") as f:
            f.write(compressed)
        
        file_size = os.path.getsize(file_path)
        
        logger.info(
            "Snapshot saved",
            extra={
                "hostname": hostname,
                "file_path": str(file_path),
                "file_size": file_size,
                "checksum": checksum[:12],
            },
        )
        
        return {
            "file_path": str(
                file_path.relative_to(self._base_path.parent)
            ),
            "file_size_bytes": file_size,
            "checksum": checksum,
        }
    
    async def load_snapshot(
        self, hostname: str, collection_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Load a snapshot from disk.
        
        Args:
            hostname: Server hostname.
            collection_date: Date of the snapshot.
        
        Returns:
            Parsed inventory data dictionary, or None if not found.
        """
        file_path = self.get_snapshot_path(hostname, collection_date)
        
        if not file_path.exists():
            return None
        
        with gzip.open(file_path, "rb") as f:
            json_bytes = f.read()
        
        return json.loads(json_bytes.decode("utf-8"))
    
    async def load_latest_snapshot(
        self, hostname: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load the most recent snapshot for a server.
        
        Args:
            hostname: Server hostname.
        
        Returns:
            Most recent snapshot data, or None.
        """
        server_dir = self._base_path / hostname
        
        if not server_dir.exists():
            return None
        
        # Find most recent snapshot file
        snapshot_files = sorted(
            server_dir.glob("*.json.gz"), reverse=True
        )
        
        if not snapshot_files:
            return None
        
        with gzip.open(snapshot_files[0], "rb") as f:
            json_bytes = f.read()
        
        return json.loads(json_bytes.decode("utf-8"))
    
    async def verify_integrity(
        self, file_path: str, expected_checksum: str
    ) -> bool:
        """
        Verify a snapshot file's integrity using its checksum.
        
        Args:
            file_path: Path to the snapshot file.
            expected_checksum: Expected SHA-256 hash.
        
        Returns:
            True if the file matches the expected checksum.
        """
        full_path = self._base_path.parent / file_path
        
        if not full_path.exists():
            return False
        
        with open(full_path, "rb") as f:
            actual_checksum = hashlib.sha256(f.read()).hexdigest()
        
        return actual_checksum == expected_checksum
    
    async def cleanup_old_snapshots(self) -> int:
        """
        Remove snapshots older than the retention period.
        
        Returns:
            Number of files removed.
        """
        from datetime import timedelta
        
        cutoff = date.today() - timedelta(days=self._retention_days)
        removed = 0
        
        if not self._base_path.exists():
            return 0
        
        for server_dir in self._base_path.iterdir():
            if not server_dir.is_dir():
                continue
            
            for snapshot_file in server_dir.glob("*.json.gz"):
                # Parse date from filename
                try:
                    file_date = date.fromisoformat(
                        snapshot_file.stem.replace(".json", "")
                    )
                    if file_date < cutoff:
                        snapshot_file.unlink()
                        removed += 1
                except ValueError:
                    continue
        
        if removed > 0:
            logger.info(
                f"Cleaned up {removed} old snapshot files"
            )
        
        return removed
