"""
SSH Configuration Collector
===========================

Collects SSH daemon configuration for security auditing.
Does not expose sensitive configuration values publicly.
"""

from typing import Any, Dict, FrozenSet

from backend.collectors.base import BaseCollector, LinuxDistro
from backend.ssh.connection import SSHConnection

# Security-relevant SSH settings to collect
TARGET_SETTINGS = frozenset([
    "permitrootlogin",
    "passwordauthentication",
    "pubkeyauthentication",
    "allowusers",
    "allowgroups",
    "denyusers",
    "denygroups",
    "maxauthtries",
    "logingracetime",
    "clientaliveinterval",
    "clientalivecountmax",
    "x11forwarding",
    "permitemptypasswords",
    "protocol",
    "usepam",
    "challengeresponseauthentication",
    "kbdinteractiveauthentication",
    "maxsessions",
    "maxstartups",
    "permituserenvironment",
    "banner",
])


class SSHConfigCollector(BaseCollector):
    """Collects SSH daemon configuration."""

    name = "ssh_config"
    version = "1.0.0"
    description = "Collects SSH daemon security configuration"
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)

    async def collect(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> Dict[str, Any]:
        """Collect SSH configuration."""
        data: Dict[str, Any] = {
            "version": "",
            "service_running": False,
            "service_enabled": False,
            "config": {},
            "security_issues": [],
        }

        # SSH version
        result = await self.execute_command(connection, "ssh -V")
        # ssh -V writes to stderr
        version_str = result.stderr.strip() or result.stdout.strip()
        data["version"] = version_str

        # Service status
        svc_name = "sshd" if distro in (
            LinuxDistro.RHEL, LinuxDistro.CENTOS,
            LinuxDistro.ROCKY, LinuxDistro.ORACLE,
            LinuxDistro.AMAZON_LINUX,
        ) else "ssh"

        result = await self.execute_command(
            connection, f"systemctl is-active {svc_name}"
        )
        data["service_running"] = result.stdout.strip() == "active"

        result = await self.execute_command(
            connection, f"systemctl is-enabled {svc_name}"
        )
        data["service_enabled"] = result.stdout.strip() == "enabled"

        # Get effective configuration via sshd -T
        result = await self.execute_command(connection, "sshd -T")
        if result.exit_code == 0:
            config = self._parse_sshd_config(result.stdout)
            data["config"] = config
        else:
            # Fallback to parsing config file
            result = await self.execute_command(
                connection, "cat /etc/ssh/sshd_config"
            )
            if result.exit_code == 0:
                config = self._parse_config_file(result.stdout)
                data["config"] = config

        # Security audit
        data["security_issues"] = self._audit_config(
            data["config"]
        )

        return data

    def _parse_sshd_config(self, content: str) -> Dict[str, str]:
        """Parse sshd -T output (key value pairs)."""
        config = {}
        for line in content.strip().splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                key = parts[0].lower()
                if key in TARGET_SETTINGS:
                    config[key] = parts[1]
        return config

    def _parse_config_file(self, content: str) -> Dict[str, str]:
        """Parse /etc/ssh/sshd_config file."""
        config = {}
        for line in content.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                key = parts[0].lower()
                if key in TARGET_SETTINGS:
                    config[key] = parts[1]
        return config

    def _audit_config(self, config: Dict[str, str]) -> list:
        """Audit SSH config for security issues."""
        issues = []

        if config.get("permitrootlogin", "").lower() not in ("no", "prohibit-password"):
            issues.append({
                "setting": "PermitRootLogin",
                "value": config.get("permitrootlogin", "not set"),
                "recommended": "no",
                "severity": "warning",
            })

        if config.get("passwordauthentication", "").lower() == "yes":
            issues.append({
                "setting": "PasswordAuthentication",
                "value": "yes",
                "recommended": "no",
                "severity": "info",
            })

        if config.get("permitemptypasswords", "").lower() == "yes":
            issues.append({
                "setting": "PermitEmptyPasswords",
                "value": "yes",
                "recommended": "no",
                "severity": "critical",
            })

        max_auth = config.get("maxauthtries", "6")
        try:
            if int(max_auth) > 5:
                issues.append({
                    "setting": "MaxAuthTries",
                    "value": max_auth,
                    "recommended": "<=5",
                    "severity": "info",
                })
        except ValueError:
            pass

        if issues:
            self.add_warning(f"{len(issues)} SSH security issues")

        return issues
