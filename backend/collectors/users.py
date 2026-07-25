"""
User Inventory Collector
========================

Collects non-system user accounts with security-relevant details
including password status, group memberships, and SSH key presence.
"""

from typing import Any, Dict, FrozenSet, List

from backend.collectors.base import BaseCollector, LinuxDistro
from backend.ssh.connection import SSHConnection


# Minimum UID for non-system users (varies by distro)
_MIN_UID = {
    LinuxDistro.RHEL: 1000,
    LinuxDistro.CENTOS: 1000,
    LinuxDistro.ROCKY: 1000,
    LinuxDistro.ORACLE: 1000,
    LinuxDistro.AMAZON_LINUX: 1000,
    LinuxDistro.UBUNTU: 1000,
    LinuxDistro.DEBIAN: 1000,
    LinuxDistro.KALI: 1000,
    LinuxDistro.SUSE: 1000,
}


class UserCollector(BaseCollector):
    """Collects non-system user inventory with security metadata."""

    name = "users"
    version = "1.0.0"
    description = "Collects non-system user accounts and security details"
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)

    async def collect(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> Dict[str, Any]:
        """Collect user inventory."""
        min_uid = _MIN_UID.get(distro, 1000)
        users: List[Dict[str, Any]] = []

        # Get all users from /etc/passwd
        result = await self.execute_command(connection, "cat /etc/passwd")
        if result.exit_code != 0:
            raise RuntimeError("Cannot read /etc/passwd")

        passwd_entries = self._parse_passwd(result.stdout, min_uid)

        # Get group info
        result = await self.execute_command(connection, "cat /etc/group")
        group_map = self._build_group_map(result.stdout) if result.exit_code == 0 else {}

        # Get shadow info for password aging
        result = await self.execute_command(connection, "cat /etc/shadow")
        shadow_map = self._parse_shadow(result.stdout) if result.exit_code == 0 else {}

        # Get lastlog info
        result = await self.execute_command(connection, "lastlog")
        lastlog_map = self._parse_lastlog(result.stdout) if result.exit_code == 0 else {}

        # Get authorized keys presence
        result = await self.execute_command(
            connection, "find /home -name authorized_keys -type f"
        )
        auth_keys_paths = set(result.stdout.strip().splitlines()) if result.exit_code == 0 else set()

        # Build user records
        for entry in passwd_entries:
            username = entry["username"]
            uid = entry["uid"]

            user_data: Dict[str, Any] = {
                "username": username,
                "uid": uid,
                "gid": entry["gid"],
                "primary_group": group_map.get(str(entry["gid"]), {}).get("name", ""),
                "secondary_groups": self._get_secondary_groups(username, group_map),
                "home_directory": entry["home"],
                "login_shell": entry["shell"],
                "gecos": entry["gecos"],
            }

            # Shadow data
            shadow = shadow_map.get(username, {})
            user_data["account_status"] = shadow.get("status", "unknown")
            user_data["account_locked"] = shadow.get("locked", False)
            user_data["password_expired"] = shadow.get("expired", False)
            user_data["password_last_changed"] = shadow.get("last_changed", "")
            user_data["password_expiry_date"] = shadow.get("expiry_date", "")
            user_data["password_warning_days"] = shadow.get("warn_days", "")
            user_data["password_max_days"] = shadow.get("max_days", "")
            user_data["password_min_days"] = shadow.get("min_days", "")

            # Last login
            user_data["last_login"] = lastlog_map.get(username, "Never")

            # SSH authorized keys
            home = entry["home"]
            has_keys = any(
                p.startswith(home) for p in auth_keys_paths
            )
            user_data["ssh_authorized_keys_present"] = has_keys

            users.append(user_data)

        return {
            "users": users,
            "total_count": len(users),
            "min_uid_threshold": min_uid,
        }

    def _parse_passwd(self, content: str, min_uid: int) -> List[Dict[str, Any]]:
        """Parse /etc/passwd and filter non-system users."""
        entries = []
        for line in content.strip().splitlines():
            parts = line.split(":")
            if len(parts) < 7:
                continue
            uid = int(parts[2])
            # Filter: only non-system users (UID >= min_uid) OR root
            if uid < min_uid and uid != 0:
                continue
            # Skip nfsnobody and other high-UID service accounts
            if parts[0] in ("nfsnobody", "nobody"):
                continue
            entries.append({
                "username": parts[0],
                "uid": uid,
                "gid": int(parts[3]),
                "gecos": parts[4],
                "home": parts[5],
                "shell": parts[6],
            })
        return entries

    def _build_group_map(self, content: str) -> Dict[str, Dict]:
        """Build GID -> group info map and name -> members map."""
        groups = {}
        for line in content.strip().splitlines():
            parts = line.split(":")
            if len(parts) < 4:
                continue
            gid = parts[2]
            groups[gid] = {
                "name": parts[0],
                "members": parts[3].split(",") if parts[3] else [],
            }
        return groups

    def _get_secondary_groups(self, username: str, group_map: Dict) -> List[str]:
        """Get secondary group memberships for a user."""
        groups = []
        for gid, info in group_map.items():
            if username in info["members"]:
                groups.append(info["name"])
        return groups

    def _parse_shadow(self, content: str) -> Dict[str, Dict]:
        """Parse /etc/shadow for password aging info."""
        shadow = {}
        for line in content.strip().splitlines():
            parts = line.split(":")
            if len(parts) < 9:
                continue
            username = parts[0]
            password_field = parts[1]

            locked = password_field.startswith("!") or password_field.startswith("*")
            expired = False
            status = "active"

            if password_field in ("!", "*", "!!"):
                status = "locked" if password_field.startswith("!") else "no_password"
                locked = True
            elif password_field.startswith("!"):
                status = "locked"
                locked = True

            # Password aging
            last_changed = parts[2] if parts[2] else ""
            min_days = parts[3] if parts[3] else ""
            max_days = parts[4] if parts[4] else ""
            warn_days = parts[5] if parts[5] else ""
            expiry_date = parts[7] if len(parts) > 7 and parts[7] else ""

            # Check if password is expired
            if max_days and last_changed and max_days != "99999":
                try:
                    if int(last_changed) + int(max_days) < self._days_since_epoch():
                        expired = True
                        status = "expired"
                except (ValueError, TypeError):
                    pass

            shadow[username] = {
                "status": status,
                "locked": locked,
                "expired": expired,
                "last_changed": last_changed,
                "min_days": min_days,
                "max_days": max_days,
                "warn_days": warn_days,
                "expiry_date": expiry_date,
            }
        return shadow

    def _parse_lastlog(self, content: str) -> Dict[str, str]:
        """Parse lastlog output."""
        result = {}
        lines = content.strip().splitlines()
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if not parts:
                continue
            username = parts[0]
            if "Never logged in" in line:
                result[username] = "Never"
            elif len(parts) >= 4:
                # Extract the date portion
                result[username] = " ".join(parts[1:])
        return result

    @staticmethod
    def _days_since_epoch() -> int:
        """Current days since Unix epoch."""
        import time
        return int(time.time() / 86400)
