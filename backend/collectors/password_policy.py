"""
Password Policy Collector
=========================

Collects global password policy settings including
login.defs, PAM configuration, and lockout settings.
"""

from typing import Any, Dict, FrozenSet

from backend.collectors.base import BaseCollector, LinuxDistro
from backend.ssh.connection import SSHConnection


class PasswordPolicyCollector(BaseCollector):
    """Collects password policy and compliance settings."""

    name = "password_policy"
    version = "1.0.0"
    description = "Collects password policy, PAM, and lockout config"
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)

    async def collect(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> Dict[str, Any]:
        """Collect password policy data."""
        data: Dict[str, Any] = {
            "login_defs": {},
            "pam_config": {},
            "pwquality": {},
            "lockout": {},
            "compliance_issues": [],
        }

        # ─── /etc/login.defs ───────────────────────────────────────
        result = await self.execute_command(
            connection, "cat /etc/login.defs"
        )
        if result.exit_code == 0:
            data["login_defs"] = self._parse_login_defs(
                result.stdout
            )

        # ─── PAM configuration ─────────────────────────────────────
        if distro in (
            LinuxDistro.RHEL, LinuxDistro.CENTOS,
            LinuxDistro.ROCKY, LinuxDistro.ORACLE,
            LinuxDistro.AMAZON_LINUX,
        ):
            # RHEL-family PAM files
            result = await self.execute_command(
                connection, "cat /etc/pam.d/system-auth"
            )
            if result.exit_code == 0:
                data["pam_config"]["system_auth"] = (
                    self._parse_pam(result.stdout)
                )
            result = await self.execute_command(
                connection, "cat /etc/pam.d/password-auth"
            )
            if result.exit_code == 0:
                data["pam_config"]["password_auth"] = (
                    self._parse_pam(result.stdout)
                )
        else:
            # Debian-family PAM files
            result = await self.execute_command(
                connection, "cat /etc/pam.d/common-password"
            )
            if result.exit_code == 0:
                data["pam_config"]["common_password"] = (
                    self._parse_pam(result.stdout)
                )
            result = await self.execute_command(
                connection, "cat /etc/pam.d/common-auth"
            )
            if result.exit_code == 0:
                data["pam_config"]["common_auth"] = (
                    self._parse_pam(result.stdout)
                )

        # ─── pwquality.conf ────────────────────────────────────────
        result = await self.execute_command(
            connection, "cat /etc/security/pwquality.conf"
        )
        if result.exit_code == 0:
            data["pwquality"] = self._parse_key_value(
                result.stdout
            )

        # ─── Lockout (faillock) ────────────────────────────────────
        result = await self.execute_command(
            connection, "cat /etc/security/faillock.conf"
        )
        if result.exit_code == 0:
            data["lockout"] = self._parse_key_value(result.stdout)

        # ─── Compliance checks ─────────────────────────────────────
        data["compliance_issues"] = self._check_compliance(
            data
        )

        return data

    def _parse_login_defs(self, content: str) -> Dict[str, str]:
        """Parse /etc/login.defs."""
        defs = {}
        target_keys = {
            "PASS_MAX_DAYS", "PASS_MIN_DAYS",
            "PASS_WARN_AGE", "PASS_MIN_LEN",
            "LOGIN_RETRIES", "LOGIN_TIMEOUT",
            "UID_MIN", "UID_MAX", "GID_MIN", "GID_MAX",
            "ENCRYPT_METHOD", "SHA_CRYPT_MIN_ROUNDS",
            "CREATE_HOME", "UMASK",
        }
        for line in content.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0] in target_keys:
                defs[parts[0]] = parts[1]
        return defs

    def _parse_pam(self, content: str) -> Dict[str, Any]:
        """Parse PAM configuration for security-relevant modules."""
        modules = []
        for line in content.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 3:
                modules.append({
                    "type": parts[0],
                    "control": parts[1],
                    "module": parts[2],
                    "args": " ".join(parts[3:]) if len(parts) > 3 else "",
                })
        # Extract key settings
        result = {
            "modules": modules,
            "uses_pam_pwquality": any(
                "pam_pwquality" in m["module"] for m in modules
            ),
            "uses_pam_faillock": any(
                "pam_faillock" in m["module"] for m in modules
            ),
            "uses_pam_tally2": any(
                "pam_tally2" in m["module"] for m in modules
            ),
            "password_history": self._extract_pam_arg(
                modules, "pam_pwhistory", "remember"
            ),
        }
        return result

    def _extract_pam_arg(
        self, modules, module_name: str, arg_name: str
    ) -> str:
        """Extract a specific argument from a PAM module."""
        for m in modules:
            if module_name in m["module"]:
                for part in m["args"].split():
                    if part.startswith(f"{arg_name}="):
                        return part.split("=", 1)[1]
        return ""

    def _parse_key_value(self, content: str) -> Dict[str, str]:
        """Parse key = value config files."""
        data = {}
        for line in content.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                data[key.strip()] = value.strip()
        return data

    def _check_compliance(self, data: Dict) -> list:
        """Check for non-compliant password settings."""
        issues = []
        defs = data.get("login_defs", {})

        max_days = defs.get("PASS_MAX_DAYS", "99999")
        if int(max_days) > 90:
            issues.append({
                "setting": "PASS_MAX_DAYS",
                "value": max_days,
                "expected": "<=90",
                "severity": "warning",
                "message": "Password max age exceeds 90 days",
            })

        min_days = defs.get("PASS_MIN_DAYS", "0")
        if int(min_days) < 1:
            issues.append({
                "setting": "PASS_MIN_DAYS",
                "value": min_days,
                "expected": ">=1",
                "severity": "info",
                "message": "No minimum password age set",
            })

        min_len = defs.get("PASS_MIN_LEN", "5")
        if int(min_len) < 8:
            issues.append({
                "setting": "PASS_MIN_LEN",
                "value": min_len,
                "expected": ">=8",
                "severity": "warning",
                "message": "Minimum password length below 8",
            })

        if issues:
            self.add_warning(
                f"Found {len(issues)} compliance issues"
            )

        return issues
