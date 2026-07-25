"""
SSH Module
==========

Manages SSH connections to Linux servers using Paramiko.
Provides connection pooling, timeouts, retries, and host key validation.
"""

from backend.ssh.manager import SSHManager
from backend.ssh.connection import SSHConnection
from backend.ssh.pool import SSHConnectionPool

__all__ = ["SSHManager", "SSHConnection", "SSHConnectionPool"]
