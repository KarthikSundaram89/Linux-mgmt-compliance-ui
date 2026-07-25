"""
Unit tests for Service Inventory Collector.
"""

import pytest

from backend.collectors.services import ServiceCollector
from backend.collectors.base import LinuxDistro


SYSTEMCTL_OUTPUT = """sshd.service loaded active running OpenSSH server daemon
crond.service loaded active running Command Scheduler
chronyd.service loaded active running NTP client/server
httpd.service loaded failed failed The Apache HTTP Server
firewalld.service loaded active running firewalld - dynamic firewall daemon
"""

UNIT_FILES = """sshd.service enabled
crond.service enabled
chronyd.service enabled
httpd.service enabled
firewalld.service enabled
bluetooth.service disabled
"""


@pytest.fixture
def collector():
    return ServiceCollector()


@pytest.mark.asyncio
async def test_service_collector_success(collector, mock_connection):
    """Test service collection parses all services."""
    conn = mock_connection({
        "systemctl list-units --type=service --all --no-pager --no-legend": (SYSTEMCTL_OUTPUT, "", 0),
        "systemctl list-unit-files --type=service --no-pager --no-legend": (UNIT_FILES, "", 0),
    })
    result = await collector.run(conn, LinuxDistro.RHEL)

    assert result.success is True
    assert result.data["total_count"] == 5
    assert result.data["running_count"] == 4


@pytest.mark.asyncio
async def test_service_collector_detects_failed(collector, mock_connection):
    """Test that failed services are highlighted."""
    conn = mock_connection({
        "systemctl list-units --type=service --all --no-pager --no-legend": (SYSTEMCTL_OUTPUT, "", 0),
        "systemctl list-unit-files --type=service --no-pager --no-legend": (UNIT_FILES, "", 0),
    })
    result = await collector.run(conn, LinuxDistro.RHEL)

    assert result.data["failed_count"] == 1
    assert result.data["failed_services"][0]["name"] == "httpd.service"
    assert len(result.warnings) == 1


@pytest.mark.asyncio
async def test_service_collector_enabled_state(collector, mock_connection):
    """Test enabled/disabled state resolution."""
    conn = mock_connection({
        "systemctl list-units --type=service --all --no-pager --no-legend": (SYSTEMCTL_OUTPUT, "", 0),
        "systemctl list-unit-files --type=service --no-pager --no-legend": (UNIT_FILES, "", 0),
    })
    result = await collector.run(conn, LinuxDistro.RHEL)

    svcs = {s["name"]: s for s in result.data["services"]}
    assert svcs["sshd.service"]["enabled"] == "enabled"
    assert svcs["chronyd.service"]["enabled"] == "enabled"
