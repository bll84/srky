"""Base plugin interface for device support."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection_manager.connection import ConnectionManager
    from core.models import DeviceProfile, DiscoveredDevice, TestResultEntry


class DevicePlugin(ABC):
    """Abstract base class for device plugins.

    Each device family implements this to provide:
    - Detection rules
    - Identification logic
    - Test suites
    - Command protocol adaptation
    """

    @property
    @abstractmethod
    def family_name(self) -> str:
        """Human-readable family name."""

    @property
    @abstractmethod
    def supported_families(self) -> list[str]:
        """List of DeviceFamily values this plugin handles."""

    @abstractmethod
    def can_handle(self, device: DiscoveredDevice) -> bool:
        """Check if this plugin can handle the given device."""

    @abstractmethod
    def identify(
        self,
        device: DiscoveredDevice,
        conn_manager: ConnectionManager,
    ) -> dict:
        """Attempt to identify the device and return info dict."""

    @abstractmethod
    def get_quick_tests(self, profile: DeviceProfile) -> list[str]:
        """Return list of test IDs for quick test mode."""

    @abstractmethod
    def get_full_tests(self, profile: DeviceProfile) -> list[str]:
        """Return list of test IDs for full test mode."""

    @abstractmethod
    def run_test(
        self,
        test_id: str,
        device: DiscoveredDevice,
        conn_manager: ConnectionManager,
        profile: DeviceProfile,
    ) -> TestResultEntry:
        """Run a specific test and return the result."""


class PluginRegistry:
    """Registry for device plugins."""

    def __init__(self) -> None:
        self._plugins: list[DevicePlugin] = []

    def register(self, plugin: DevicePlugin) -> None:
        self._plugins.append(plugin)

    def get_plugin_for(self, device: DiscoveredDevice) -> DevicePlugin | None:
        for plugin in self._plugins:
            if plugin.can_handle(device):
                return plugin
        return None

    def list_plugins(self) -> list[str]:
        return [p.family_name for p in self._plugins]
