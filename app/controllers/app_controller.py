"""Main application controller - orchestrates all subsystems."""

from __future__ import annotations

import logging
from typing import Callable

from PySide6.QtCore import QObject, Signal

from core.connection_manager.connection import ConnectionManager
from core.device_discovery.scanner import DeviceScanner
from core.models import (
    ConnectionType,
    DeviceFamily,
    DeviceProfile,
    DiscoveredDevice,
    SSHCredentials,
    TestReport,
)
from core.profiles.builtin_profiles import register_builtin_profiles
from core.profiles.profile_registry import ProfileRegistry
from core.report_engine.reporter import ReportEngine
from core.test_engine.engine import TestEngine
from device_plugins.arduino.plugin import ArduinoPlugin
from device_plugins.base_plugin import PluginRegistry
from device_plugins.esp32.plugin import ESP32Plugin
from device_plugins.generic_serial.plugin import GenericSerialPlugin
from device_plugins.pico.plugin import PicoPlugin
from device_plugins.raspberry_pi.plugin import RaspberryPiPlugin

logger = logging.getLogger(__name__)


class AppController(QObject):
    """Central controller that ties discovery, connection, testing, and UI together."""

    # Signals
    status_changed = Signal(str)
    devices_updated = Signal()
    device_selected = Signal(str)
    report_ready = Signal()

    def __init__(self) -> None:
        super().__init__()

        # Core subsystems
        self.scanner = DeviceScanner()
        self.conn_manager = ConnectionManager()
        self.profile_registry = ProfileRegistry()
        self.plugin_registry = PluginRegistry()
        self.test_engine = TestEngine(self.plugin_registry, self.conn_manager)

        # State
        self._devices: list[DiscoveredDevice] = []
        self._selected_device_id: str = ""
        self._last_report: TestReport | None = None
        self._ssh_credentials: dict[str, SSHCredentials] = {}

        # Initialize
        self._register_profiles()
        self._register_plugins()

    def _register_profiles(self) -> None:
        register_builtin_profiles(self.profile_registry)
        logger.info("Registered %d device profiles", len(self.profile_registry.list_profiles()))

    def _register_plugins(self) -> None:
        self.plugin_registry.register(ESP32Plugin())
        self.plugin_registry.register(ArduinoPlugin())
        self.plugin_registry.register(PicoPlugin())
        self.plugin_registry.register(RaspberryPiPlugin())
        self.plugin_registry.register(GenericSerialPlugin())
        logger.info("Registered %d device plugins", len(self.plugin_registry.list_plugins()))

    # ── Device Discovery ──

    def scan_devices(self, ssh_hosts: list[str] | None = None) -> None:
        """Scan for all connected devices."""
        self.status_changed.emit("Cihazlar taranıyor...")

        def progress(msg: str) -> None:
            self.status_changed.emit(msg)

        devices = self.scanner.scan_all(
            ssh_hosts=ssh_hosts,
            progress_callback=progress,
        )

        # Assign profiles
        for dev in devices:
            profile = self.profile_registry.get_for_device(dev)
            if profile:
                dev.profile = profile

        self._devices = devices
        self.devices_updated.emit()
        self.status_changed.emit(f"{len(devices)} cihaz bulundu")

    def add_ssh_device(self, host: str, username: str = "pi", password: str = "") -> None:
        """Manually add an SSH device (Raspberry Pi Linux)."""
        creds = SSHCredentials(host=host, username=username, password=password)
        device = DiscoveredDevice(
            ip_address=host,
            family=DeviceFamily.RASPBERRY_PI_LINUX,
            board_model="Raspberry Pi (SSH)",
            connection_type=ConnectionType.SSH,
            confidence=0.70,
            description=f"Elle eklenen SSH hedefi: {host}",
        )
        profile = self.profile_registry.get("raspberry_pi_linux")
        if profile:
            device.profile = profile

        self._ssh_credentials[device.id] = creds
        self._devices.append(device)
        self.devices_updated.emit()
        self.status_changed.emit(f"SSH hedefi eklendi: {host}")

    def get_devices(self) -> list[DiscoveredDevice]:
        return self._devices

    def get_device(self, device_id: str) -> DiscoveredDevice | None:
        for dev in self._devices:
            if dev.id == device_id:
                return dev
        return None

    # ── Device Selection ──

    def select_device(self, device_id: str) -> None:
        self._selected_device_id = device_id
        device = self.get_device(device_id)
        if device:
            self.status_changed.emit(f"Seçildi: {device.board_model}")
            self.device_selected.emit(device_id)

    def get_selected_device_id(self) -> str:
        return self._selected_device_id

    # ── Connection ──

    def connect_selected_device(self) -> bool:
        """Connect to the currently selected device."""
        device = self.get_device(self._selected_device_id)
        if not device:
            self.status_changed.emit("Cihaz seçilmedi")
            return False

        if device.connection_type == ConnectionType.SSH:
            creds = self._ssh_credentials.get(device.id)
            if not creds:
                creds = SSHCredentials(host=device.ip_address)
            success = self.conn_manager.connect_ssh(device, creds)
        else:
            success = self.conn_manager.connect_serial(device)

        if success:
            device.is_connected = True
            self.status_changed.emit(f"Bağlandı: {device.board_model}")

            # Try to identify via plugin
            plugin = self.plugin_registry.get_plugin_for(device)
            if plugin:
                info = plugin.identify(device, self.conn_manager)
                if info and "error" not in info:
                    logger.info("Device identified: %s", info)

            self.device_selected.emit(device.id)
        else:
            self.status_changed.emit(f"Bağlantı başarısız: {device.board_model}")

        return success

    def is_connected(self, device_id: str) -> bool:
        return self.conn_manager.is_connected(device_id)

    # ── Profiles ──

    def get_profile(self, device_id: str) -> DeviceProfile | None:
        device = self.get_device(device_id)
        if not device:
            return None
        if device.profile:
            return device.profile
        return self.profile_registry.get_for_device(device)

    # ── Testing ──

    def run_tests(
        self,
        device_id: str,
        mode: str = "quick",
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> TestReport | None:
        """Run tests on a device. Called from worker thread."""
        device = self.get_device(device_id)
        if not device:
            return None

        profile = self.get_profile(device_id)
        if not profile:
            self.status_changed.emit("Cihaz için profil bulunamadı")
            return None

        if mode == "full":
            report = self.test_engine.run_full_test(device, profile, progress_callback)
        else:
            report = self.test_engine.run_quick_test(device, profile, progress_callback)

        self._last_report = report
        return report

    def stop_tests(self) -> None:
        self.test_engine.stop()

    def set_last_report(self, report: TestReport) -> None:
        self._last_report = report
        self.report_ready.emit()

    def get_last_report(self) -> TestReport | None:
        return self._last_report

    # ── Lifecycle ──

    def shutdown(self) -> None:
        """Clean shutdown."""
        self.scanner.stop()
        self.test_engine.stop()
        self.conn_manager.disconnect_all()
        logger.info("Application shutdown complete")
