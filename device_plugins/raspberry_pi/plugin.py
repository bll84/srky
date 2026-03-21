"""Raspberry Pi Linux device plugin (SSH-based)."""

from __future__ import annotations

import logging
import time

from core.connection_manager.connection import ConnectionManager
from core.models import (
    DeviceFamily,
    DeviceProfile,
    DiscoveredDevice,
    TestResult,
    TestResultEntry,
)
from device_plugins.base_plugin import DevicePlugin

logger = logging.getLogger(__name__)


class RaspberryPiPlugin(DevicePlugin):
    @property
    def family_name(self) -> str:
        return "Raspberry Pi (Linux)"

    @property
    def supported_families(self) -> list[str]:
        return [DeviceFamily.RASPBERRY_PI_LINUX.value]

    def can_handle(self, device: DiscoveredDevice) -> bool:
        return device.family == DeviceFamily.RASPBERRY_PI_LINUX

    def identify(self, device: DiscoveredDevice, conn_manager: ConnectionManager) -> dict:
        adapter = conn_manager.get_ssh_adapter(device.id)
        if not adapter:
            return {"error": "No SSH connection"}
        info = adapter.get_system_info()
        # Refine confidence if we confirm it's a Pi
        model = info.get("model", "")
        if "raspberry pi" in model.lower():
            device.confidence = 0.95
            device.board_model = model.strip().rstrip("\x00")
        return info

    def get_quick_tests(self, profile: DeviceProfile) -> list[str]:
        return [
            "rpi_ssh_connection",
            "rpi_identity",
            "rpi_system_info",
        ]

    def get_full_tests(self, profile: DeviceProfile) -> list[str]:
        return [
            "rpi_ssh_connection",
            "rpi_identity",
            "rpi_system_info",
            "rpi_cpu_memory",
            "rpi_storage",
            "rpi_temperature",
            "rpi_gpio_check",
            "rpi_i2c_check",
            "rpi_spi_check",
            "rpi_uart_check",
            "rpi_wifi_check",
            "rpi_bluetooth_check",
            "rpi_services",
        ]

    def run_test(
        self,
        test_id: str,
        device: DiscoveredDevice,
        conn_manager: ConnectionManager,
        profile: DeviceProfile,
    ) -> TestResultEntry:
        adapter = conn_manager.get_ssh_adapter(device.id)
        dispatch = {
            "rpi_ssh_connection": self._test_ssh,
            "rpi_identity": self._test_identity,
            "rpi_system_info": self._test_sysinfo,
            "rpi_cpu_memory": self._test_cpu_mem,
            "rpi_storage": self._test_storage,
            "rpi_temperature": self._test_temp,
            "rpi_gpio_check": self._test_gpio,
            "rpi_i2c_check": self._test_i2c,
            "rpi_spi_check": self._test_spi,
            "rpi_uart_check": self._test_uart,
            "rpi_wifi_check": self._test_wifi,
            "rpi_bluetooth_check": self._test_bt,
            "rpi_services": self._test_services,
        }
        handler = dispatch.get(test_id)
        if not handler:
            return TestResultEntry(test_id=test_id, test_name=test_id, result=TestResult.NOT_SUPPORTED)
        start = time.time()
        result = handler(adapter, profile)
        result.duration_seconds = time.time() - start
        result.device_type = device.board_model
        return result

    def _test_ssh(self, adapter, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="rpi_ssh_connection", test_name="SSH Connection",
                                description="Verify SSH connectivity")
        if not adapter:
            entry.result = TestResult.FAIL
            entry.error_detail = "No SSH adapter"
            return entry
        stdout, _, code = adapter.exec("echo ok")
        if code == 0 and "ok" in stdout:
            entry.result = TestResult.PASS
        else:
            entry.result = TestResult.FAIL
        return entry

    def _test_identity(self, adapter, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="rpi_identity", test_name="Device Identity",
                                description="Read Raspberry Pi model and OS info")
        if not adapter:
            entry.result = TestResult.FAIL
            return entry
        info = adapter.get_system_info()
        entry.data = info
        if info.get("model") and info["model"] != "unknown":
            entry.result = TestResult.PASS
            entry.log.append(f"Model: {info['model']}")
            entry.log.append(f"Hostname: {info.get('hostname', 'N/A')}")
            entry.log.append(f"Kernel: {info.get('kernel', 'N/A')}")
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = "Could not read device model"
        return entry

    def _test_sysinfo(self, adapter, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="rpi_system_info", test_name="System Info",
                                description="Collect OS, kernel, uptime info")
        if not adapter:
            entry.result = TestResult.FAIL
            return entry
        info = adapter.get_system_info()
        entry.data = {
            "os": info.get("os", ""),
            "kernel": info.get("kernel", ""),
            "arch": info.get("arch", ""),
            "uptime": info.get("uptime", ""),
        }
        entry.result = TestResult.PASS
        return entry

    def _test_cpu_mem(self, adapter, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="rpi_cpu_memory", test_name="CPU & Memory",
                                description="Check CPU and memory status")
        if not adapter:
            entry.result = TestResult.FAIL
            return entry
        cpu_out, _, _ = adapter.exec("lscpu | grep -E 'Model name|CPU\\(s\\)|MHz'")
        mem_out, _, _ = adapter.exec("free -m | head -3")
        entry.data = {"cpu": cpu_out.strip(), "memory": mem_out.strip()}
        entry.result = TestResult.PASS
        return entry

    def _test_storage(self, adapter, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="rpi_storage", test_name="Storage",
                                description="Check disk usage")
        if not adapter:
            entry.result = TestResult.FAIL
            return entry
        out, _, _ = adapter.exec("df -h / | tail -1")
        entry.data = {"root_disk": out.strip()}
        entry.result = TestResult.PASS
        return entry

    def _test_temp(self, adapter, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="rpi_temperature", test_name="Temperature",
                                description="Read CPU temperature")
        if not adapter:
            entry.result = TestResult.FAIL
            return entry
        out, _, code = adapter.exec("vcgencmd measure_temp 2>/dev/null || cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null")
        if out.strip():
            temp_str = out.strip()
            entry.data = {"temperature": temp_str}
            entry.result = TestResult.PASS
            # Warn if too hot
            try:
                if "temp=" in temp_str:
                    val = float(temp_str.split("=")[1].replace("'C", ""))
                    if val > 80:
                        entry.result = TestResult.WARNING
                        entry.recommendation = "CPU temperature is high!"
            except (ValueError, IndexError):
                pass
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = "Could not read temperature"
        return entry

    def _test_gpio(self, adapter, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="rpi_gpio_check", test_name="GPIO Check",
                                description="Check GPIO subsystem availability")
        if not adapter:
            entry.result = TestResult.FAIL
            return entry
        checks = adapter.check_gpio()
        entry.data = checks
        gpio_avail = checks.get("gpio_available", "no")
        gpiochip = checks.get("gpiochip", "none")
        if "yes" in gpio_avail or gpiochip != "none":
            entry.result = TestResult.PASS
            entry.log.append(f"GPIO available. Chips: {gpiochip}")
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = "GPIO subsystem not detected"
            entry.recommendation = "Check if GPIO is enabled in raspi-config"
        return entry

    def _test_i2c(self, adapter, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="rpi_i2c_check", test_name="I2C Check",
                                description="Check I2C interface status")
        if not adapter:
            entry.result = TestResult.FAIL
            return entry
        out, _, code = adapter.exec("ls /dev/i2c-* 2>/dev/null")
        if out.strip():
            entry.result = TestResult.PASS
            entry.data = {"i2c_devices": out.strip().split()}
            scan_out, _, _ = adapter.exec("i2cdetect -y 1 2>/dev/null | tail -8")
            if scan_out:
                entry.data["i2c_scan"] = scan_out.strip()
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = "I2C not enabled"
            entry.recommendation = "Enable I2C via raspi-config"
        return entry

    def _test_spi(self, adapter, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="rpi_spi_check", test_name="SPI Check",
                                description="Check SPI interface status")
        if not adapter:
            entry.result = TestResult.FAIL
            return entry
        out, _, _ = adapter.exec("ls /dev/spidev* 2>/dev/null")
        if out.strip():
            entry.result = TestResult.PASS
            entry.data = {"spi_devices": out.strip().split()}
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = "SPI not enabled"
            entry.recommendation = "Enable SPI via raspi-config"
        return entry

    def _test_uart(self, adapter, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="rpi_uart_check", test_name="UART Check",
                                description="Check UART interface status")
        if not adapter:
            entry.result = TestResult.FAIL
            return entry
        out, _, _ = adapter.exec("ls /dev/ttyAMA* /dev/ttyS* 2>/dev/null")
        if out.strip():
            entry.result = TestResult.PASS
            entry.data = {"uart_devices": out.strip().split()}
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = "No UART devices found"
        return entry

    def _test_wifi(self, adapter, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="rpi_wifi_check", test_name="Wi-Fi Check",
                                description="Check Wi-Fi status")
        if not adapter:
            entry.result = TestResult.FAIL
            return entry
        out, _, _ = adapter.exec("iwconfig wlan0 2>/dev/null | head -5")
        if out.strip() and "no wireless" not in out.lower():
            entry.result = TestResult.PASS
            entry.data = {"wifi_info": out.strip()}
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = "Wi-Fi not available or not configured"
        return entry

    def _test_bt(self, adapter, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="rpi_bluetooth_check", test_name="Bluetooth Check",
                                description="Check Bluetooth status")
        if not adapter:
            entry.result = TestResult.FAIL
            return entry
        out, _, _ = adapter.exec("hciconfig 2>/dev/null | head -5")
        if out.strip() and "hci0" in out.lower():
            entry.result = TestResult.PASS
            entry.data = {"bluetooth_info": out.strip()}
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = "Bluetooth not detected"
        return entry

    def _test_services(self, adapter, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="rpi_services", test_name="System Services",
                                description="Check key system services")
        if not adapter:
            entry.result = TestResult.FAIL
            return entry
        services = ["ssh", "networking", "bluetooth", "avahi-daemon"]
        results = {}
        for svc in services:
            out, _, code = adapter.exec(f"systemctl is-active {svc} 2>/dev/null")
            results[svc] = out.strip()
        entry.data = {"services": results}
        entry.result = TestResult.PASS
        return entry
