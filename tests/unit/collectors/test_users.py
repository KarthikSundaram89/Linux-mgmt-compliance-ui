"""
Unit tests for User Inventory Collector.
"""

import pytest

from backend.collectors.users import UserCollector
from backend.collectors.base import LinuxDistro


PASSWD = """root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sshd:x:74:74:Privilege-separated SSH:/var/empty/sshd:/sbin/nologin
jdoe:x:1001:1001:John Doe:/home/jdoe:/bin/bash
asmith:x:1002:1002:Alice Smith:/home/asmith:/bin/bash
deploy:x:1003:1003:Deploy User:/home/deploy:/bin/bash
"""

GROUP = """root:x:0:
wheel:x:10:jdoe
users:x:100:jdoe,asmith
docker:x:998:deploy
jdoe:x:1001:
asmith:x:1002:
deploy:x:1003:
"""

SHADOW = """root:$6$hash:19500:0:99999:7:::
jdoe:$6$hash:19700:1:90:7:::
asmith:!$6$hash:19600:0:60:7:::
deploy:$6$hash:19650:0:99999:7:::
"""

LASTLOG = """Username         Port     From             Latest
root             pts/0    10.0.0.1         Mon Jul 20 14:30:00 +0000 2026
jdoe             pts/1    10.0.0.50        Fri Jul 24 09:15:00 +0000 2026
asmith           pts/2    10.0.0.51        Thu Jul 23 16:00:00 +0000 2026
deploy                                     **Never logged in**
"""

AUTH_KEYS = """/home/jdoe/.ssh/authorized_keys
/home/deploy/.ssh/authorized_keys
"""


@pytest.fixture
def collector():
    return UserCollector()


@pytest.fixture
def mock_user_connection(mock_connection):
    return mock_connection({
        "cat /etc/passwd": (PASSWD, "", 0),
        "cat /etc/group": (GROUP, "", 0),
        "cat /etc/shadow": (SHADOW, "", 0),
        "lastlog": (LASTLOG, "", 0),
        "find /home -name authorized_keys -type f": (AUTH_KEYS, "", 0),
    })


@pytest.mark.asyncio
async def test_user_collector_filters_system_users(
    collector, mock_user_connection
):
    """Test that system users (UID < 1000) are filtered except root."""
    result = await collector.run(mock_user_connection, LinuxDistro.RHEL)

    assert result.success is True
    usernames = [u["username"] for u in result.data["users"]]
    assert "jdoe" in usernames
    assert "asmith" in usernames
    assert "deploy" in usernames
    assert "root" in usernames  # root is included
    assert "daemon" not in usernames
    assert "sshd" not in usernames


@pytest.mark.asyncio
async def test_user_collector_detects_locked_accounts(
    collector, mock_user_connection
):
    """Test locked account detection from shadow."""
    result = await collector.run(mock_user_connection, LinuxDistro.RHEL)

    users = {u["username"]: u for u in result.data["users"]}
    assert users["asmith"]["account_locked"] is True
    assert users["jdoe"]["account_locked"] is False


@pytest.mark.asyncio
async def test_user_collector_ssh_keys(
    collector, mock_user_connection
):
    """Test SSH authorized keys detection."""
    result = await collector.run(mock_user_connection, LinuxDistro.RHEL)

    users = {u["username"]: u for u in result.data["users"]}
    assert users["jdoe"]["ssh_authorized_keys_present"] is True
    assert users["deploy"]["ssh_authorized_keys_present"] is True
    assert users["asmith"]["ssh_authorized_keys_present"] is False


@pytest.mark.asyncio
async def test_user_collector_secondary_groups(
    collector, mock_user_connection
):
    """Test secondary group membership detection."""
    result = await collector.run(mock_user_connection, LinuxDistro.RHEL)

    users = {u["username"]: u for u in result.data["users"]}
    assert "wheel" in users["jdoe"]["secondary_groups"]
    assert "users" in users["jdoe"]["secondary_groups"]
    assert "docker" in users["deploy"]["secondary_groups"]
