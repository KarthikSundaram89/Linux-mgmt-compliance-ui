"""
Sudo Inventory Collector
========================

Identifies privileged users: sudo group members, sudoers entries,
NOPASSWD rules, and potential conflicts.
"""

from typing import Any, Dict, FrozenSet, List

from backend.collectors.base import BaseCollector, LinuxDistro
from backend.ssh.connection import SSHConnection


class SudoCollector(BaseCollector):
    """Collects sudo/privilege escalation configuration."""

    name = "sudo"
    version = "1.0.0"
    description = "Collects sudo configuration, privileged users, and rules"
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)

    async def collect(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> Dict[str, Any]:
        """Collect sudo inventory."""
        data: Dict[str, Any] = {
            "privileged_users": [],
            "sudoers_rules": [],
            "sudoers_d_entries": [],
            "nopasswd_entries": [],
            "warnings": [],
        }

        # Get sudo group members
        result = await self.execute_command(connection, "cat /etc/group")
        if result.exit_code == 0:
            sudo_members = self._get_sudo_members(result.stdout, distro)
            data["privileged_users"] = sudo_members

        # Parse main sudoers file
        result = await self.execute_command(connection, "cat /etc/sudoers")
        if result.exit_code == 0:
            rules = self._parse_sudoers(result.stdout)
            data["sudoers_rules"] = rules
            data["nopasswd_entries"] = [
                r for r in rules if r.get("nopasswd")
            ]

        # Parse sudoers.d directory
        result = await self.execute_command(connection, "ls -la /etc/sudoers.d/")
        if result.exit_code == 0:
            data["sudoers_d_files"] = self._parse_ls_output(result.stdout)

        result = await self.execute_command(connection, "grep -r '' /etc/sudoers.d/")
        if result.exit_code == 0:
            d_rules = self._parse_sudoers_d(result.stdout)
            data["sudoers_d_entries"] = d_rules
            # Add NOPASSWD from sudoers.d
            data["nopasswd_entries"].extend(
                [r for r in d_rules if r.get("nopasswd")]
            )

        # Validate sudoers syntax
        result = await self.execute_command(connection, "visudo -c")
        data["syntax_valid"] = result.exit_code == 0
        if result.exit_code != 0:
            self.add_warning(f"sudoers syntax error: {result.stderr[:200]}")
            data["warnings"].append(result.stderr[:200])

        # Detect conflicts/duplicates
        data["duplicate_rules"] = self._find_duplicates(
            data["sudoers_rules"] + data["sudoers_d_entries"]
        )

        return data

    def _get_sudo_members(self, group_content: str, distro: LinuxDistro) -> List[Dict[str, Any]]:
        """Extract members of sudo/wheel groups."""
        sudo_group_names = {"sudo", "wheel"}
        members = []

        for line in group_content.strip().splitlines():
            parts = line.split(":")
            if len(parts) < 4:
                continue
            if parts[0] in sudo_group_names:
                for user in parts[3].split(","):
                    user = user.strip()
                    if user:
                        members.append({
                            "username": user,
                            "group": parts[0],
                            "source": "group_membership",
                        })
        return members

    def _parse_sudoers(self, content: str) -> List[Dict[str, Any]]:
        """Parse sudoers file into structured rules."""
        rules = []
        for line in content.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("Defaults"):
                continue
            if "ALL" in line or "=" in line:
                rule = self._parse_sudoers_line(line, "/etc/sudoers")
                if rule:
                    rules.append(rule)
        return rules

    def _parse_sudoers_d(self, content: str) -> List[Dict[str, Any]]:
        """Parse grep output from sudoers.d directory."""
        rules = []
        for line in content.strip().splitlines():
            if ":" not in line:
                continue
            file_path, _, rule_line = line.partition(":")
            rule_line = rule_line.strip()
            if not rule_line or rule_line.startswith("#") or rule_line.startswith("Defaults"):
                continue
            if "ALL" in rule_line or "=" in rule_line:
                rule = self._parse_sudoers_line(rule_line, file_path.strip())
                if rule:
                    rules.append(rule)
        return rules

    def _parse_sudoers_line(self, line: str, source_file: str) -> Dict[str, Any]:
        """Parse a single sudoers rule line."""
        nopasswd = "NOPASSWD" in line
        # Extract username/group (before the host spec)
        parts = line.split()
        if not parts:
            return {}

        user_or_group = parts[0]
        is_group = user_or_group.startswith("%")

        return {
            "user_or_group": user_or_group.lstrip("%"),
            "is_group": is_group,
            "rule": line[:200],
            "nopasswd": nopasswd,
            "source_file": source_file,
            "has_command_restriction": "ALL" not in line.split("=")[-1] if "=" in line else False,
        }

    def _parse_ls_output(self, content: str) -> List[str]:
        """Extract filenames from ls output."""
        files = []
        for line in content.strip().splitlines():
            parts = line.split()
            if len(parts) >= 9 and not parts[-1].startswith("."):
                files.append(parts[-1])
        return files

    def _find_duplicates(self, rules: List[Dict]) -> List[Dict]:
        """Find duplicate or conflicting sudo rules."""
        seen = {}
        duplicates = []
        for rule in rules:
            key = rule.get("user_or_group", "")
            if key in seen:
                duplicates.append({
                    "user_or_group": key,
                    "first_source": seen[key],
                    "duplicate_source": rule.get("source_file", ""),
                })
            else:
                seen[key] = rule.get("source_file", "")
        return duplicates
