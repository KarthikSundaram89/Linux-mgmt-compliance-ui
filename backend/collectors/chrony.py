"""
Chrony NTP Collector
====================

Collects time synchronization status via chronyd.
Raises warnings if synchronization is unhealthy.
"""

from typing import Any, Dict, FrozenSet

from backend.collectors.base import BaseCollector, LinuxDistro
from backend.ssh.connection import SSHConnection


class ChronyCollector(BaseCollector):
    """Collects chronyd time synchronization status."""

    name = "chrony"
    version = "1.0.0"
    description = "Collects NTP/chrony time synchronization status"
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)

    async def collect(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> Dict[str, Any]:
        """Collect chrony status."""
        data: Dict[str, Any] = {
            "installed": False,
            "service_running": False,
            "service_enabled": False,
            "synchronized": False,
            "tracking": {},
            "sources": [],
            "warnings": [],
        }

        # Check service status (name varies by distro)
        svc_name = "chronyd" if distro in (
            LinuxDistro.RHEL, LinuxDistro.CENTOS,
            LinuxDistro.ROCKY, LinuxDistro.ORACLE,
            LinuxDistro.AMAZON_LINUX,
        ) else "chrony"

        result = await self.execute_command(
            connection, f"systemctl is-active {svc_name}"
        )
        data["service_running"] = result.stdout.strip() == "active"
        data["installed"] = result.exit_code == 0 or "inactive" in result.stdout

        result = await self.execute_command(
            connection, f"systemctl is-enabled {svc_name}"
        )
        data["service_enabled"] = result.stdout.strip() == "enabled"

        if not data["installed"]:
            self.add_warning("chronyd not installed")
            return data

        if not data["service_running"]:
            self.add_warning("chronyd service is not running")
            return data

        # Get tracking info
        result = await self.execute_command(
            connection, "chronyc tracking"
        )
        if result.exit_code == 0:
            tracking = self._parse_tracking(result.stdout)
            data["tracking"] = tracking
            data["synchronized"] = tracking.get("leap_status") != "Not synchronised"

            # Check synchronization health
            if not data["synchronized"]:
                self.add_warning("Time synchronization is NOT healthy")
            
            # Check offset
            offset_str = tracking.get("system_time", "0")
            try:
                offset = abs(float(offset_str.split()[0]))
                if offset > 0.5:
                    self.add_warning(
                        f"Time offset is high: {offset:.6f} seconds"
                    )
            except (ValueError, IndexError):
                pass

        # Get time sources
        result = await self.execute_command(
            connection, "chronyc sources -v"
        )
        if result.exit_code == 0:
            data["sources"] = self._parse_sources(result.stdout)

        return data

    def _parse_tracking(self, content: str) -> Dict[str, str]:
        """Parse chronyc tracking output."""
        tracking = {}
        for line in content.strip().splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip().lower().replace(" ", "_")
                tracking[key] = value.strip()
        return tracking

    def _parse_sources(self, content: str) -> list:
        """Parse chronyc sources output."""
        sources = []
        in_data = False
        for line in content.strip().splitlines():
            if line.startswith("===") or line.startswith("---"):
                in_data = True
                continue
            if not in_data or not line.strip():
                continue
            # Source lines start with ^, *, +, -, etc.
            if len(line) > 2 and line[0] in "^*+-?x~":
                parts = line[1:].split()
                if len(parts) >= 4:
                    sources.append({
                        "mode": line[0],
                        "state": parts[0][0] if parts[0] else "",
                        "name": parts[0][1:] if len(parts[0]) > 1 else parts[0],
                        "stratum": parts[1] if len(parts) > 1 else "",
                        "poll": parts[2] if len(parts) > 2 else "",
                        "reach": parts[3] if len(parts) > 3 else "",
                    })
        return sources
