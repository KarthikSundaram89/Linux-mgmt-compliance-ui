"""
Filesystem Inventory Collector
==============================

Collects mounted filesystems with capacity, usage, mount options,
and highlights NFS/SMB/bind mounts.
"""

from typing import Any, Dict, FrozenSet, List

from backend.collectors.base import BaseCollector, LinuxDistro
from backend.ssh.connection import SSHConnection

# Filesystem types of special interest
NETWORK_FS = frozenset(["nfs", "nfs4", "cifs", "smb", "smbfs"])
SPECIAL_FS = frozenset(["tmpfs", "devtmpfs", "overlay", "aufs"])
SKIP_FS = frozenset(["proc", "sysfs", "devpts", "securityfs",
                      "cgroup", "cgroup2", "pstore", "debugfs",
                      "hugetlbfs", "mqueue", "configfs", "bpf",
                      "fusectl", "tracefs", "efivarfs"])


class FilesystemCollector(BaseCollector):
    """Collects filesystem inventory and usage statistics."""

    name = "filesystem"
    version = "1.0.0"
    description = "Collects mounted filesystems, usage, and mount options"
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)

    async def collect(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> Dict[str, Any]:
        """Collect filesystem data."""
        mounts: List[Dict[str, Any]] = []
        nfs_mounts: List[Dict[str, Any]] = []
        smb_mounts: List[Dict[str, Any]] = []
        bind_mounts: List[Dict[str, Any]] = []

        # Get filesystem usage with POSIX output
        result = await self.execute_command(connection, "df -PT")
        if result.exit_code != 0:
            raise RuntimeError("Cannot execute df command")

        df_data = self._parse_df(result.stdout)

        # Get mount options from /proc/mounts
        result = await self.execute_command(
            connection, "cat /proc/mounts"
        )
        mount_options = {}
        if result.exit_code == 0:
            mount_options = self._parse_proc_mounts(result.stdout)

        # Build filesystem records
        for fs in df_data:
            mount_point = fs["mount_point"]
            fs_type = fs["fs_type"]

            # Skip virtual filesystems
            if fs_type in SKIP_FS:
                continue

            opts = mount_options.get(mount_point, {})
            record = {
                "mount_point": mount_point,
                "filesystem_type": fs_type,
                "device": fs["device"],
                "capacity_kb": fs["total_kb"],
                "used_kb": fs["used_kb"],
                "free_kb": fs["free_kb"],
                "usage_percent": fs["usage_percent"],
                "mount_options": opts.get("options", ""),
                "read_only": "ro" in opts.get("options", "").split(","),
                "is_network": fs_type in NETWORK_FS,
                "is_tmpfs": fs_type in ("tmpfs", "devtmpfs"),
                "is_overlay": fs_type == "overlay",
                "remote_server": self._extract_remote(fs["device"]),
            }
            mounts.append(record)

            # Categorize special mounts
            if fs_type in ("nfs", "nfs4"):
                nfs_mounts.append(record)
            elif fs_type in ("cifs", "smb", "smbfs"):
                smb_mounts.append(record)
            if "bind" in opts.get("options", ""):
                bind_mounts.append(record)

        # High usage warnings
        high_usage = [
            m for m in mounts if m["usage_percent"] >= 90
        ]
        for m in high_usage:
            self.add_warning(
                f"High usage: {m['mount_point']} at "
                f"{m['usage_percent']}%"
            )

        return {
            "mounts": mounts,
            "total_count": len(mounts),
            "nfs_mounts": nfs_mounts,
            "smb_mounts": smb_mounts,
            "bind_mounts": bind_mounts,
            "tmpfs_mounts": [
                m for m in mounts if m["is_tmpfs"]
            ],
            "overlay_mounts": [
                m for m in mounts if m["is_overlay"]
            ],
            "high_usage_mounts": high_usage,
        }

    def _parse_df(self, content: str) -> List[Dict[str, Any]]:
        """Parse df -PT output."""
        results = []
        lines = content.strip().splitlines()
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) < 7:
                continue
            try:
                results.append({
                    "device": parts[0],
                    "fs_type": parts[1],
                    "total_kb": int(parts[2]),
                    "used_kb": int(parts[3]),
                    "free_kb": int(parts[4]),
                    "usage_percent": int(parts[5].rstrip("%")),
                    "mount_point": parts[6],
                })
            except (ValueError, IndexError):
                continue
        return results

    def _parse_proc_mounts(self, content: str) -> Dict[str, Dict]:
        """Parse /proc/mounts for mount options."""
        mounts = {}
        for line in content.strip().splitlines():
            parts = line.split()
            if len(parts) >= 4:
                mount_point = parts[1]
                mounts[mount_point] = {
                    "device": parts[0],
                    "fs_type": parts[2],
                    "options": parts[3],
                }
        return mounts

    def _extract_remote(self, device: str) -> str:
        """Extract remote server from NFS/CIFS device path."""
        if ":" in device and device.startswith("/") is False:
            return device.split(":")[0]
        if device.startswith("//"):
            parts = device.split("/")
            return parts[2] if len(parts) > 2 else ""
        return ""
