"""
Cron & Systemd Timers Collector
===============================

Collects scheduled tasks from system cron, user crontabs,
and systemd timers for operational visibility.
"""

from typing import Any, Dict, FrozenSet, List

from backend.collectors.base import BaseCollector, LinuxDistro
from backend.ssh.connection import SSHConnection


class CronCollector(BaseCollector):
    """Collects cron jobs and systemd timers."""

    name = "cron"
    version = "1.0.0"
    description = "Collects cron jobs and systemd timer schedules"
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)

    async def collect(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> Dict[str, Any]:
        """Collect cron and timer data."""
        data: Dict[str, Any] = {
            "system_crontab": [],
            "cron_d_jobs": [],
            "cron_directories": {},
            "user_crontabs": [],
            "systemd_timers": [],
        }

        # /etc/crontab
        result = await self.execute_command(
            connection, "cat /etc/crontab"
        )
        if result.exit_code == 0:
            data["system_crontab"] = self._parse_crontab(
                result.stdout, source="/etc/crontab"
            )

        # /etc/cron.d/*
        result = await self.execute_command(
            connection, "cat /etc/cron.d/*"
        )
        if result.exit_code == 0:
            data["cron_d_jobs"] = self._parse_crontab(
                result.stdout, source="/etc/cron.d/"
            )

        # cron.daily, cron.hourly, etc.
        for period in ("hourly", "daily", "weekly", "monthly"):
            result = await self.execute_command(
                connection, f"ls -la /etc/cron.{period}/"
            )
            if result.exit_code == 0:
                scripts = self._parse_ls_scripts(result.stdout)
                data["cron_directories"][period] = scripts

        # Root crontab
        result = await self.execute_command(connection, "crontab -l")
        if result.exit_code == 0 and "no crontab" not in result.stderr.lower():
            jobs = self._parse_crontab(
                result.stdout, source="root_crontab", user="root"
            )
            data["user_crontabs"].extend(jobs)

        # Systemd timers
        result = await self.execute_command(
            connection,
            "systemctl list-timers --all --no-pager --no-legend",
        )
        if result.exit_code == 0:
            data["systemd_timers"] = self._parse_timers(
                result.stdout
            )

        # Summary counts
        total_jobs = (
            len(data["system_crontab"])
            + len(data["cron_d_jobs"])
            + len(data["user_crontabs"])
            + len(data["systemd_timers"])
        )
        data["total_scheduled_jobs"] = total_jobs

        return data

    def _parse_crontab(
        self, content: str, source: str = "", user: str = ""
    ) -> List[Dict[str, Any]]:
        """Parse crontab content into structured jobs."""
        jobs = []
        for line in content.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Skip environment variable assignments
            if "=" in line and not any(c in line[:6] for c in "0123456789*"):
                continue
            parts = line.split(None, 5)
            if len(parts) < 6:
                # May be 5 fields + command (no user field)
                if len(parts) >= 5:
                    jobs.append({
                        "minute": parts[0],
                        "hour": parts[1],
                        "day": parts[2],
                        "month": parts[3],
                        "weekday": parts[4],
                        "user": user,
                        "command": "",
                        "schedule": " ".join(parts[:5]),
                        "source": source,
                    })
                continue

            # System crontab has user field
            if source in ("/etc/crontab", "/etc/cron.d/"):
                jobs.append({
                    "minute": parts[0],
                    "hour": parts[1],
                    "day": parts[2],
                    "month": parts[3],
                    "weekday": parts[4],
                    "user": parts[5],
                    "command": " ".join(parts[6:]) if len(parts) > 6 else "",
                    "schedule": " ".join(parts[:5]),
                    "source": source,
                })
            else:
                jobs.append({
                    "minute": parts[0],
                    "hour": parts[1],
                    "day": parts[2],
                    "month": parts[3],
                    "weekday": parts[4],
                    "user": user,
                    "command": " ".join(parts[5:]),
                    "schedule": " ".join(parts[:5]),
                    "source": source,
                })
        return jobs

    def _parse_ls_scripts(self, content: str) -> List[str]:
        """Extract script names from ls output."""
        scripts = []
        for line in content.strip().splitlines():
            parts = line.split()
            if len(parts) >= 9:
                name = parts[-1]
                if name not in (".", ".."):
                    scripts.append(name)
        return scripts

    def _parse_timers(self, content: str) -> List[Dict[str, str]]:
        """Parse systemctl list-timers output."""
        timers = []
        for line in content.strip().splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            # Format: NEXT LEFT LAST PASSED UNIT ACTIVATES
            # The columns are variable-width, so find .timer unit
            timer_units = [p for p in parts if p.endswith(".timer")]
            activates = [p for p in parts if p.endswith(".service")]

            if timer_units:
                timers.append({
                    "timer_unit": timer_units[0],
                    "activates": activates[0] if activates else "",
                    "raw_line": line.strip(),
                })
        return timers
