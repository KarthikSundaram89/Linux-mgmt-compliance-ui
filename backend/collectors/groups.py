"""
Group Inventory Collector
=========================

Collects local groups, members, empty groups, and administrative groups.
"""

from typing import Any, Dict, FrozenSet, List

from backend.collectors.base import BaseCollector, LinuxDistro
from backend.ssh.connection import SSHConnection

# Well-known administrative groups
ADMIN_GROUPS = frozenset([
    "wheel", "sudo", "adm", "root", "admin",
    "docker", "lxd", "libvirt", "disk",
])


class GroupCollector(BaseCollector):
    """Collects local group inventory and membership."""

    name = "groups"
    version = "1.0.0"
    description = "Collects local groups, members, and administrative groups"
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)

    async def collect(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> Dict[str, Any]:
        """Collect group inventory."""
        result = await self.execute_command(connection, "cat /etc/group")
        if result.exit_code != 0:
            raise RuntimeError("Cannot read /etc/group")

        groups: List[Dict[str, Any]] = []
        empty_groups: List[str] = []
        admin_groups: List[Dict[str, Any]] = []

        for line in result.stdout.strip().splitlines():
            parts = line.split(":")
            if len(parts) < 4:
                continue

            name = parts[0]
            gid = int(parts[2])
            members = [m for m in parts[3].split(",") if m]

            group_data = {
                "name": name,
                "gid": gid,
                "members": members,
                "member_count": len(members),
                "is_system": gid < 1000,
                "is_admin": name in ADMIN_GROUPS,
            }
            groups.append(group_data)

            if not members:
                empty_groups.append(name)

            if name in ADMIN_GROUPS and members:
                admin_groups.append({
                    "name": name,
                    "gid": gid,
                    "members": members,
                })

        return {
            "groups": groups,
            "total_count": len(groups),
            "empty_groups": empty_groups,
            "empty_group_count": len(empty_groups),
            "admin_groups": admin_groups,
            "admin_group_count": len(admin_groups),
        }
