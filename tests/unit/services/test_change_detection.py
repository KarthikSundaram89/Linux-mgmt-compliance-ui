"""
Unit tests for Change Detection Engine.
"""

import pytest

from backend.services.change_detection_service import ChangeDetectionEngine


@pytest.fixture
def engine():
    return ChangeDetectionEngine()


def test_no_changes_on_first_snapshot(engine):
    """First snapshot should produce no changes."""
    changes = engine.detect_changes(
        server_id="srv-1",
        snapshot_id="snap-1",
        current_data={"operating_system": {"kernel_release": "5.15"}},
        previous_data=None,
    )
    assert changes == []


def test_kernel_change_detected(engine):
    """Kernel version change should be detected."""
    changes = engine.detect_changes(
        server_id="srv-1",
        snapshot_id="snap-2",
        current_data={"operating_system": {"kernel_release": "5.16.0", "pretty_name": "RHEL 8"}},
        previous_data={"operating_system": {"kernel_release": "5.15.0", "pretty_name": "RHEL 8"}},
    )
    assert len(changes) == 1
    assert changes[0].category == "operating_system"
    assert changes[0].change_type == "kernel_changed"
    assert changes[0].severity == "warning"


def test_user_added_detected(engine):
    """New user should be detected."""
    changes = engine.detect_changes(
        server_id="srv-1",
        snapshot_id="snap-2",
        current_data={"users": {"users": [
            {"username": "jdoe", "uid": 1001},
            {"username": "newuser", "uid": 1002},
        ]}},
        previous_data={"users": {"users": [
            {"username": "jdoe", "uid": 1001},
        ]}},
    )
    added = [c for c in changes if c.change_type == "added"]
    assert len(added) == 1
    assert added[0].field_name == "newuser"


def test_user_removed_detected(engine):
    """Removed user should be detected."""
    changes = engine.detect_changes(
        server_id="srv-1",
        snapshot_id="snap-2",
        current_data={"users": {"users": [
            {"username": "jdoe", "uid": 1001},
        ]}},
        previous_data={"users": {"users": [
            {"username": "jdoe", "uid": 1001},
            {"username": "gone", "uid": 1002},
        ]}},
    )
    removed = [c for c in changes if c.change_type == "removed"]
    assert len(removed) == 1
    assert removed[0].field_name == "gone"


def test_package_upgrade_detected(engine):
    """Package version change should be an upgrade."""
    changes = engine.detect_changes(
        server_id="srv-1",
        snapshot_id="snap-2",
        current_data={"packages": {"packages": [
            {"name": "openssl", "version": "3.0.8"},
        ]}},
        previous_data={"packages": {"packages": [
            {"name": "openssl", "version": "3.0.7"},
        ]}},
    )
    assert len(changes) == 1
    assert changes[0].change_type == "upgraded"
    assert changes[0].old_value == "3.0.7"
    assert changes[0].new_value == "3.0.8"


def test_service_failed_critical(engine):
    """Service entering failed state is critical."""
    changes = engine.detect_changes(
        server_id="srv-1",
        snapshot_id="snap-2",
        current_data={"services": {"services": [
            {"name": "httpd", "sub_state": "dead", "enabled": "enabled", "is_failed": True},
        ]}},
        previous_data={"services": {"services": [
            {"name": "httpd", "sub_state": "running", "enabled": "enabled", "is_failed": False},
        ]}},
    )
    failed = [c for c in changes if c.change_type == "failed"]
    assert len(failed) == 1
    assert failed[0].severity == "critical"


def test_sudo_granted_warning(engine):
    """New sudo access should generate warning."""
    changes = engine.detect_changes(
        server_id="srv-1",
        snapshot_id="snap-2",
        current_data={"sudo": {"privileged_users": [
            {"username": "jdoe"},
            {"username": "newadmin"},
        ], "nopasswd_entries": []}},
        previous_data={"sudo": {"privileged_users": [
            {"username": "jdoe"},
        ], "nopasswd_entries": []}},
    )
    granted = [c for c in changes if c.change_type == "granted"]
    assert len(granted) == 1
    assert granted[0].field_name == "newadmin"
    assert granted[0].severity == "warning"


def test_change_summary_generation(engine):
    """Test human-readable summary generation."""
    changes = engine.detect_changes(
        server_id="srv-1",
        snapshot_id="snap-2",
        current_data={"operating_system": {"kernel_release": "6.0", "pretty_name": "RHEL 9"}},
        previous_data={"operating_system": {"kernel_release": "5.15", "pretty_name": "RHEL 9"}},
    )
    summary = engine.generate_summary(changes)
    assert "1 change" in summary
    assert "OPERATING_SYSTEM" in summary
    assert "kernel_changed" in summary
