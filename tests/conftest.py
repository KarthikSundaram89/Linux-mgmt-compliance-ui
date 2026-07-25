"""
Shared test fixtures and mock SSH connection.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Optional
from unittest.mock import AsyncMock

import pytest

from backend.collectors.base import LinuxDistro
from backend.ssh.connection import CommandResult, SSHConnection


class MockSSHConnection:
    """
    Mock SSH connection for testing collectors.

    Accepts a mapping of command -> (stdout, stderr, exit_code)
    to simulate remote command execution without network access.
    """

    def __init__(self, responses: Optional[Dict[str, tuple]] = None):
        self._responses = responses or {}

    async def execute(
        self, command: str, timeout: Optional[int] = None
    ) -> CommandResult:
        """Return mocked command result."""
        if command in self._responses:
            stdout, stderr, exit_code = self._responses[command]
            return CommandResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                duration_seconds=0.01,
            )
        # Default: command not found
        return CommandResult(
            stdout="",
            stderr=f"mock: command not configured: {command[:80]}",
            exit_code=127,
            duration_seconds=0.01,
        )

    @property
    def is_connected(self) -> bool:
        return True


@pytest.fixture
def mock_connection():
    """Provide a MockSSHConnection factory."""
    def _factory(responses: Dict[str, tuple]) -> MockSSHConnection:
        return MockSSHConnection(responses)
    return _factory


@pytest.fixture
def rhel_distro():
    """RHEL distribution fixture."""
    return LinuxDistro.RHEL


@pytest.fixture
def ubuntu_distro():
    """Ubuntu distribution fixture."""
    return LinuxDistro.UBUNTU
