"""
CMDB CSV Import Service
=======================

Reads the EC2 CMDB CSV file from the EFS mount daily and
synchronizes the server inventory. Adds new servers, updates
existing ones, and marks removed servers as inactive.

The CSV file is produced by an external process and contains:
- region
- account_name (profile name)
- instance_id
- instance_ip
- Name (tag - used as hostname)
- app_name (tag)
- PDO (tag)

EFS mount path and CSV column names are fully configurable
via application settings.
"""

import csv
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.settings.config import get_settings

logger = logging.getLogger("app")


class CMDBImportResult:
    """Result of a CMDB import operation."""

    def __init__(self):
        self.total_rows: int = 0
        self.servers_created: int = 0
        self.servers_updated: int = 0
        self.servers_deactivated: int = 0
        self.servers_skipped: int = 0
        self.errors: List[str] = []
        self.started_at: datetime = datetime.now(timezone.utc)
        self.completed_at: Optional[datetime] = None

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "servers_created": self.servers_created,
            "servers_updated": self.servers_updated,
            "servers_deactivated": self.servers_deactivated,
            "servers_skipped": self.servers_skipped,
            "errors": self.errors[:50],
            "success": self.success,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class CMDBImportService:
    """
    Reads EC2 CMDB CSV from EFS and syncs server inventory.

    Workflow:
    1. Read CSV file from configured EFS path
    2. Parse rows using configured column mapping
    3. For each row:
       - If server exists (by instance_id or IP): update fields
       - If server is new: create with default credential profile
    4. Servers in DB but NOT in CSV: mark as inactive (decommissioned)
    5. Log results and store import history

    This runs daily BEFORE the collection schedule so newly
    added servers are collected on the same day.
    """

    def __init__(self):
        self._settings = get_settings()

    async def run_import(self) -> CMDBImportResult:
        """
        Execute the CMDB CSV import.

        Returns:
            CMDBImportResult with counts and any errors.
        """
        result = CMDBImportResult()

        csv_path = self._settings.cmdb_import_path
        logger.info(
            f"Starting CMDB import from: {csv_path}"
        )

        # ─── Validate file exists ──────────────────────────────────
        if not os.path.isfile(csv_path):
            error = f"CMDB CSV file not found: {csv_path}"
            logger.error(error)
            result.errors.append(error)
            result.completed_at = datetime.now(timezone.utc)
            return result

        # ─── Read and parse CSV ────────────────────────────────────
        try:
            rows = self._read_csv(csv_path)
            result.total_rows = len(rows)
            logger.info(f"Read {len(rows)} rows from CMDB CSV")
        except Exception as e:
            error = f"Failed to read CSV: {str(e)}"
            logger.error(error, exc_info=True)
            result.errors.append(error)
            result.completed_at = datetime.now(timezone.utc)
            return result

        if not rows:
            logger.warning("CMDB CSV is empty, nothing to import")
            result.completed_at = datetime.now(timezone.utc)
            return result

        # ─── Sync with database ────────────────────────────────────
        try:
            await self._sync_servers(rows, result)
        except Exception as e:
            error = f"Database sync failed: {str(e)}"
            logger.error(error, exc_info=True)
            result.errors.append(error)

        result.completed_at = datetime.now(timezone.utc)

        logger.info(
            f"CMDB import complete: "
            f"{result.servers_created} created, "
            f"{result.servers_updated} updated, "
            f"{result.servers_deactivated} deactivated, "
            f"{result.servers_skipped} skipped"
        )

        return result

    def _read_csv(self, path: str) -> List[Dict[str, str]]:
        """
        Read the CSV file using configured settings.

        Returns:
            List of row dictionaries.
        """
        rows: List[Dict[str, str]] = []
        encoding = self._settings.cmdb_csv_encoding
        delimiter = self._settings.cmdb_csv_delimiter

        with open(path, "r", encoding=encoding) as f:
            if self._settings.cmdb_csv_has_header:
                reader = csv.DictReader(f, delimiter=delimiter)
            else:
                # Use column index positions
                reader = csv.DictReader(
                    f,
                    fieldnames=[
                        self._settings.cmdb_col_region,
                        self._settings.cmdb_col_account_name,
                        self._settings.cmdb_col_instance_id,
                        self._settings.cmdb_col_instance_ip,
                        self._settings.cmdb_col_name,
                        self._settings.cmdb_col_app_name,
                        self._settings.cmdb_col_pdo,
                    ],
                    delimiter=delimiter,
                )

            for row in reader:
                # Skip empty rows
                ip = row.get(self._settings.cmdb_col_instance_ip, "").strip()
                name = row.get(self._settings.cmdb_col_name, "").strip()
                if ip and name:
                    rows.append(row)

        return rows

    def _parse_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Parse a CSV row into server fields using column mapping.

        Returns:
            Dictionary of server fields.
        """
        s = self._settings
        return {
            "hostname": row.get(s.cmdb_col_name, "").strip(),
            "ip_address": row.get(s.cmdb_col_instance_ip, "").strip(),
            "aws_region": row.get(s.cmdb_col_region, "").strip(),
            "aws_account_name": row.get(s.cmdb_col_account_name, "").strip(),
            "instance_id": row.get(s.cmdb_col_instance_id, "").strip(),
            "app_name": row.get(s.cmdb_col_app_name, "").strip(),
            "pdo": row.get(s.cmdb_col_pdo, "").strip(),
        }

    async def _sync_servers(
        self, rows: List[Dict[str, str]], result: CMDBImportResult
    ) -> None:
        """
        Synchronize CSV data with the database.

        Creates new servers, updates existing, deactivates removed.
        """
        from backend.database.session import async_session_factory
        from backend.models.server import Server
        from backend.repositories.server_repository import ServerRepository

        async with async_session_factory() as session:
            repo = ServerRepository(session)

            # Track which servers are in the CSV
            csv_instance_ids: Set[str] = set()
            csv_ips: Set[str] = set()

            for row in rows:
                parsed = self._parse_row(row)
                hostname = parsed["hostname"]
                ip_address = parsed["ip_address"]
                instance_id = parsed["instance_id"]

                if not hostname or not ip_address:
                    result.servers_skipped += 1
                    continue

                csv_instance_ids.add(instance_id)
                csv_ips.add(ip_address)

                # Check if server exists (by hostname or IP)
                existing = await repo.get_by_hostname(hostname)
                if not existing:
                    # Try by IP
                    all_servers = await repo.get_all(
                        filters={"ip_address": ip_address, "is_deleted": False}
                    )
                    existing = all_servers[0] if all_servers else None

                if existing:
                    # Update existing server with latest CMDB data
                    update_data = {
                        "ip_address": ip_address,
                        "aws_region": parsed["aws_region"],
                        "aws_account_name": parsed["aws_account_name"],
                        "instance_id": instance_id,
                        "app_name": parsed["app_name"],
                        "pdo": parsed["pdo"],
                        "is_active": True,
                    }
                    await repo.update(existing, update_data)
                    result.servers_updated += 1
                else:
                    # Create new server
                    default_profile = self._settings.cmdb_default_credential_profile
                    if not default_profile:
                        result.servers_skipped += 1
                        if result.servers_skipped <= 5:
                            result.errors.append(
                                f"No default credential profile configured. "
                                f"Cannot create server: {hostname}"
                            )
                        continue

                    new_server = Server(
                        hostname=hostname,
                        ip_address=ip_address,
                        port=self._settings.cmdb_default_ssh_port,
                        environment="production",
                        credential_profile_id=default_profile,
                        aws_region=parsed["aws_region"],
                        aws_account_name=parsed["aws_account_name"],
                        instance_id=instance_id,
                        app_name=parsed["app_name"],
                        pdo=parsed["pdo"],
                        is_active=True,
                        description=f"Auto-imported from CMDB | App: {parsed['app_name']} | PDO: {parsed['pdo']}",
                    )
                    await repo.create(new_server)
                    result.servers_created += 1

            # Deactivate servers no longer in CMDB
            # (only if they were previously auto-imported)
            active_servers = await repo.get_active_servers()
            for server in active_servers:
                if server.instance_id and server.instance_id not in csv_instance_ids:
                    await repo.update(server, {"is_active": False})
                    result.servers_deactivated += 1

            await session.commit()

    async def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the CMDB import configuration.

        Checks:
        - EFS mount path exists
        - CSV file is readable
        - Column headers match configuration
        - Default credential profile is set

        Returns:
            Validation result dict.
        """
        issues: List[str] = []
        s = self._settings

        # Check file path
        if not os.path.isfile(s.cmdb_import_path):
            issues.append(f"CSV file not found: {s.cmdb_import_path}")
        else:
            # Try reading headers
            try:
                with open(s.cmdb_import_path, "r", encoding=s.cmdb_csv_encoding) as f:
                    reader = csv.reader(f, delimiter=s.cmdb_csv_delimiter)
                    headers = next(reader, [])

                    expected_cols = [
                        s.cmdb_col_region, s.cmdb_col_account_name,
                        s.cmdb_col_instance_id, s.cmdb_col_instance_ip,
                        s.cmdb_col_name, s.cmdb_col_app_name, s.cmdb_col_pdo,
                    ]
                    missing = [c for c in expected_cols if c not in headers]
                    if missing:
                        issues.append(f"Missing CSV columns: {missing}")
                    else:
                        row_count = sum(1 for _ in reader)
                        return {
                            "valid": True,
                            "file": s.cmdb_import_path,
                            "headers": headers,
                            "row_count": row_count,
                            "issues": [],
                        }
            except Exception as e:
                issues.append(f"Cannot read CSV: {str(e)}")

        if not s.cmdb_default_credential_profile:
            issues.append("No default credential profile configured")

        return {
            "valid": len(issues) == 0,
            "file": s.cmdb_import_path,
            "issues": issues,
        }
