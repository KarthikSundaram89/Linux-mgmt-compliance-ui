# Creating New Collectors - Developer Guide

## Overview

The Linux Inventory Manager uses a plugin-based collector architecture. Each collector is an independent module that connects to a Linux server via SSH, executes predefined commands, and returns structured JSON data.

## Architecture

```
SSH Manager → BaseCollector.run() → collect() → CollectorResult
                                         ↓
                              Snapshot Storage (JSON.gz)
                                         ↓
                              Change Detection Engine
                                         ↓
                              Database (ChangeHistory)
```

## Creating a New Collector

### Step 1: Create the Collector File

Create `backend/collectors/your_collector.py`:

```python
from typing import Any, Dict, FrozenSet
from backend.collectors.base import BaseCollector, LinuxDistro
from backend.ssh.connection import SSHConnection


class YourCollector(BaseCollector):
    """Describe what this collector does."""

    # Required: unique identifier
    name = "your_collector"
    # Required: semantic version
    version = "1.0.0"
    # Required: human description
    description = "Collects XYZ information"
    # Required: which distros are supported
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)

    async def collect(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> Dict[str, Any]:
        """Implement your collection logic here."""
        data = {}

        # Execute commands (MUST be in allowlist)
        result = await self.execute_command(
            connection, "cat /etc/your-file"
        )
        if result.exit_code == 0:
            data["parsed_data"] = self._parse(result.stdout)

        # Use distribution-specific commands
        if distro in (LinuxDistro.RHEL, LinuxDistro.CENTOS):
            result = await self.execute_command(
                connection, "yum-specific-command"
            )
        elif distro in (LinuxDistro.UBUNTU, LinuxDistro.DEBIAN):
            result = await self.execute_command(
                connection, "apt-specific-command"
            )

        return data

    def _parse(self, content: str) -> list:
        """Parse raw output into structured data."""
        # Your parsing logic here
        return []
```

### Step 2: Add Commands to Allowlist

**CRITICAL:** Every command your collector executes MUST be added to `COMMAND_ALLOWLIST` or `PARAMETERIZED_COMMAND_PREFIXES` in `backend/collectors/base.py`.

```python
# In COMMAND_ALLOWLIST (for exact commands):
"cat /etc/your-file",
"your-exact-command",

# In PARAMETERIZED_COMMAND_PREFIXES (for commands with arguments):
"your-command --option ",
```

Commands NOT in the allowlist will raise `SecurityError` and the collection will fail.

### Step 3: Register the Collector

Add to `backend/collectors/registry.py` in the `register_all_collectors()` function:

```python
from backend.collectors.your_collector import YourCollector
collector_registry.register(YourCollector)
```

### Step 4: Write Unit Tests

Create `tests/unit/collectors/test_your_collector.py`:

```python
import pytest
from backend.collectors.your_collector import YourCollector
from backend.collectors.base import LinuxDistro


@pytest.fixture
def collector():
    return YourCollector()


@pytest.mark.asyncio
async def test_basic_collection(collector, mock_connection):
    conn = mock_connection({
        "cat /etc/your-file": ("expected output", "", 0),
    })
    result = await collector.run(conn, LinuxDistro.RHEL)
    assert result.success is True
    assert "parsed_data" in result.data
```

## Collector Rules

1. **Independence**: No collector may depend on another collector's output
2. **No Database Access**: Collectors return data; they never write to DB
3. **Command Allowlist**: Only allowlisted commands may be executed
4. **Error Isolation**: One collector's failure must not stop others
5. **Structured Output**: Always return JSON-serializable dictionaries
6. **Distribution Aware**: Use `distro` parameter for OS-specific commands
7. **Graceful Degradation**: Handle missing commands/files gracefully
8. **Warnings**: Use `self.add_warning()` for non-fatal issues
9. **Timeout Safe**: Long commands should use explicit timeouts
10. **No Secrets**: Never collect or return sensitive data (keys, passwords)

## Collector Result Structure

```python
@dataclass
class CollectorResult:
    collector_name: str      # e.g., "packages"
    collector_version: str   # e.g., "1.0.0"
    success: bool            # True if collection completed
    data: Dict[str, Any]     # The collected structured data
    warnings: List[str]      # Non-fatal issues
    errors: List[str]        # Fatal errors (if success=False)
    commands_run: int         # SSH commands executed
    duration_seconds: float  # Total wall-clock time
    metadata: Dict[str, Any] # Collector metadata
```

## Change Detection Integration

When your collector's data changes between snapshots, the `ChangeDetectionEngine` automatically detects it. For custom change detection logic:

1. Add your category to `SEVERITY_MAP` in `change_detection_service.py`
2. Add a `_detect_your_category_changes()` method
3. Register it in the `detectors` dict inside `detect_changes()`

## Testing Without SSH

Use the `MockSSHConnection` in `tests/conftest.py`:

```python
conn = mock_connection({
    "command": ("stdout", "stderr", exit_code),
})
```

## Enabling/Disabling Collectors

```python
from backend.collectors.registry import collector_registry

# Disable a collector
collector_registry.disable("your_collector")

# Re-enable
collector_registry.enable("your_collector")

# Check status
collector_registry.is_enabled("your_collector")
```

## Best Practices

- Keep collectors focused: one domain per collector
- Parse output defensively (handle missing fields, empty output)
- Log at DEBUG level for command execution, INFO for completion
- Include counts and summaries in output (total_count, etc.)
- Use `self.add_warning()` when data looks unusual
- Test with multiple distributions
- Document the commands used and what they return
