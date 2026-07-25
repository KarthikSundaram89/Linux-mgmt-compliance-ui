"""
Service Inventory Collector
===========================

Collects all systemd services with status, enabled state,
and highlights failed services.
"""

from typing import Any, Dict, FrozenSet, List

from backend.collectors.base import BaseCollector, LinuxDistro
from backend.ssh.connection import SSHConnection


class ServiceCollector(BaseCollector):
    """Collects systemd service inventory."""

    name = "services"
    version = "1.0.0"
    description = "Collects systemd service status and configuration"
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)

    async def collect(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> Dict[str, Any]:
        """Collect service inventory."""
        services: List[Dict[str, Any]] = []
        failed_services: List[Dict[str, Any]] = []

        # Get all service units
        result = await self.execute_command(
            connection,
            "systemctl list-units --type=service --all "
            "--no-pager --no-legend",
        )
        if result.exit_code != 0:
            raise RuntimeError("systemctl list-units failed")

        # Get unit file states (enabled/disabled)
        unit_result = await self.execute_command(
            connection,
            "systemctl list-unit-files --type=service "
            "--no-pager --no-legend",
        )
        unit_file_states = {}
        if unit_result.exit_code == 0:
            unit_file_states = self._parse_unit_files(
                unit_result.stdout
            )

        # Parse service list
        for line in result.stdout.strip().splitlines():
            svc = self._parse_service_line(line)
            if not svc:
                continue

            svc_name = svc["name"]
            # Add enabled state from unit files
            svc["enabled"] = unit_file_states.get(
                svc_name, "unknown"
            )
            svc["is_failed"] = svc["active_state"] == "failed"

            services.append(svc)

            if svc["is_failed"]:
                failed_services.append(svc)

        if failed_services:
            self.add_warning(
                f"{len(failed_services)} failed services detected"
            )

        return {
            "services": services,
            "total_count": len(services),
            "running_count": sum(
                1 for s in services if s["sub_state"] == "running"
            ),
            "failed_services": failed_services,
            "failed_count": len(failed_services),
        }

    def _parse_service_line(self, line: str) -> Dict[str, Any]:
        """Parse a single line from systemctl list-units."""
        # Format: UNIT LOAD ACTIVE SUB DESCRIPTION...
        parts = line.split(None, 4)
        if len(parts) < 4:
            return {}

        unit_name = parts[0].strip()
        # Remove bullet character if present
        if unit_name.startswith("\u25cf"):
            unit_name = parts[1].strip() if len(parts) > 1 else ""
            parts = line.split(None, 5)
            if len(parts) < 5:
                return {}
            return {
                "name": unit_name,
                "load_state": parts[2],
                "active_state": parts[3],
                "sub_state": parts[4],
                "description": parts[5] if len(parts) > 5 else "",
            }

        return {
            "name": unit_name,
            "load_state": parts[1],
            "active_state": parts[2],
            "sub_state": parts[3],
            "description": parts[4] if len(parts) > 4 else "",
        }

    def _parse_unit_files(self, content: str) -> Dict[str, str]:
        """Parse systemctl list-unit-files output."""
        states = {}
        for line in content.strip().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                states[parts[0]] = parts[1]
        return states
