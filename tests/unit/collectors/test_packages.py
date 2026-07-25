"""
Unit tests for Package Inventory Collector.
"""

import pytest

from backend.collectors.packages import PackageCollector
from backend.collectors.base import LinuxDistro


RPM_OUTPUT = """bash|5.1.8|1.el9|x86_64|Red Hat, Inc.|Mon 01 Jul 2026 12:00:00 AM UTC
openssl|3.0.7|20.el9|x86_64|Red Hat, Inc.|Mon 01 Jul 2026 12:00:00 AM UTC
kernel|5.14.0|362.el9|x86_64|Red Hat, Inc.|Mon 15 Jul 2026 12:00:00 AM UTC
vim-minimal|9.0.1|1.el9|x86_64|Red Hat, Inc.|Mon 01 Jul 2026 12:00:00 AM UTC
"""

DPKG_OUTPUT = """bash|5.2.15-2ubuntu1|amd64|install ok installed
openssl|3.0.11-1ubuntu1|amd64|install ok installed
linux-image-6.5.0|6.5.0-35.35|amd64|install ok installed
vim|2:9.0.1000-4ubuntu2|amd64|install ok installed
"""


@pytest.fixture
def collector():
    return PackageCollector()


@pytest.mark.asyncio
async def test_rpm_package_collection(collector, mock_connection):
    """Test RPM-based package collection."""
    conn = mock_connection({
        "rpm -qa --qf '%{NAME}|%{VERSION}|%{RELEASE}|%{ARCH}|%{VENDOR}|%{INSTALLTIME:date}\\n'": (RPM_OUTPUT, "", 0),
    })
    result = await collector.run(conn, LinuxDistro.RHEL)

    assert result.success is True
    assert result.data["package_manager"] == "rpm"
    assert result.data["total_count"] == 4

    pkgs = {p["name"]: p for p in result.data["packages"]}
    assert "bash" in pkgs
    assert pkgs["bash"]["version"] == "5.1.8"
    assert pkgs["openssl"]["architecture"] == "x86_64"
    assert pkgs["kernel"]["release"] == "362.el9"


@pytest.mark.asyncio
async def test_dpkg_package_collection(collector, mock_connection):
    """Test dpkg-based package collection."""
    conn = mock_connection({
        "dpkg-query -W -f='${Package}|${Version}|${Architecture}|${Status}\\n'": (DPKG_OUTPUT, "", 0),
    })
    result = await collector.run(conn, LinuxDistro.UBUNTU)

    assert result.success is True
    assert result.data["package_manager"] == "dpkg"
    assert result.data["total_count"] == 4

    pkgs = {p["name"]: p for p in result.data["packages"]}
    assert "bash" in pkgs
    assert "openssl" in pkgs
    assert pkgs["vim"]["architecture"] == "amd64"


@pytest.mark.asyncio
async def test_package_collection_fallback(collector, mock_connection):
    """Test fallback to yum when rpm fails."""
    conn = mock_connection({
        "rpm -qa --qf '%{NAME}|%{VERSION}|%{RELEASE}|%{ARCH}|%{VENDOR}|%{INSTALLTIME:date}\\n'": ("", "command failed", 1),
        "yum list installed": ("Installed Packages\nbash.x86_64    5.1.8-1.el9    @baseos\n", "", 0),
    })
    result = await collector.run(conn, LinuxDistro.RHEL)

    assert result.success is True
    assert len(result.data["packages"]) >= 1
