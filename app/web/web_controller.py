"""Web controller - bridges Flask routes to AppController (without Qt dependency)."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable

from core.connection_manager.connection import ConnectionManager
from core.device_discovery.scanner import DeviceScanner
from core.models import (
    ConnectionType,
    DeviceFamily,
    DeviceProfile,
    DiscoveredDevice,
    SSHCredentials,
    TestReport,
    TestResult,
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


class WebController:
    """Non-Qt controller for the web interface."""

    def __init__(self) -> None:
        self.scanner = DeviceScanner()
        self.conn_manager = ConnectionManager()
        self.profile_registry = ProfileRegistry()
        self.plugin_registry = PluginRegistry()
        self.test_engine = TestEngine(self.plugin_registry, self.conn_manager)

        self._devices: list[DiscoveredDevice] = []
        self._selected_device_id: str = ""
        self._last_report: TestReport | None = None
        self._ssh_credentials: dict[str, SSHCredentials] = {}

        self._status: str = "Hazır"
        self._test_progress: dict[str, Any] = {"running": False, "test_id": "", "current": 0, "total": 0, "pct": 0}

        self._register_profiles()
        self._register_plugins()

    def _register_profiles(self) -> None:
        register_builtin_profiles(self.profile_registry)

    def _register_plugins(self) -> None:
        self.plugin_registry.register(ESP32Plugin())
        self.plugin_registry.register(ArduinoPlugin())
        self.plugin_registry.register(PicoPlugin())
        self.plugin_registry.register(RaspberryPiPlugin())
        self.plugin_registry.register(GenericSerialPlugin())

    # ── Status ──

    def get_status(self) -> str:
        return self._status

    # ── Device Discovery ──

    def scan_devices(self, ssh_hosts: list[str] | None = None) -> list[dict]:
        self._status = "Cihazlar taranıyor..."
        devices = self.scanner.scan_all(
            ssh_hosts=ssh_hosts,
            progress_callback=lambda msg: setattr(self, "_status", msg),
        )
        for dev in devices:
            profile = self.profile_registry.get_for_device(dev)
            if profile:
                dev.profile = profile
        self._devices = devices
        self._status = f"{len(devices)} cihaz bulundu"
        return self._devices_to_dicts()

    def add_ssh_device(self, host: str, username: str = "pi", password: str = "") -> list[dict]:
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
        self._status = f"SSH hedefi eklendi: {host}"
        return self._devices_to_dicts()

    def get_devices(self) -> list[dict]:
        return self._devices_to_dicts()

    def _devices_to_dicts(self) -> list[dict]:
        result = []
        for dev in self._devices:
            result.append({
                "id": dev.id,
                "board_model": dev.board_model,
                "family": dev.family.value,
                "port": dev.port,
                "ip_address": dev.ip_address,
                "connection_type": dev.connection_type.value,
                "confidence": dev.confidence,
                "vid": dev.vid,
                "pid": dev.pid,
                "manufacturer": dev.manufacturer,
                "serial_number": dev.serial_number,
                "is_connected": dev.is_connected,
                "address": dev.port or dev.ip_address,
            })
        return result

    # ── Device Selection & Details ──

    def select_device(self, device_id: str) -> dict | None:
        self._selected_device_id = device_id
        return self.get_device_detail(device_id)

    def get_device_detail(self, device_id: str) -> dict | None:
        device = self._find_device(device_id)
        if not device:
            return None

        profile = self._get_profile(device)
        detail: dict[str, Any] = {
            "id": device.id,
            "board_model": device.board_model,
            "family": device.family.value,
            "port": device.port or device.ip_address,
            "connection_type": device.connection_type.value,
            "confidence": device.confidence,
            "vid": f"0x{device.vid:04X}" if device.vid else "Yok",
            "pid": f"0x{device.pid:04X}" if device.pid else "Yok",
            "manufacturer": device.manufacturer or "Bilinmiyor",
            "serial_number": device.serial_number or "Yok",
            "is_connected": device.is_connected,
        }

        if profile:
            features = []
            if profile.wifi:
                features.append("Wi-Fi")
            if profile.bluetooth:
                features.append("Bluetooth")
            if profile.dac_pins:
                features.append("DAC")
            detail.update({
                "mcu": profile.mcu,
                "flash": f"{profile.flash_size_mb} MB" if profile.flash_size_mb else "Yok",
                "ram": f"{profile.ram_kb} KB" if profile.ram_kb else "Yok",
                "psram": profile.psram,
                "features": features,
                "supported_tests": profile.supported_tests,
                "notes": profile.notes,
                "pin_count": len(profile.pins),
            })
        else:
            detail.update({
                "mcu": "Bilinmiyor", "flash": "Yok", "ram": "Yok",
                "psram": False, "features": [], "supported_tests": [],
                "notes": "Bu cihaz için profil yüklenmedi", "pin_count": 0,
            })

        return detail

    # ── Pin Matrix ──

    def get_pin_matrix(self, device_id: str) -> list[dict]:
        device = self._find_device(device_id)
        if not device:
            return []
        profile = self._get_profile(device)
        if not profile:
            return []

        from core.models import PinStatus
        pins = sorted(profile.pins, key=lambda p: p.number)
        result = []
        for pin in pins:
            status = pin.status
            if pin.is_reserved:
                status = PinStatus.RESERVED
            elif pin.is_unsafe:
                status = PinStatus.WARNING
            result.append({
                "number": pin.number,
                "name": pin.name,
                "gpio": pin.gpio_number,
                "functions": [f.value for f in pin.functions],
                "voltage": pin.voltage_level,
                "status": status.value,
                "notes": pin.notes,
                "is_reserved": pin.is_reserved,
                "is_boot_pin": pin.is_boot_pin,
            })
        return result

    # ── Connection ──

    def connect_device(self, device_id: str) -> dict:
        device = self._find_device(device_id)
        if not device:
            return {"success": False, "message": "Cihaz bulunamadı"}

        if device.connection_type == ConnectionType.SSH:
            creds = self._ssh_credentials.get(device.id)
            if not creds:
                creds = SSHCredentials(host=device.ip_address)
            success = self.conn_manager.connect_ssh(device, creds)
        else:
            success = self.conn_manager.connect_serial(device)

        if success:
            device.is_connected = True
            plugin = self.plugin_registry.get_plugin_for(device)
            if plugin:
                plugin.identify(device, self.conn_manager)
            self._status = f"Bağlandı: {device.board_model}"
            return {"success": True, "message": f"Bağlandı: {device.board_model}"}
        else:
            self._status = f"Bağlantı başarısız: {device.board_model}"
            return {"success": False, "message": f"Bağlantı başarısız: {device.board_model}"}

    def is_connected(self, device_id: str) -> bool:
        return self.conn_manager.is_connected(device_id)

    # ── Testing ──

    def run_tests(self, device_id: str, mode: str = "quick") -> None:
        """Run tests in a background thread."""
        self._test_progress = {"running": True, "test_id": "", "current": 0, "total": 0, "pct": 0}
        thread = threading.Thread(target=self._run_tests_worker, args=(device_id, mode), daemon=True)
        thread.start()

    def _run_tests_worker(self, device_id: str, mode: str) -> None:
        device = self._find_device(device_id)
        if not device:
            self._test_progress["running"] = False
            return

        profile = self._get_profile(device)
        if not profile:
            self._status = "Cihaz için profil bulunamadı"
            self._test_progress["running"] = False
            return

        def progress_cb(test_id: str, current: int, total: int) -> None:
            pct = int((current / total) * 100) if total > 0 else 0
            self._test_progress.update({"test_id": test_id, "current": current, "total": total, "pct": pct})
            self._status = f"Çalışıyor: {test_id} ({current}/{total})"

        if mode == "full":
            report = self.test_engine.run_full_test(device, profile, progress_cb)
        else:
            report = self.test_engine.run_quick_test(device, profile, progress_cb)

        self._last_report = report
        self._test_progress = {"running": False, "test_id": "", "current": 0, "total": 0, "pct": 100}
        self._status = "Tamamlandı"

    def get_test_progress(self) -> dict:
        return self._test_progress

    def stop_tests(self) -> None:
        self.test_engine.stop()
        self._test_progress["running"] = False
        self._status = "Durduruldu"

    # ── Reports ──

    def get_report(self, fmt: str = "text") -> dict | None:
        if not self._last_report:
            return None
        report = self._last_report
        if fmt == "json":
            content = ReportEngine.to_json(report)
        elif fmt == "csv":
            content = ReportEngine.to_csv(report)
        else:
            content = ReportEngine.to_text(report)
        return {
            "content": content,
            "format": fmt,
            "summary": {
                "board_model": report.board_model,
                "total": report.total_tests,
                "passed": report.passed,
                "failed": report.failed,
                "warnings": report.warnings,
                "skipped": report.skipped,
            },
        }

    def export_report(self, fmt: str, filepath: str) -> None:
        if not self._last_report:
            return
        if fmt == "json":
            ReportEngine.save_json(self._last_report, filepath)
        elif fmt == "csv":
            ReportEngine.save_csv(self._last_report, filepath)
        else:
            ReportEngine.save_text(self._last_report, filepath)

    # ── Helpers ──

    def _find_device(self, device_id: str) -> DiscoveredDevice | None:
        for dev in self._devices:
            if dev.id == device_id:
                return dev
        return None

    def _get_profile(self, device: DiscoveredDevice) -> DeviceProfile | None:
        if device.profile:
            return device.profile
        return self.profile_registry.get_for_device(device)

    def shutdown(self) -> None:
        self.scanner.stop()
        self.test_engine.stop()
        self.conn_manager.disconnect_all()
