"""
Change Detection Service
========================

Compares consecutive inventory snapshots and identifies changes.
Only detected differences are stored in the change history.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.models.change_history import ChangeHistory
from backend.models.base import generate_uuid

logger = logging.getLogger("collector")


# Change severity rules by category
SEVERITY_RULES = {
    "user": {
        "added": "warning",
        "removed": "warning",
        "modified": "info",
    },
    "package": {
        "added": "info",
        "removed": "warning",
        "modified": "info",
    },
    "service": {
        "added": "info",
        "removed": "warning",
        "modified": "warning",
    },
    "kernel": {
        "modified": "warning",
    },
    "filesystem": {
        "added": "info",
        "removed": "critical",
        "modified": "warning",
    },
    "password_policy": {
        "modified": "critical",
    },
    "network": {
        "added": "info",
        "removed": "warning",
        "modified": "warning",
    },
    "chrony": {
        "modified": "warning",
    },
}


class ChangeDetectionService:
    """
    Detects and records changes between inventory snapshots.
    
    Compares the latest snapshot with the previous one for each
    server and generates ChangeHistory records for all detected
    differences.
    
    Change types:
    - added: New item that wasn't in previous snapshot
    - removed: Item that was in previous but not in current
    - modified: Item exists in both but values differ
    """
    
    def detect_changes(
        self,
        server_id: str,
        snapshot_id: str,
        current_data: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]],
    ) -> List[ChangeHistory]:
        """
        Compare two snapshots and return detected changes.
        
        Args:
            server_id: The server's unique identifier.
            snapshot_id: The current snapshot's ID.
            current_data: Current inventory data.
            previous_data: Previous inventory data (None if first).
        
        Returns:
            List of ChangeHistory objects (not yet persisted).
        """
        if previous_data is None:
            # First collection, no changes to detect
            logger.info(
                "First snapshot for server, no previous data",
                extra={"server_id": server_id},
            )
            return []
        
        changes: List[ChangeHistory] = []
        now = datetime.now(timezone.utc)
        
        # Compare each category present in data
        for category in current_data:
            if category.startswith("_"):
                continue  # Skip metadata fields
            
            current_section = current_data.get(category, {})
            previous_section = previous_data.get(category, {})
            
            category_changes = self._compare_sections(
                server_id=server_id,
                snapshot_id=snapshot_id,
                category=category,
                current=current_section,
                previous=previous_section,
                detected_at=now,
            )
            changes.extend(category_changes)
        
        # Check for removed categories
        for category in previous_data:
            if category.startswith("_"):
                continue
            if category not in current_data:
                changes.append(
                    self._create_change(
                        server_id=server_id,
                        snapshot_id=snapshot_id,
                        category=category,
                        change_type="removed",
                        field_name=f"{category} (entire section)",
                        old_value=str(previous_data[category])[:500],
                        new_value=None,
                        detected_at=now,
                    )
                )
        
        if changes:
            logger.info(
                f"Detected {len(changes)} changes",
                extra={
                    "server_id": server_id,
                    "change_count": len(changes),
                },
            )
        
        return changes
    
    def _compare_sections(
        self,
        server_id: str,
        snapshot_id: str,
        category: str,
        current: Any,
        previous: Any,
        detected_at: datetime,
    ) -> List[ChangeHistory]:
        """Compare two sections of inventory data."""
        changes = []
        
        if isinstance(current, dict) and isinstance(previous, dict):
            changes.extend(
                self._compare_dicts(
                    server_id, snapshot_id, category,
                    current, previous, detected_at,
                )
            )
        elif isinstance(current, list) and isinstance(previous, list):
            changes.extend(
                self._compare_lists(
                    server_id, snapshot_id, category,
                    current, previous, detected_at,
                )
            )
        elif current != previous:
            changes.append(
                self._create_change(
                    server_id=server_id,
                    snapshot_id=snapshot_id,
                    category=category,
                    change_type="modified",
                    field_name=category,
                    old_value=str(previous)[:500],
                    new_value=str(current)[:500],
                    detected_at=detected_at,
                )
            )
        
        return changes
    
    def _compare_dicts(
        self,
        server_id: str,
        snapshot_id: str,
        category: str,
        current: Dict,
        previous: Dict,
        detected_at: datetime,
    ) -> List[ChangeHistory]:
        """Compare two dictionaries and detect changes."""
        changes = []
        
        # Added keys
        for key in set(current) - set(previous):
            changes.append(
                self._create_change(
                    server_id=server_id,
                    snapshot_id=snapshot_id,
                    category=category,
                    change_type="added",
                    field_name=str(key),
                    old_value=None,
                    new_value=str(current[key])[:500],
                    detected_at=detected_at,
                )
            )
        
        # Removed keys
        for key in set(previous) - set(current):
            changes.append(
                self._create_change(
                    server_id=server_id,
                    snapshot_id=snapshot_id,
                    category=category,
                    change_type="removed",
                    field_name=str(key),
                    old_value=str(previous[key])[:500],
                    new_value=None,
                    detected_at=detected_at,
                )
            )
        
        # Modified keys
        for key in set(current) & set(previous):
            if current[key] != previous[key]:
                changes.append(
                    self._create_change(
                        server_id=server_id,
                        snapshot_id=snapshot_id,
                        category=category,
                        change_type="modified",
                        field_name=str(key),
                        old_value=str(previous[key])[:500],
                        new_value=str(current[key])[:500],
                        detected_at=detected_at,
                    )
                )
        
        return changes
    
    def _compare_lists(
        self,
        server_id: str,
        snapshot_id: str,
        category: str,
        current: List,
        previous: List,
        detected_at: datetime,
    ) -> List[ChangeHistory]:
        """Compare two lists and detect additions/removals."""
        changes = []
        
        current_set = set(str(item) for item in current)
        previous_set = set(str(item) for item in previous)
        
        for item in current_set - previous_set:
            changes.append(
                self._create_change(
                    server_id=server_id,
                    snapshot_id=snapshot_id,
                    category=category,
                    change_type="added",
                    field_name=item[:200],
                    old_value=None,
                    new_value=item[:500],
                    detected_at=detected_at,
                )
            )
        
        for item in previous_set - current_set:
            changes.append(
                self._create_change(
                    server_id=server_id,
                    snapshot_id=snapshot_id,
                    category=category,
                    change_type="removed",
                    field_name=item[:200],
                    old_value=item[:500],
                    new_value=None,
                    detected_at=detected_at,
                )
            )
        
        return changes
    
    def _create_change(
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
        severity = self._determine_severity(category, change_type)
        
        return ChangeHistory(
            id=generate_uuid(),
            server_id=server_id,
            snapshot_id=snapshot_id,
            category=category,
            change_type=change_type,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            severity=severity,
            detected_at=detected_at,
        )
    
    def _determine_severity(
        self, category: str, change_type: str
    ) -> str:
        """Determine change severity based on category and type."""
        category_rules = SEVERITY_RULES.get(category, {})
        return category_rules.get(change_type, "info")
