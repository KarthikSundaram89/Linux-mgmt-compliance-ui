"""
Collector Registry
==================

Plugin registry that discovers, registers, and manages collectors.
Supports enabling/disabling collectors via configuration.
"""

import logging
from typing import Dict, List, Optional, Type

from backend.collectors.base import BaseCollector, LinuxDistro

logger = logging.getLogger("collector")


class CollectorRegistry:
    """
    Central registry for all inventory collectors.

    Acts as a plugin manager:
    - Discovers and registers collector classes
    - Enables/disables collectors via configuration
    - Provides collectors filtered by distribution support
    - Ensures collector independence (no ordering dependencies)
    """

    def __init__(self):
        self._collectors: Dict[str, Type[BaseCollector]] = {}
        self._disabled: set = set()

    def register(self, collector_class: Type[BaseCollector]) -> None:
        """
        Register a collector class.

        Args:
            collector_class: The collector class to register.
        """
        name = collector_class.name
        if name in self._collectors:
            logger.warning(f"Collector '{name}' already registered, overwriting")
        self._collectors[name] = collector_class
        logger.debug(f"Registered collector: {name} v{collector_class.version}")

    def unregister(self, name: str) -> None:
        """Remove a collector from the registry."""
        self._collectors.pop(name, None)

    def disable(self, name: str) -> None:
        """Disable a collector by name."""
        self._disabled.add(name)
        logger.info(f"Collector disabled: {name}")

    def enable(self, name: str) -> None:
        """Enable a previously disabled collector."""
        self._disabled.discard(name)
        logger.info(f"Collector enabled: {name}")

    def is_enabled(self, name: str) -> bool:
        """Check if a collector is enabled."""
        return name in self._collectors and name not in self._disabled

    def get_collector(self, name: str) -> Optional[BaseCollector]:
        """
        Get an instantiated collector by name.

        Returns None if not found or disabled.
        """
        if name not in self._collectors or name in self._disabled:
            return None
        return self._collectors[name]()

    def get_all_collectors(
        self,
        distro: LinuxDistro = LinuxDistro.UNKNOWN,
    ) -> List[BaseCollector]:
        """
        Get all enabled collectors, optionally filtered by distro.

        Args:
            distro: Only return collectors supporting this distro.

        Returns:
            List of instantiated collector objects.
        """
        collectors = []
        for name, cls in self._collectors.items():
            if name in self._disabled:
                continue
            if distro != LinuxDistro.UNKNOWN:
                if distro not in cls.supported_distros:
                    continue
            collectors.append(cls())
        return collectors

    def list_registered(self) -> List[Dict[str, str]]:
        """List all registered collectors with their metadata."""
        result = []
        for name, cls in self._collectors.items():
            result.append({
                "name": name,
                "version": cls.version,
                "description": cls.description,
                "enabled": name not in self._disabled,
                "supported_distros": [
                    d.value for d in cls.supported_distros
                ],
            })
        return result

    @property
    def count(self) -> int:
        """Total number of registered collectors."""
        return len(self._collectors)

    @property
    def enabled_count(self) -> int:
        """Number of enabled collectors."""
        return len(self._collectors) - len(
            self._disabled & set(self._collectors.keys())
        )


# Global registry instance
collector_registry = CollectorRegistry()


def register_all_collectors() -> None:
    """
    Register all built-in collectors.

    Called during application startup to populate the registry.
    """
    from backend.collectors.operating_system import OperatingSystemCollector
    from backend.collectors.users import UserCollector
    from backend.collectors.groups import GroupCollector
    from backend.collectors.sudo import SudoCollector
    from backend.collectors.password_policy import PasswordPolicyCollector
    from backend.collectors.filesystem import FilesystemCollector
    from backend.collectors.packages import PackageCollector
    from backend.collectors.services import ServiceCollector
    from backend.collectors.chrony import ChronyCollector
    from backend.collectors.network import NetworkCollector
    from backend.collectors.ssh_config import SSHConfigCollector
    from backend.collectors.cron import CronCollector

    collector_registry.register(OperatingSystemCollector)
    collector_registry.register(UserCollector)
    collector_registry.register(GroupCollector)
    collector_registry.register(SudoCollector)
    collector_registry.register(PasswordPolicyCollector)
    collector_registry.register(FilesystemCollector)
    collector_registry.register(PackageCollector)
    collector_registry.register(ServiceCollector)
    collector_registry.register(ChronyCollector)
    collector_registry.register(NetworkCollector)
    collector_registry.register(SSHConfigCollector)
    collector_registry.register(CronCollector)

    logger.info(
        f"Registered {collector_registry.count} collectors"
    )
