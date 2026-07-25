"""
Base Collector Framework
========================

Enhanced abstract base class for all Linux inventory collectors.
Implements plugin architecture, command allowlist enforcement,
distribution detection, and standardized result handling.

Security: Every command executed MUST be in the COMMAND_ALLOWLIST.
No user-supplied or arbitrary commands may be executed.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set

from backend.ssh.connection import CommandResult, SSHConnection

logger = logging.getLogger("collector")


# ─── Linux Distribution Detection ─────────────────────────────────────────

class LinuxDistro(str, Enum):
    """Supported Linux distributions."""
    RHEL = "rhel"
    AMAZON_LINUX = "amazon_linux"
    UBUNTU = "ubuntu"
    DEBIAN = "debian"
    ROCKY = "rocky"
    ORACLE = "oracle"
    KALI = "kali"
    CENTOS = "centos"
    SUSE = "suse"
    UNKNOWN = "unknown"


# ─── Command Allowlist ─────────────────────────────────────────────────────
# SECURITY: Only these commands may be executed on remote servers.
# This list enables enterprise SAST/DAST compliance reviews.

COMMAND_ALLOWLIST: FrozenSet[str] = frozenset([
    # Distribution detection
    "cat /etc/os-release",
    "cat /etc/redhat-release",
    "cat /etc/debian_version",
    "cat /etc/system-release",
    "uname -a",
    "uname -r",
    "uname -m",
    "uname -n",
    # Operating system
    "hostname",
    "hostname -f",
    "hostnamectl",
    "timedatectl",
    "uptime -s",
    "uptime",
    "cat /proc/uptime",
    "cat /proc/sys/kernel/random/boot_id",
    "stat -c %W /",
    "ls -lct /etc/hostname | tail -1",
    "systemd-detect-virt",
    "systemd-detect-virt --vm",
    "cat /sys/class/dmi/id/sys_vendor",
    "cat /sys/class/dmi/id/product_name",
    "needs-restarting -r",
    "cat /var/run/reboot-required",
    "date +%Y-%m-%dT%H:%M:%S%z",
    # Users and groups
    "cat /etc/passwd",
    "cat /etc/shadow",
    "cat /etc/group",
    "cat /etc/gshadow",
    "cat /etc/login.defs",
    "getent passwd",
    "getent group",
    "lastlog",
    "faillog -a",
    # User details (parameterized by scripts)
    "chage -l",
    "passwd -S",
    # Sudo
    "cat /etc/sudoers",
    "cat /etc/sudoers.d/*",
    "ls -la /etc/sudoers.d/",
    "grep -r '' /etc/sudoers.d/",
    "visudo -c",
    # Password policies
    "cat /etc/pam.d/system-auth",
    "cat /etc/pam.d/password-auth",
    "cat /etc/pam.d/common-password",
    "cat /etc/pam.d/common-auth",
    "cat /etc/security/pwquality.conf",
    "cat /etc/security/faillock.conf",
    "pam_tally2",
    "faillock",
    # Filesystem
    "df -PTh",
    "df -PT",
    "mount",
    "cat /etc/fstab",
    "cat /proc/mounts",
    "findmnt -J",
    "findmnt --json",
    "stat -f /",
    # NFS stale check
    "timeout 5 stat -t",
    # Packages - RPM based
    "rpm -qa --queryformat",
    "rpm -qa --qf '%{NAME}|%{VERSION}|%{RELEASE}|%{ARCH}|%{VENDOR}|%{INSTALLTIME:date}\\n'",
    "yum list installed",
    "dnf list installed",
    "yum repolist",
    "dnf repolist",
    # Packages - Debian based
    "dpkg-query -W -f='${Package}|${Version}|${Architecture}|${Status}\\n'",
    "apt list --installed",
    # Services
    "systemctl list-units --type=service --all --no-pager --no-legend",
    "systemctl list-unit-files --type=service --no-pager --no-legend",
    "systemctl show --no-pager",
    "systemctl is-failed --quiet",
    # Chrony / NTP
    "chronyc tracking",
    "chronyc sources -v",
    "chronyc sourcestats",
    "systemctl is-active chronyd",
    "systemctl is-enabled chronyd",
    "systemctl is-active chrony",
    "systemctl is-enabled chrony",
    "timedatectl show",
    "cat /etc/chrony.conf",
    "cat /etc/chrony/chrony.conf",
    # Network
    "ip addr show",
    "ip route show",
    "ip -4 addr show",
    "ip -6 addr show",
    "cat /etc/resolv.conf",
    "cat /etc/hostname",
    "cat /etc/hosts",
    "ip link show",
    # SSH configuration
    "sshd -T",
    "ssh -V",
    "cat /etc/ssh/sshd_config",
    "systemctl is-active sshd",
    "systemctl is-active ssh",
    "systemctl is-enabled sshd",
    "systemctl is-enabled ssh",
    # Cron and timers
    "cat /etc/crontab",
    "ls -la /etc/cron.d/",
    "cat /etc/cron.d/*",
    "ls -la /etc/cron.daily/",
    "ls -la /etc/cron.hourly/",
    "ls -la /etc/cron.weekly/",
    "ls -la /etc/cron.monthly/",
    "crontab -l",
    "systemctl list-timers --all --no-pager --no-legend",
    # Authorized keys detection
    "find /home -name authorized_keys -type f",
    "find /root -name authorized_keys -type f",
    "test -f /root/.ssh/authorized_keys && echo exists || echo missing",
])

# Commands that are parameterized at runtime (validated by prefix)
PARAMETERIZED_COMMAND_PREFIXES: FrozenSet[str] = frozenset([
    "chage -l ",
    "passwd -S ",
    "id ",
    "groups ",
    "systemctl show ",
    "systemctl is-active ",
    "systemctl is-enabled ",
    "systemctl is-failed ",
    "crontab -l -u ",
    "timeout 5 stat -t ",
    "test -f ",
    "cat /home/",
    "find /home/",
    "rpm -qa --queryformat",
    "dpkg-query -W",
])


def is_command_allowed(command: str) -> bool:
    """
    Verify a command is in the allowlist.

    Security enforcement: prevents execution of arbitrary
    or user-supplied commands on remote servers.

    Args:
        command: The full command string to validate.

    Returns:
        True if the command is allowed to execute.
    """
    # Strip whitespace for comparison
    cmd = command.strip()

    # Check exact match
    if cmd in COMMAND_ALLOWLIST:
        return True

    # Check parameterized prefixes
    for prefix in PARAMETERIZED_COMMAND_PREFIXES:
        if cmd.startswith(prefix):
            return True

    return False


# ─── Collector Result ──────────────────────────────────────────────────────

@dataclass
class CollectorResult:
    """
    Standardized result returned by every collector.

    Attributes:
        collector_name: Name of the collector that produced this.
        collector_version: Version of the collector.
        success: Whether collection completed successfully.
        data: Collected structured data (JSON-serializable).
        warnings: Non-fatal issues encountered.
        errors: Fatal errors that prevented collection.
        commands_run: Number of SSH commands executed.
        duration_seconds: Total collection time.
        metadata: Additional metadata about the collection.
        raw_outputs: Optional raw command outputs (configurable).
    """

    collector_name: str
    collector_version: str = "1.0.0"
    success: bool = False
    data: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    commands_run: int = 0
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_outputs: Dict[str, str] = field(default_factory=dict)


# ─── Base Collector ────────────────────────────────────────────────────────

class BaseCollector(ABC):
    """
    Abstract base class for all inventory collectors.

    Every collector must:
    1. Be independent (no dependencies on other collectors)
    2. Return structured JSON data via CollectorResult
    3. Never directly update the database
    4. Handle errors gracefully (never crash the collection)
    5. Only execute commands from the COMMAND_ALLOWLIST

    Plugin Contract:
    - Define name, version, description, supported_distros
    - Implement collect() method
    - Use execute_command() for all SSH operations
    """

    # ─── Subclass Configuration ────────────────────────────────────
    name: str = "base"
    version: str = "1.0.0"
    description: str = "Base collector"
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)
    enabled: bool = True

    def __init__(self):
        self._logger = logging.getLogger(f"collector.{self.name}")
        self._commands_run = 0
        self._warnings: List[str] = []

    async def run(
        self,
        connection: SSHConnection,
        distro: LinuxDistro = LinuxDistro.UNKNOWN,
        store_raw: bool = False,
    ) -> CollectorResult:
        """
        Execute the collector with full error handling and timing.

        This is the public entry point called by the orchestrator.

        Args:
            connection: Active SSH connection to the target.
            distro: Detected Linux distribution.
            store_raw: Whether to include raw command outputs.

        Returns:
            CollectorResult with collected data or error info.
        """
        start_time = time.time()
        self._commands_run = 0
        self._warnings = []

        result = CollectorResult(
            collector_name=self.name,
            collector_version=self.version,
        )

        # Check distribution support
        if distro != LinuxDistro.UNKNOWN and distro not in self.supported_distros:
            result.success = False
            result.errors.append(
                f"Unsupported distribution: {distro.value}"
            )
            result.duration_seconds = time.time() - start_time
            return result

        try:
            self._logger.info(
                f"Starting {self.name} collection",
                extra={"distro": distro.value},
            )

            data = await self.collect(connection, distro)

            result.success = True
            result.data = data
            result.warnings = self._warnings.copy()
            result.metadata = {
                "collector_version": self.version,
                "collector_description": self.description,
                "distro": distro.value,
                "supported_distros": [
                    d.value for d in self.supported_distros
                ],
            }

            self._logger.info(
                f"{self.name} collection completed",
                extra={
                    "commands_run": self._commands_run,
                    "warnings": len(self._warnings),
                },
            )

        except Exception as e:
            result.success = False
            result.errors.append(f"{type(e).__name__}: {str(e)}")
            result.warnings = self._warnings.copy()
            self._logger.error(
                f"{self.name} collection failed: {e}",
                exc_info=True,
            )

        result.commands_run = self._commands_run
        result.duration_seconds = time.time() - start_time
        return result

    @abstractmethod
    async def collect(
        self,
        connection: SSHConnection,
        distro: LinuxDistro,
    ) -> Dict[str, Any]:
        """
        Perform the actual data collection.

        Subclasses implement this to execute SSH commands
        and return structured data.

        Args:
            connection: Active SSH connection.
            distro: Detected Linux distribution.

        Returns:
            Dictionary of collected data (JSON-serializable).
        """
        ...

    async def execute_command(
        self,
        connection: SSHConnection,
        command: str,
        timeout: Optional[int] = None,
        required: bool = False,
    ) -> CommandResult:
        """
        Execute an allowlisted command on the remote server.

        Security: Validates command against allowlist before execution.

        Args:
            connection: SSH connection.
            command: Command to execute (must be allowlisted).
            timeout: Optional timeout override.
            required: If True, raises on failure.

        Returns:
            CommandResult from SSH execution.

        Raises:
            SecurityError: If command is not in allowlist.
            RuntimeError: If required and command fails.
        """
        # Security enforcement
        if not is_command_allowed(command):
            error_msg = f"Command not in allowlist: {command[:80]}"
            self._logger.error(error_msg)
            raise SecurityError(error_msg)

        self._logger.debug(f"Executing: {command[:100]}")
        self._commands_run += 1

        result = await connection.execute(command, timeout=timeout)

        if result.exit_code != 0:
            if required:
                raise RuntimeError(
                    f"Required command failed (exit={result.exit_code}): "
                    f"{command[:80]} - {result.stderr[:200]}"
                )
            elif result.stderr:
                self._logger.debug(
                    f"Command returned non-zero",
                    extra={
                        "command": command[:80],
                        "exit_code": result.exit_code,
                    },
                )

        return result

    def add_warning(self, message: str) -> None:
        """Add a non-fatal warning to the collection result."""
        self._warnings.append(message)
        self._logger.warning(message)


class SecurityError(Exception):
    """Raised when a command fails security validation."""
    pass
