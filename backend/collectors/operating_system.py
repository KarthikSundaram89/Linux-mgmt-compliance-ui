"""
Operating System Collector
==========================

Collects OS-level information: distribution, kernel, hostname,
uptime, virtualization, timezone, and reboot pending status.
"""

from typing import Any, Dict, FrozenSet

from backend.collectors.base import BaseCollector, LinuxDistro
from backend.ssh.connection import SSHConnection


class OperatingSystemCollector(BaseCollector):
    """Collects comprehensive operating system information."""

    name = "operating_system"
    version = "1.0.0"
    description = "Collects OS identity, kernel, uptime, and virtualization info"
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)

    async def collect(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> Dict[str, Any]:
        """Collect operating system data."""
        data: Dict[str, Any] = {}

        # ─── OS Release ────────────────────────────────────────────
        result = await self.execute_command(connection, "cat /etc/os-release")
        if result.exit_code == 0:
            os_info = self._parse_os_release(result.stdout)
            data["distribution"] = os_info.get("ID", "")
            data["distribution_version"] = os_info.get("VERSION_ID", "")
            data["pretty_name"] = os_info.get("PRETTY_NAME", "")
            data["distribution_id_like"] = os_info.get("ID_LIKE", "")

        # ─── Hostname ──────────────────────────────────────────────
        result = await self.execute_command(connection, "hostname")
        if result.exit_code == 0:
            data["hostname"] = result.stdout.strip()

        result = await self.execute_command(connection, "hostname -f")
        if result.exit_code == 0:
            data["fqdn"] = result.stdout.strip()

        # ─── Kernel ────────────────────────────────────────────────
        result = await self.execute_command(connection, "uname -r")
        if result.exit_code == 0:
            data["kernel_release"] = result.stdout.strip()

        result = await self.execute_command(connection, "uname -a")
        if result.exit_code == 0:
            parts = result.stdout.strip().split()
            data["kernel_version"] = parts[2] if len(parts) > 2 else ""
            data["architecture"] = parts[-2] if len(parts) > 2 else ""

        result = await self.execute_command(connection, "uname -m")
        if result.exit_code == 0:
            data["machine_type"] = result.stdout.strip()

        # ─── Platform Info ─────────────────────────────────────────
        result = await self.execute_command(connection, "hostnamectl")
        if result.exit_code == 0:
            hctl = self._parse_hostnamectl(result.stdout)
            data["platform"] = hctl.get("Chassis", "")
            data["operating_system"] = hctl.get("Operating System", "")
            data["cpe_os_name"] = hctl.get("CPE OS Name", "")

        # ─── Virtualization ────────────────────────────────────────
        result = await self.execute_command(connection, "systemd-detect-virt")
        if result.exit_code == 0:
            virt_type = result.stdout.strip()
            data["virtualization_type"] = virt_type if virt_type != "none" else "bare-metal"
        else:
            data["virtualization_type"] = "unknown"

        result = await self.execute_command(connection, "cat /sys/class/dmi/id/sys_vendor")
        if result.exit_code == 0:
            data["virtualization_vendor"] = result.stdout.strip()

        # ─── Timezone and Time ─────────────────────────────────────
        result = await self.execute_command(connection, "timedatectl")
        if result.exit_code == 0:
            tc = self._parse_hostnamectl(result.stdout)
            data["timezone"] = tc.get("Time zone", "").split()[0] if tc.get("Time zone") else ""

        result = await self.execute_command(connection, "date +%Y-%m-%dT%H:%M:%S%z")
        if result.exit_code == 0:
            data["current_time"] = result.stdout.strip()

        # ─── Uptime and Boot ───────────────────────────────────────
        result = await self.execute_command(connection, "uptime -s")
        if result.exit_code == 0:
            data["last_boot_time"] = result.stdout.strip()

        result = await self.execute_command(connection, "cat /proc/uptime")
        if result.exit_code == 0:
            parts = result.stdout.strip().split()
            if parts:
                data["uptime_seconds"] = float(parts[0])

        result = await self.execute_command(
            connection, "cat /proc/sys/kernel/random/boot_id"
        )
        if result.exit_code == 0:
            data["boot_id"] = result.stdout.strip()

        # ─── OS Install Date (best effort) ─────────────────────────
        result = await self.execute_command(connection, "stat -c %W /")
        if result.exit_code == 0:
            val = result.stdout.strip()
            if val and val != "0":
                data["os_install_epoch"] = int(val)

        # ─── Reboot Pending ────────────────────────────────────────
        data["reboot_pending"] = await self._check_reboot_pending(
            connection, distro
        )

        return data

    async def _check_reboot_pending(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> bool:
        """Check if a reboot is pending."""
        if distro in (LinuxDistro.UBUNTU, LinuxDistro.DEBIAN, LinuxDistro.KALI):
            result = await self.execute_command(
                connection, "cat /var/run/reboot-required"
            )
            return result.exit_code == 0
        elif distro in (LinuxDistro.RHEL, LinuxDistro.CENTOS, LinuxDistro.ROCKY, LinuxDistro.ORACLE, LinuxDistro.AMAZON_LINUX):
            result = await self.execute_command(
                connection, "needs-restarting -r"
            )
            # Exit code 1 = reboot needed
            return result.exit_code == 1
        return False

    def _parse_os_release(self, content: str) -> Dict[str, str]:
        """Parse /etc/os-release into a dictionary."""
        data = {}
        for line in content.strip().splitlines():
            if "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                data[key.strip()] = value.strip().strip('"')
        return data

    def _parse_hostnamectl(self, content: str) -> Dict[str, str]:
        """Parse key: value output from hostnamectl/timedatectl."""
        data = {}
        for line in content.strip().splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                data[key.strip()] = value.strip()
        return data
