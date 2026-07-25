"""
Change Detection Engine
=======================

Compares consecutive inventory snapshots and identifies changes
across all collector categories. Only detected differences are
stored in the change history.

Generates human-readable change summaries.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from backend.models.change_history import ChangeHistory
from backend.models.base import generate_uuid

logger = logging.getLogger("collector")


# ─── Severity Rules ───────────────────────────────────────────────────────
# Maps (category, change_type) to severity level.

SEVERITY_MAP = {
    # Operating System
    ("operating_system", "kernel_changed"): "warning",
    ("operating_system", "distribution_changed"): "critical",
    ("operating_system", "reboot_pending"): "info",
    # Users
    ("users", "added"): "warning",
    ("users", "removed"): "warning",
    ("users", "locked"): "info",
    ("users", "unlocked"): "warning",
    ("users", "password_changed"): "info",
    ("users", "group_changed"): "info",
    ("users", "shell_changed"): "warning",
    # Sudo
    ("sudo", "granted"): "warning",
    ("sudo", "revoked"): "info",
    ("sudo", "nopasswd_added"): "critical",
    ("sudo", "nopasswd_removed"): "info",
    # Filesystem
    ("filesystem", "mount_added"): "info",
    ("filesystem", "mount_removed"): "critical",
    ("filesystem", "options_changed"): "warning",
    ("filesystem", "high_usage"): "warning",
    # Packages
    ("packages", "installed"): "info",
    ("packages", "removed"): "warning",
    ("packages", "upgraded"): "info",
    ("packages", "downgraded"): "warning",
    # Services
    ("services", "started"): "info",
    ("services", "stopped"): "warning",
    ("services", "enabled"): "info",
    ("services", "disabled"): "warning",
    ("services", "failed"): "critical",
    # Chrony
    ("chrony", "service_status_changed"): "warning",
    ("chrony", "config_changed"): "info",
    ("chrony", "sync_lost"): "critical",
    # SSH
    ("ssh_config", "config_changed"): "warning",
    ("ssh_config", "root_login_enabled"): "critical",
    # Cron
    ("cron", "job_added"): "info",
    ("cron", "job_removed"): "info",
    ("cron", "schedule_changed"): "info",
    # Password policy
    ("password_policy", "policy_modified"): "critical",
    # Network
    ("network", "ip_changed"): "info",
    ("network", "dns_changed"): "warning",
    ("network", "gateway_changed"): "warning",
    # Groups
    ("groups", "added"): "info",
    ("groups", "removed"): "info",
    ("groups", "member_added"): "info",
    ("groups", "member_removed"): "info",
    ("groups", "admin_member_added"): "warning",
    ("groups", "admin_member_removed"): "warning",
}


def _severity(category: str, change_type: str) -> str:
    """Get severity for a category/change_type combination."""
    return SEVERITY_MAP.get((category, change_type), "info")


class ChangeDetectionEngine:
    """
    Detects and records changes between inventory snapshots.

    Compares current snapshot data with the previous successful
    snapshot for the same server. Generates ChangeHistory records
    for every detected difference.

    Each collector category has a specialized comparison method
    that understands the data structure.
    """

    def detect_changes(
        self,
        server_id: str,
        snapshot_id: str,
        current_data: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]],
    ) -> List[ChangeHistory]:
        """
        Compare two snapshots and return all detected changes.

        Args:
            server_id: Server unique identifier.
            snapshot_id: Current snapshot ID.
            current_data: Current collection results.
            previous_data: Previous collection results (None if first).

        Returns:
            List of ChangeHistory objects (not yet persisted).
        """
        if previous_data is None:
            logger.info(
                "First snapshot, no changes to detect",
                extra={"server_id": server_id},
            )
            return []

        now = datetime.now(timezone.utc)
        changes: List[ChangeHistory] = []

        # Dispatch to category-specific detectors
        detectors = {
            "operating_system": self._detect_os_changes,
            "users": self._detect_user_changes,
            "groups": self._detect_group_changes,
            "sudo": self._detect_sudo_changes,
            "filesystem": self._detect_filesystem_changes,
            "packages": self._detect_package_changes,
            "services": self._detect_service_changes,
            "chrony": self._detect_chrony_changes,
            "ssh_config": self._detect_ssh_changes,
            "cron": self._detect_cron_changes,
            "password_policy": self._detect_policy_changes,
            "network": self._detect_network_changes,
        }

        for category, detector in detectors.items():
            curr = current_data.get(category)
            prev = previous_data.get(category)
            if curr is None:
                continue
            if prev is None:
                # Category newly collected
                continue
            try:
                category_changes = detector(
                    server_id, snapshot_id, curr, prev, now
                )
                changes.extend(category_changes)
            except Exception as e:
                logger.error(
                    f"Change detection failed for {category}: {e}",
                    exc_info=True,
                )

        if changes:
            logger.info(
                f"Detected {len(changes)} total changes",
                extra={"server_id": server_id},
            )

        return changes

    def generate_summary(
        self, changes: List[ChangeHistory]
    ) -> str:
        """
        Generate a human-readable change summary.

        Args:
            changes: List of detected changes.

        Returns:
            Formatted summary string.
        """
        if not changes:
            return "No changes detected."

        lines = [f"Detected {len(changes)} change(s):"]
        by_category: Dict[str, List[ChangeHistory]] = {}
        for c in changes:
            by_category.setdefault(c.category, []).append(c)

        for category, items in sorted(by_category.items()):
            lines.append(f"\n  [{category.upper()}] ({len(items)} changes)")
            for item in items[:10]:
                sev = item.severity.upper()
                lines.append(
                    f"    [{sev}] {item.change_type}: {item.field_name}"
                )
            if len(items) > 10:
                lines.append(f"    ... and {len(items) - 10} more")

        return "\n".join(lines)

    # ─── Category-Specific Detectors ───────────────────────────────

    def _detect_os_changes(
        self, server_id, snapshot_id, curr, prev, now
    ) -> List[ChangeHistory]:
        """Detect OS-level changes."""
        changes = []
        # Kernel change
        if curr.get("kernel_release") != prev.get("kernel_release"):
            changes.append(self._make_change(
                server_id, snapshot_id, "operating_system",
                "kernel_changed", "kernel_release",
                prev.get("kernel_release", ""),
                curr.get("kernel_release", ""), now,
            ))
        # Distribution change
        if curr.get("pretty_name") != prev.get("pretty_name"):
            changes.append(self._make_change(
                server_id, snapshot_id, "operating_system",
                "distribution_changed", "pretty_name",
                prev.get("pretty_name", ""),
                curr.get("pretty_name", ""), now,
            ))
        # Reboot pending state change
        if curr.get("reboot_pending") and not prev.get("reboot_pending"):
            changes.append(self._make_change(
                server_id, snapshot_id, "operating_system",
                "reboot_pending", "reboot_pending",
                "false", "true", now,
            ))
        return changes

    def _detect_user_changes(
        self, server_id, snapshot_id, curr, prev, now
    ) -> List[ChangeHistory]:
        """Detect user account changes."""
        changes = []
        curr_users = {u["username"]: u for u in curr.get("users", [])}
        prev_users = {u["username"]: u for u in prev.get("users", [])}

        # Added users
        for username in set(curr_users) - set(prev_users):
            changes.append(self._make_change(
                server_id, snapshot_id, "users", "added",
                username, None, f"UID={curr_users[username]['uid']}", now,
            ))

        # Removed users
        for username in set(prev_users) - set(curr_users):
            changes.append(self._make_change(
                server_id, snapshot_id, "users", "removed",
                username, f"UID={prev_users[username]['uid']}", None, now,
            ))

        # Modified users
        for username in set(curr_users) & set(prev_users):
            cu = curr_users[username]
            pu = prev_users[username]
            if cu.get("account_locked") and not pu.get("account_locked"):
                changes.append(self._make_change(
                    server_id, snapshot_id, "users", "locked",
                    username, "unlocked", "locked", now,
                ))
            elif not cu.get("account_locked") and pu.get("account_locked"):
                changes.append(self._make_change(
                    server_id, snapshot_id, "users", "unlocked",
                    username, "locked", "unlocked", now,
                ))
            if cu.get("password_last_changed") != pu.get("password_last_changed"):
                changes.append(self._make_change(
                    server_id, snapshot_id, "users", "password_changed",
                    username,
                    pu.get("password_last_changed", ""),
                    cu.get("password_last_changed", ""), now,
                ))
            if cu.get("secondary_groups") != pu.get("secondary_groups"):
                changes.append(self._make_change(
                    server_id, snapshot_id, "users", "group_changed",
                    username,
                    str(pu.get("secondary_groups", [])),
                    str(cu.get("secondary_groups", [])), now,
                ))
            if cu.get("login_shell") != pu.get("login_shell"):
                changes.append(self._make_change(
                    server_id, snapshot_id, "users", "shell_changed",
                    username,
                    pu.get("login_shell", ""),
                    cu.get("login_shell", ""), now,
                ))
        return changes

    def _detect_group_changes(
        self, server_id, snapshot_id, curr, prev, now
    ) -> List[ChangeHistory]:
        """Detect group changes."""
        changes = []
        curr_groups = {g["name"]: g for g in curr.get("groups", [])}
        prev_groups = {g["name"]: g for g in prev.get("groups", [])}

        for name in set(curr_groups) - set(prev_groups):
            changes.append(self._make_change(
                server_id, snapshot_id, "groups", "added",
                name, None, f"GID={curr_groups[name]['gid']}", now,
            ))
        for name in set(prev_groups) - set(curr_groups):
            changes.append(self._make_change(
                server_id, snapshot_id, "groups", "removed",
                name, f"GID={prev_groups[name]['gid']}", None, now,
            ))
        for name in set(curr_groups) & set(prev_groups):
            cm = set(curr_groups[name].get("members", []))
            pm = set(prev_groups[name].get("members", []))
            is_admin = curr_groups[name].get("is_admin", False)
            for member in cm - pm:
                ctype = "admin_member_added" if is_admin else "member_added"
                changes.append(self._make_change(
                    server_id, snapshot_id, "groups", ctype,
                    f"{name}/{member}", None, member, now,
                ))
            for member in pm - cm:
                ctype = "admin_member_removed" if is_admin else "member_removed"
                changes.append(self._make_change(
                    server_id, snapshot_id, "groups", ctype,
                    f"{name}/{member}", member, None, now,
                ))
        return changes

    def _detect_sudo_changes(
        self, server_id, snapshot_id, curr, prev, now
    ) -> List[ChangeHistory]:
        """Detect sudo privilege changes."""
        changes = []
        curr_priv = {u["username"] for u in curr.get("privileged_users", [])}
        prev_priv = {u["username"] for u in prev.get("privileged_users", [])}

        for user in curr_priv - prev_priv:
            changes.append(self._make_change(
                server_id, snapshot_id, "sudo", "granted",
                user, None, "sudo access granted", now,
            ))
        for user in prev_priv - curr_priv:
            changes.append(self._make_change(
                server_id, snapshot_id, "sudo", "revoked",
                user, "had sudo", "revoked", now,
            ))

        # NOPASSWD changes
        curr_np = {e.get("user_or_group", "") for e in curr.get("nopasswd_entries", [])}
        prev_np = {e.get("user_or_group", "") for e in prev.get("nopasswd_entries", [])}
        for entry in curr_np - prev_np:
            if entry:
                changes.append(self._make_change(
                    server_id, snapshot_id, "sudo", "nopasswd_added",
                    entry, None, "NOPASSWD rule added", now,
                ))
        for entry in prev_np - curr_np:
            if entry:
                changes.append(self._make_change(
                    server_id, snapshot_id, "sudo", "nopasswd_removed",
                    entry, "NOPASSWD rule", None, now,
                ))
        return changes

    def _detect_filesystem_changes(
        self, server_id, snapshot_id, curr, prev, now
    ) -> List[ChangeHistory]:
        """Detect filesystem mount changes."""
        changes = []
        curr_mounts = {m["mount_point"]: m for m in curr.get("mounts", [])}
        prev_mounts = {m["mount_point"]: m for m in prev.get("mounts", [])}

        for mp in set(curr_mounts) - set(prev_mounts):
            changes.append(self._make_change(
                server_id, snapshot_id, "filesystem", "mount_added",
                mp, None, curr_mounts[mp].get("device", ""), now,
            ))
        for mp in set(prev_mounts) - set(curr_mounts):
            changes.append(self._make_change(
                server_id, snapshot_id, "filesystem", "mount_removed",
                mp, prev_mounts[mp].get("device", ""), None, now,
            ))
        for mp in set(curr_mounts) & set(prev_mounts):
            co = curr_mounts[mp].get("mount_options", "")
            po = prev_mounts[mp].get("mount_options", "")
            if co != po:
                changes.append(self._make_change(
                    server_id, snapshot_id, "filesystem",
                    "options_changed", mp, po[:200], co[:200], now,
                ))
        return changes

    def _detect_package_changes(
        self, server_id, snapshot_id, curr, prev, now
    ) -> List[ChangeHistory]:
        """Detect package install/remove/upgrade/downgrade."""
        changes = []
        curr_pkgs = {p["name"]: p for p in curr.get("packages", [])}
        prev_pkgs = {p["name"]: p for p in prev.get("packages", [])}

        for name in set(curr_pkgs) - set(prev_pkgs):
            changes.append(self._make_change(
                server_id, snapshot_id, "packages", "installed",
                name, None, curr_pkgs[name].get("version", ""), now,
            ))
        for name in set(prev_pkgs) - set(curr_pkgs):
            changes.append(self._make_change(
                server_id, snapshot_id, "packages", "removed",
                name, prev_pkgs[name].get("version", ""), None, now,
            ))
        for name in set(curr_pkgs) & set(prev_pkgs):
            cv = curr_pkgs[name].get("version", "")
            pv = prev_pkgs[name].get("version", "")
            if cv != pv:
                # Simple heuristic: if new version sorts higher, it's upgrade
                ctype = "upgraded" if cv > pv else "downgraded"
                changes.append(self._make_change(
                    server_id, snapshot_id, "packages", ctype,
                    name, pv, cv, now,
                ))
        return changes

    def _detect_service_changes(
        self, server_id, snapshot_id, curr, prev, now
    ) -> List[ChangeHistory]:
        """Detect systemd service state changes."""
        changes = []
        curr_svcs = {s["name"]: s for s in curr.get("services", [])}
        prev_svcs = {s["name"]: s for s in prev.get("services", [])}

        for name in set(curr_svcs) & set(prev_svcs):
            cs = curr_svcs[name]
            ps = prev_svcs[name]
            # Running state
            if cs.get("sub_state") == "running" and ps.get("sub_state") != "running":
                changes.append(self._make_change(
                    server_id, snapshot_id, "services", "started",
                    name, ps.get("sub_state", ""), "running", now,
                ))
            elif cs.get("sub_state") != "running" and ps.get("sub_state") == "running":
                changes.append(self._make_change(
                    server_id, snapshot_id, "services", "stopped",
                    name, "running", cs.get("sub_state", ""), now,
                ))
            # Enabled state
            if cs.get("enabled") == "enabled" and ps.get("enabled") != "enabled":
                changes.append(self._make_change(
                    server_id, snapshot_id, "services", "enabled",
                    name, ps.get("enabled", ""), "enabled", now,
                ))
            elif cs.get("enabled") == "disabled" and ps.get("enabled") != "disabled":
                changes.append(self._make_change(
                    server_id, snapshot_id, "services", "disabled",
                    name, ps.get("enabled", ""), "disabled", now,
                ))
            # Failed state
            if cs.get("is_failed") and not ps.get("is_failed"):
                changes.append(self._make_change(
                    server_id, snapshot_id, "services", "failed",
                    name, "active", "failed", now,
                ))
        return changes

    def _detect_chrony_changes(
        self, server_id, snapshot_id, curr, prev, now
    ) -> List[ChangeHistory]:
        """Detect chrony/NTP changes."""
        changes = []
        if curr.get("service_running") != prev.get("service_running"):
            changes.append(self._make_change(
                server_id, snapshot_id, "chrony",
                "service_status_changed", "chronyd",
                str(prev.get("service_running")),
                str(curr.get("service_running")), now,
            ))
        if curr.get("synchronized") is False and prev.get("synchronized") is True:
            changes.append(self._make_change(
                server_id, snapshot_id, "chrony", "sync_lost",
                "time_sync", "synchronized", "NOT synchronized", now,
            ))
        return changes

    def _detect_ssh_changes(
        self, server_id, snapshot_id, curr, prev, now
    ) -> List[ChangeHistory]:
        """Detect SSH configuration changes."""
        changes = []
        curr_cfg = curr.get("config", {})
        prev_cfg = prev.get("config", {})

        for key in set(curr_cfg) | set(prev_cfg):
            cv = curr_cfg.get(key, "")
            pv = prev_cfg.get(key, "")
            if cv != pv:
                ctype = "config_changed"
                if key == "permitrootlogin" and cv.lower() in ("yes", "without-password"):
                    ctype = "root_login_enabled"
                changes.append(self._make_change(
                    server_id, snapshot_id, "ssh_config", ctype,
                    key, pv, cv, now,
                ))
        return changes

    def _detect_cron_changes(
        self, server_id, snapshot_id, curr, prev, now
    ) -> List[ChangeHistory]:
        """Detect cron/timer changes."""
        changes = []

        def _job_key(job):
            return f"{job.get('schedule','')}|{job.get('command','')}"

        curr_jobs = set()
        for jobs_list in (curr.get("system_crontab", []),
                          curr.get("cron_d_jobs", []),
                          curr.get("user_crontabs", [])):
            for job in jobs_list:
                curr_jobs.add(_job_key(job))

        prev_jobs = set()
        for jobs_list in (prev.get("system_crontab", []),
                          prev.get("cron_d_jobs", []),
                          prev.get("user_crontabs", [])):
            for job in jobs_list:
                prev_jobs.add(_job_key(job))

        for key in curr_jobs - prev_jobs:
            changes.append(self._make_change(
                server_id, snapshot_id, "cron", "job_added",
                key[:200], None, "added", now,
            ))
        for key in prev_jobs - curr_jobs:
            changes.append(self._make_change(
                server_id, snapshot_id, "cron", "job_removed",
                key[:200], "existed", None, now,
            ))
        return changes

    def _detect_policy_changes(
        self, server_id, snapshot_id, curr, prev, now
    ) -> List[ChangeHistory]:
        """Detect password policy changes."""
        changes = []
        curr_defs = curr.get("login_defs", {})
        prev_defs = prev.get("login_defs", {})

        for key in set(curr_defs) | set(prev_defs):
            cv = curr_defs.get(key, "")
            pv = prev_defs.get(key, "")
            if cv != pv:
                changes.append(self._make_change(
                    server_id, snapshot_id, "password_policy",
                    "policy_modified", key, pv, cv, now,
                ))

        curr_pq = curr.get("pwquality", {})
        prev_pq = prev.get("pwquality", {})
        for key in set(curr_pq) | set(prev_pq):
            if curr_pq.get(key, "") != prev_pq.get(key, ""):
                changes.append(self._make_change(
                    server_id, snapshot_id, "password_policy",
                    "policy_modified", f"pwquality.{key}",
                    prev_pq.get(key, ""), curr_pq.get(key, ""), now,
                ))
        return changes

    def _detect_network_changes(
        self, server_id, snapshot_id, curr, prev, now
    ) -> List[ChangeHistory]:
        """Detect network identity changes."""
        changes = []
        if curr.get("default_gateway") != prev.get("default_gateway"):
            changes.append(self._make_change(
                server_id, snapshot_id, "network", "gateway_changed",
                "default_gateway",
                prev.get("default_gateway", ""),
                curr.get("default_gateway", ""), now,
            ))
        if curr.get("dns_servers") != prev.get("dns_servers"):
            changes.append(self._make_change(
                server_id, snapshot_id, "network", "dns_changed",
                "dns_servers",
                str(prev.get("dns_servers", [])),
                str(curr.get("dns_servers", [])), now,
            ))
        return changes

    # ─── Helper ────────────────────────────────────────────────────

    def _make_change(
        self,
        server_id: str,
        snapshot_id: str,
        category: str,
        change_type: str,
        field_name: str,
        old_value: Optional[str],
        new_value: Optional[str],
        detected_at: datetime,
    ) -> ChangeHistory:
        """Create a ChangeHistory instance."""
        return ChangeHistory(
            id=generate_uuid(),
            server_id=server_id,
            snapshot_id=snapshot_id,
            category=category,
            change_type=change_type,
            field_name=field_name,
            old_value=old_value[:500] if old_value else None,
            new_value=new_value[:500] if new_value else None,
            severity=_severity(category, change_type),
            detected_at=detected_at,
        )
