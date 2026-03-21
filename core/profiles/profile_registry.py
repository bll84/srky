"""Device profile registry and loader."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core.models import DeviceFamily, DeviceProfile

if TYPE_CHECKING:
    from core.models import DiscoveredDevice

logger = logging.getLogger(__name__)


class ProfileRegistry:
    """Central registry for device profiles."""

    def __init__(self) -> None:
        self._profiles: dict[str, DeviceProfile] = {}

    def register(self, key: str, profile: DeviceProfile) -> None:
        self._profiles[key] = profile
        logger.debug("Registered profile: %s", key)

    def get(self, key: str) -> DeviceProfile | None:
        return self._profiles.get(key)

    def get_for_device(self, device: DiscoveredDevice) -> DeviceProfile | None:
        """Find the best matching profile for a discovered device."""
        # Try exact model match
        model_key = device.board_model.lower().replace(" ", "_")
        if model_key in self._profiles:
            return self._profiles[model_key]

        # Try family match
        family_key = f"generic_{device.family.value}"
        if family_key in self._profiles:
            return self._profiles[family_key]

        # Try VID/PID match
        for key, profile in self._profiles.items():
            if device.vid and device.vid in profile.usb_vid:
                if device.pid and device.pid in profile.usb_pid:
                    return profile

        return self._profiles.get("generic_serial")

    def list_profiles(self) -> list[str]:
        return list(self._profiles.keys())

    def list_by_family(self, family: DeviceFamily) -> list[str]:
        return [k for k, p in self._profiles.items() if p.family == family]
