"""
Unit tests for Operating System Collector.
"""

import pytest

from backend.collectors.operating_system import OperatingSystemCollector
from backend.collectors.base import LinuxDistro


OS_RELEASE = """NAME="Red Hat Enterprise Linux"
VERSION="8.9 (Ootpa)"
ID="rhel"
ID_LIKE="fedora"
VERSION_ID="8.9"
PRETTY_NAME="Red Hat Enterprise Linux 8.9 (Ootpa)"
"""

HOSTNAMECTL = """Static hostname: web-server-01
         Icon name: computer-vm
           Chassis: vm
        Machine ID: abc123
           Boot ID: def456
    Virtualization: kvm
  Operating System: Red Hat Enterprise Linux 8.9 (Ootpa)
       CPE OS Name: cpe:/o:redhat:enterprise_linux:8::baseos
            Kernel: Linux 4.18.0-513.el8.x86_64
      Architecture: x86-64
"""


@pytest.fixture
def collector():
    return OperatingSystemCollector()


@pytest.fixture
def mock_rhel_connection(mock_connection):
    return mock_connection({
        "cat /etc/os-release": (OS_RELEASE, "", 0),
        "hostname": ("web-server-01\n", "", 0),
        "hostname -f": ("web-server-01.prod.internal\n", "", 0),
        "uname -r": ("4.18.0-513.el8.x86_64\n", "", 0),
        "uname -a": ("Linux web-server-01 4.18.0-513.el8.x86_64 #1 SMP x86_64 x86_64 x86_64 GNU/Linux\n", "", 0),
        "uname -m": ("x86_64\n", "", 0),
        "hostnamectl": (HOSTNAMECTL, "", 0),
        "systemd-detect-virt": ("kvm\n", "", 0),
        "cat /sys/class/dmi/id/sys_vendor": ("Amazon EC2\n", "", 0),
        "timedatectl": ("Time zone: America/New_York (EDT, -0400)\n", "", 0),
        "date +%Y-%m-%dT%H:%M:%S%z": ("2026-07-25T14:30:00-0400\n", "", 0),
        "uptime -s": ("2026-07-01 03:15:22\n", "", 0),
        "cat /proc/uptime": ("2112000.50 1800000.30\n", "", 0),
        "cat /proc/sys/kernel/random/boot_id": ("a1b2c3d4-e5f6-7890-abcd-ef1234567890\n", "", 0),
        "stat -c %W /": ("1688000000\n", "", 0),
        "needs-restarting -r": ("", "Reboot is required\n", 1),
        "cat /var/run/reboot-required": ("", "No such file", 1),
    })


@pytest.mark.asyncio
async def test_os_collector_success(collector, mock_rhel_connection):
    """Test OS collector returns structured data."""
    result = await collector.run(mock_rhel_connection, LinuxDistro.RHEL)

    assert result.success is True
    assert result.collector_name == "operating_system"
    assert result.data["hostname"] == "web-server-01"
    assert result.data["fqdn"] == "web-server-01.prod.internal"
    assert result.data["kernel_release"] == "4.18.0-513.el8.x86_64"
    assert result.data["machine_type"] == "x86_64"
    assert result.data["virtualization_type"] == "kvm"
    assert result.data["virtualization_vendor"] == "Amazon EC2"
    assert result.data["reboot_pending"] is True
    assert result.data["boot_id"] == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


@pytest.mark.asyncio
async def test_os_collector_distro_parse(collector, mock_rhel_connection):
    """Test OS release parsing."""
    result = await collector.run(mock_rhel_connection, LinuxDistro.RHEL)

    assert result.data["distribution"] == "rhel"
    assert result.data["distribution_version"] == "8.9"
    assert "Red Hat" in result.data["pretty_name"]


@pytest.mark.asyncio
async def test_os_collector_handles_missing_commands(collector, mock_connection):
    """Test graceful handling when commands fail."""
    conn = mock_connection({
        "cat /etc/os-release": (OS_RELEASE, "", 0),
        "hostname": ("minimal-server\n", "", 0),
        "hostname -f": ("", "hostname: Name or service not known", 1),
        "uname -r": ("5.15.0\n", "", 0),
        "uname -a": ("Linux minimal 5.15.0 #1 SMP x86_64\n", "", 0),
        "uname -m": ("x86_64\n", "", 0),
        "hostnamectl": ("", "command not found", 127),
        "systemd-detect-virt": ("", "", 1),
        "cat /sys/class/dmi/id/sys_vendor": ("", "", 1),
        "timedatectl": ("", "", 127),
        "date +%Y-%m-%dT%H:%M:%S%z": ("2026-07-25T10:00:00+0000\n", "", 0),
        "uptime -s": ("", "", 1),
        "cat /proc/uptime": ("86400.0 70000.0\n", "", 0),
        "cat /proc/sys/kernel/random/boot_id": ("", "", 1),
        "stat -c %W /": ("0\n", "", 0),
        "needs-restarting -r": ("", "", 0),
        "cat /var/run/reboot-required": ("", "", 1),
    })
    result = await collector.run(conn, LinuxDistro.RHEL)

    assert result.success is True
    assert result.data["hostname"] == "minimal-server"
    assert result.data["kernel_release"] == "5.15.0"
