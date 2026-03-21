"""Raspberry Pi Pico device plugin."""

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


class PicoPlugin(DevicePlugin):
    @property
    def family_name(self) -> str:
        return "Raspberry Pi Pico"

    @property
    def supported_families(self) -> list[str]:
        return [DeviceFamily.RASPBERRY_PI_PICO.value]

    def can_handle(self, device: DiscoveredDevice) -> bool:
        return device.family == DeviceFamily.RASPBERRY_PI_PICO

    def identify(self, device: DiscoveredDevice, conn_manager: ConnectionManager) -> dict:
        proto = conn_manager.get_protocol(device.id)
        if not proto:
            return {"error": "No protocol connection"}
        info = proto.get_info()
        if info and info.get("status") == "ok":
            return info.get("data", {})
        hello = proto.hello()
        if hello and hello.get("status") == "ok":
            return hello.get("data", {"agent": "pico", "status": "responsive"})
        return {"error": "Device not responding"}

    def get_quick_tests(self, profile: DeviceProfile) -> list[str]:
        return ["pico_connection", "pico_identity", "pico_gpio_test"]

    def get_full_tests(self, profile: DeviceProfile) -> list[str]:
        tests = [
            "pico_connection",
            "pico_identity",
            "pico_gpio_test",
            "pico_adc_test",
            "pico_pwm_test",
            "pico_i2c_scan",
            "pico_spi_init",
            "pico_uart_test",
        ]
        if profile.wifi:
            tests.append("pico_wifi_scan")
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
            "pico_connection": self._test_connection,
            "pico_identity": self._test_identity,
            "pico_gpio_test": self._test_gpio,
            "pico_adc_test": self._test_adc,
            "pico_pwm_test": self._test_pwm,
            "pico_i2c_scan": self._test_i2c,
            "pico_spi_init": self._test_spi,
            "pico_uart_test": self._test_uart,
            "pico_wifi_scan": self._test_wifi,
        }
        handler = dispatch.get(test_id)
        if not handler:
            return TestResultEntry(test_id=test_id, test_name=test_id, result=TestResult.NOT_SUPPORTED)
        start = time.time()
        result = handler(proto, profile)
        result.duration_seconds = time.time() - start
        result.device_type = device.board_model
        return result

    def _test_connection(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="pico_connection", test_name="Connection Test",
                                description="Verify connection to Pico")
        if not proto:
            entry.result = TestResult.FAIL
            entry.error_detail = "No protocol connection"
            return entry
        resp = proto.hello()
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
        else:
            entry.result = TestResult.FAIL
            entry.recommendation = "Flash the Pico test agent (MicroPython)"
        return entry

    def _test_identity(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="pico_identity", test_name="Identity Test",
                                description="Read Pico device info")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.get_info()
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
            entry.data = resp.get("data", {})
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_gpio(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="pico_gpio_test", test_name="GPIO Test",
                                description="Test GPIO digital I/O")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        safe_pins = [p for p in profile.digital_pins if p not in profile.reserved_pins and p not in profile.unsafe_pins]
        if not safe_pins:
            entry.result = TestResult.SKIPPED
            return entry
        pin = safe_pins[0]
        r1 = proto.set_pin_mode(pin, "OUTPUT")
        r2 = proto.write_pin(pin, 1)
        r3 = proto.write_pin(pin, 0)
        if all(r and r.get("status") == "ok" for r in [r1, r2, r3]):
            entry.result = TestResult.PASS
            entry.log.append(f"GP{pin}: OUTPUT HIGH/LOW OK")
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_adc(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="pico_adc_test", test_name="ADC Test",
                                description="Test ADC reading")
        if not proto or not profile.adc_pins:
            entry.result = TestResult.NOT_SUPPORTED
            return entry
        resp = proto.test_adc(pin=profile.adc_pins[0])
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
            entry.data = resp.get("data", {})
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_pwm(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="pico_pwm_test", test_name="PWM Test",
                                description="Test PWM output")
        if not proto or not profile.pwm_pins:
            entry.result = TestResult.NOT_SUPPORTED
            return entry
        safe = [p for p in profile.pwm_pins if p not in profile.reserved_pins]
        if not safe:
            entry.result = TestResult.SKIPPED
            return entry
        resp = proto.test_pwm(pin=safe[0])
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_i2c(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="pico_i2c_scan", test_name="I2C Scan",
                                description="Scan I2C bus for devices")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.run_i2c_scan()
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
            entry.data = resp.get("data", {})
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_spi(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="pico_spi_init", test_name="SPI Init",
                                description="Initialize SPI")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.run_spi_init()
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_uart(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="pico_uart_test", test_name="UART Test",
                                description="Test UART loopback")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.run_uart_test()
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_wifi(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="pico_wifi_scan", test_name="Wi-Fi Scan",
                                description="Scan Wi-Fi networks (Pico W)")
        if not profile.wifi:
            entry.result = TestResult.NOT_SUPPORTED
            return entry
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.run_wifi_scan()
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
            entry.data = resp.get("data", {})
        else:
            entry.result = TestResult.FAIL
        return entry
