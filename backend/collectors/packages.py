"""
Package Inventory Collector
===========================

Collects installed packages using the appropriate package manager:
rpm/yum/dnf for RHEL-family, dpkg/apt for Debian-family.
"""

from typing import Any, Dict, FrozenSet, List

from backend.collectors.base import BaseCollector, LinuxDistro
from backend.ssh.connection import SSHConnection

_RPM_DISTROS = frozenset([
    LinuxDistro.RHEL, LinuxDistro.CENTOS, LinuxDistro.ROCKY,
    LinuxDistro.ORACLE, LinuxDistro.AMAZON_LINUX, LinuxDistro.SUSE,
])
_DEB_DISTROS = frozenset([
    LinuxDistro.UBUNTU, LinuxDistro.DEBIAN, LinuxDistro.KALI,
])


class PackageCollector(BaseCollector):
    """Collects installed package inventory."""

    name = "packages"
    version = "1.0.0"
    description = "Collects installed packages via rpm or dpkg"
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)

    async def collect(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> Dict[str, Any]:
        """Collect package inventory."""
        if distro in _RPM_DISTROS or distro == LinuxDistro.UNKNOWN:
            packages = await self._collect_rpm(connection)
            pkg_manager = "rpm"
        elif distro in _DEB_DISTROS:
            packages = await self._collect_dpkg(connection)
            pkg_manager = "dpkg"
        else:
            packages = await self._collect_rpm(connection)
            pkg_manager = "rpm"

        return {
            "packages": packages,
            "total_count": len(packages),
            "package_manager": pkg_manager,
        }

    async def _collect_rpm(
        self, connection: SSHConnection
    ) -> List[Dict[str, Any]]:
        """Collect packages via rpm."""
        cmd = (
            "rpm -qa --qf "
            "'%{NAME}|%{VERSION}|%{RELEASE}|%{ARCH}|"
            "%{VENDOR}|%{INSTALLTIME:date}\\n'"
        )
        result = await self.execute_command(connection, cmd)
        if result.exit_code != 0:
            self.add_warning("rpm query failed, trying yum")
            return await self._collect_yum(connection)

        packages = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("|")
            if len(parts) >= 6:
                packages.append({
                    "name": parts[0],
                    "version": parts[1],
                    "release": parts[2],
                    "architecture": parts[3],
                    "vendor": parts[4],
                    "install_date": parts[5],
                })
        return packages

    async def _collect_yum(
        self, connection: SSHConnection
    ) -> List[Dict[str, Any]]:
        """Fallback: collect via yum list installed."""
        result = await self.execute_command(
            connection, "yum list installed"
        )
        if result.exit_code != 0:
            return []

        packages = []
        lines = result.stdout.strip().splitlines()
        for line in lines:
            if "." not in line or line.startswith("Installed") or line.startswith("Loaded"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                name_arch = parts[0]
                name = name_arch.rsplit(".", 1)[0] if "." in name_arch else name_arch
                arch = name_arch.rsplit(".", 1)[1] if "." in name_arch else ""
                ver_rel = parts[1]
                version = ver_rel.split("-")[0] if "-" in ver_rel else ver_rel
                release = ver_rel.split("-", 1)[1] if "-" in ver_rel else ""
                repo = parts[2] if len(parts) > 2 else ""
                packages.append({
                    "name": name,
                    "version": version,
                    "release": release,
                    "architecture": arch,
                    "repository": repo,
                    "vendor": "",
                    "install_date": "",
                })
        return packages

    async def _collect_dpkg(
        self, connection: SSHConnection
    ) -> List[Dict[str, Any]]:
        """Collect packages via dpkg-query."""
        cmd = "dpkg-query -W -f='${Package}|${Version}|${Architecture}|${Status}\\n'"
        result = await self.execute_command(connection, cmd)
        if result.exit_code != 0:
            self.add_warning("dpkg-query failed")
            return []

        packages = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("|")
            if len(parts) >= 4:
                # Only include fully installed packages
                if "installed" not in parts[3].lower():
                    continue
                version = parts[1]
                packages.append({
                    "name": parts[0],
                    "version": version,
                    "release": "",
                    "architecture": parts[2],
                    "vendor": "",
                    "install_date": "",
                })
        return packages
