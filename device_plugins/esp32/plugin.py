"""ESP32 device plugin."""

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


class ESP32Plugin(DevicePlugin):
    @property
    def family_name(self) -> str:
        return "ESP32"

    @property
    def supported_families(self) -> list[str]:
        return [DeviceFamily.ESP32.value]

    def can_handle(self, device: DiscoveredDevice) -> bool:
        return device.family == DeviceFamily.ESP32

    def identify(self, device: DiscoveredDevice, conn_manager: ConnectionManager) -> dict:
        proto = conn_manager.get_protocol(device.id)
        if not proto:
            return {"error": "No protocol connection"}

        info = proto.get_info()
        if info and info.get("status") == "ok":
            return info.get("data", {})

        # Try HELLO as fallback
        hello = proto.hello()
        if hello and hello.get("status") == "ok":
            return hello.get("data", {"agent": "esp32", "status": "responsive"})

        return {"error": "Device not responding to agent commands"}

    def get_quick_tests(self, profile: DeviceProfile) -> list[str]:
        return [
            "esp32_connection",
            "esp32_identity",
            "esp32_wifi_scan",
            "esp32_memory",
        ]

    def get_full_tests(self, profile: DeviceProfile) -> list[str]:
        tests = [
            "esp32_connection",
            "esp32_identity",
            "esp32_memory",
            "esp32_wifi_scan",
            "esp32_ble_init",
            "esp32_i2c_scan",
            "esp32_spi_init",
            "esp32_adc_test",
            "esp32_pwm_test",
            "esp32_gpio_test",
            "esp32_uart_test",
            "esp32_flash_info",
        ]
        if profile.dac_pins:
            tests.append("esp32_dac_test")
        if profile.psram:
            tests.append("esp32_psram_test")
        return tests

    def run_test(
        self,
        test_id: str,
        device: DiscoveredDevice,
        conn_manager: ConnectionManager,
        profile: DeviceProfile,
    ) -> TestResultEntry:
        proto = conn_manager.get_protocol(device.id)
        dispatch = {
            "esp32_connection": self._test_connection,
            "esp32_identity": self._test_identity,
            "esp32_memory": self._test_memory,
            "esp32_wifi_scan": self._test_wifi,
            "esp32_ble_init": self._test_ble,
            "esp32_i2c_scan": self._test_i2c,
            "esp32_spi_init": self._test_spi,
            "esp32_adc_test": self._test_adc,
            "esp32_pwm_test": self._test_pwm,
            "esp32_dac_test": self._test_dac,
            "esp32_gpio_test": self._test_gpio,
            "esp32_uart_test": self._test_uart,
            "esp32_flash_info": self._test_flash,
            "esp32_psram_test": self._test_psram,
        }
        handler = dispatch.get(test_id)
        if not handler:
            return TestResultEntry(
                test_id=test_id, test_name=test_id,
                result=TestResult.NOT_SUPPORTED,
                error_detail=f"Unknown test: {test_id}",
            )
        start = time.time()
        result = handler(proto, profile)
        result.duration_seconds = time.time() - start
        result.device_type = device.board_model
        return result

    def _test_connection(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_connection", test_name="Connection Test",
                                description="Verify serial connection and agent response")
        if not proto:
            entry.result = TestResult.FAIL
            entry.error_detail = "No protocol connection"
            return entry
        resp = proto.hello()
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
            entry.log.append(f"Agent responded: {resp}")
        else:
            entry.result = TestResult.FAIL
            entry.error_detail = "Agent did not respond to HELLO"
            entry.recommendation = "Ensure test agent firmware is flashed"
        return entry

    def _test_identity(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_identity", test_name="Identity Test",
                                description="Read device identity and chip info")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.get_info()
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
            entry.data = resp.get("data", {})
            entry.log.append(f"Device info: {entry.data}")
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = "Could not read full device info"
        return entry

    def _test_memory(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_memory", test_name="Memory Test",
                                description="Check free heap and PSRAM")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.run_memory_test()
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
            entry.data = resp.get("data", {})
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = "Memory test incomplete"
        return entry

    def _test_wifi(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_wifi_scan", test_name="Wi-Fi Scan",
                                description="Scan for nearby Wi-Fi networks")
        if not profile.wifi:
            entry.result = TestResult.NOT_SUPPORTED
            return entry
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.run_wifi_scan()
        if resp and resp.get("status") == "ok":
            networks = resp.get("data", {}).get("networks", [])
            entry.result = TestResult.PASS
            entry.data = {"network_count": len(networks), "networks": networks[:10]}
            entry.log.append(f"Found {len(networks)} network(s)")
        else:
            entry.result = TestResult.FAIL
            entry.error_detail = "Wi-Fi scan failed"
        return entry

    def _test_ble(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_ble_init", test_name="BLE Init",
                                description="Initialize Bluetooth LE")
        if not profile.bluetooth:
            entry.result = TestResult.NOT_SUPPORTED
            return entry
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.run_ble_init()
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = "BLE init returned unexpected response"
        return entry

    def _test_i2c(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_i2c_scan", test_name="I2C Scan",
                                description="Scan I2C bus for connected devices")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.run_i2c_scan()
        if resp and resp.get("status") == "ok":
            devices = resp.get("data", {}).get("devices", [])
            entry.result = TestResult.PASS
            entry.data = {"i2c_devices": devices}
            entry.log.append(f"Found {len(devices)} I2C device(s)")
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = "I2C scan incomplete"
        return entry

    def _test_spi(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_spi_init", test_name="SPI Init",
                                description="Initialize SPI bus")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.run_spi_init()
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_adc(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_adc_test", test_name="ADC Test",
                                description="Test ADC channels")
        if not proto or not profile.adc_pins:
            entry.result = TestResult.NOT_SUPPORTED
            return entry
        test_pin = profile.adc_pins[0]
        resp = proto.test_adc(pin=test_pin)
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
            entry.data = resp.get("data", {})
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_pwm(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_pwm_test", test_name="PWM Test",
                                description="Test PWM output generation")
        if not proto or not profile.pwm_pins:
            entry.result = TestResult.NOT_SUPPORTED
            return entry
        safe_pins = [p for p in profile.pwm_pins if p not in profile.reserved_pins and p not in profile.unsafe_pins]
        if not safe_pins:
            entry.result = TestResult.SKIPPED
            entry.error_detail = "No safe PWM pins available"
            return entry
        resp = proto.test_pwm(pin=safe_pins[0])
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
            entry.data = resp.get("data", {})
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_dac(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_dac_test", test_name="DAC Test",
                                description="Test DAC output")
        if not profile.dac_pins:
            entry.result = TestResult.NOT_SUPPORTED
            return entry
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.send_command("TEST_DAC", pin=profile.dac_pins[0])
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
            entry.data = resp.get("data", {})
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_gpio(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_gpio_test", test_name="GPIO Basic Test",
                                description="Test basic GPIO operations (software-level)")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        safe_pins = [p for p in profile.digital_pins if p not in profile.reserved_pins and p not in profile.unsafe_pins and p not in profile.boot_pins]
        if not safe_pins:
            entry.result = TestResult.SKIPPED
            return entry
        test_pin = safe_pins[0]
        # Set as output and write HIGH
        r1 = proto.set_pin_mode(test_pin, "OUTPUT")
        r2 = proto.write_pin(test_pin, 1)
        r3 = proto.write_pin(test_pin, 0)
        if all(r and r.get("status") == "ok" for r in [r1, r2, r3]):
            entry.result = TestResult.PASS
            entry.log.append(f"GPIO {test_pin}: OUTPUT mode, HIGH/LOW write OK")
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = f"GPIO {test_pin}: Partial response"
        return entry

    def _test_uart(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_uart_test", test_name="UART Loopback",
                                description="Test UART communication")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.run_uart_test()
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_flash(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_flash_info", test_name="Flash Info",
                                description="Read flash size and partition info")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.send_command("GET_FLASH_INFO")
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
            entry.data = resp.get("data", {})
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_psram(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="esp32_psram_test", test_name="PSRAM Test",
                                description="Check PSRAM availability")
        if not profile.psram:
            entry.result = TestResult.NOT_SUPPORTED
            return entry
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.send_command("TEST_PSRAM")
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
            entry.data = resp.get("data", {})
        else:
            entry.result = TestResult.WARNING
        return entry
