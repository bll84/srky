"""Arduino device plugin."""

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


class ArduinoPlugin(DevicePlugin):
    @property
    def family_name(self) -> str:
        return "Arduino"

    @property
    def supported_families(self) -> list[str]:
        return [DeviceFamily.ARDUINO.value]

    def can_handle(self, device: DiscoveredDevice) -> bool:
        return device.family == DeviceFamily.ARDUINO

    def identify(self, device: DiscoveredDevice, conn_manager: ConnectionManager) -> dict:
        proto = conn_manager.get_protocol(device.id)
        if not proto:
            return {"error": "No protocol connection"}
        info = proto.get_info()
        if info and info.get("status") == "ok":
            return info.get("data", {})
        hello = proto.hello()
        if hello and hello.get("status") == "ok":
            return hello.get("data", {"agent": "arduino", "status": "responsive"})
        return {"error": "Device not responding"}

    def get_quick_tests(self, profile: DeviceProfile) -> list[str]:
        return ["arduino_connection", "arduino_identity", "arduino_gpio_test"]

    def get_full_tests(self, profile: DeviceProfile) -> list[str]:
        tests = [
            "arduino_connection",
            "arduino_identity",
            "arduino_gpio_test",
            "arduino_adc_test",
            "arduino_pwm_test",
            "arduino_i2c_scan",
            "arduino_spi_init",
            "arduino_uart_test",
        ]
        if "eeprom" in profile.supported_tests:
            tests.append("arduino_eeprom_test")
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
            "arduino_connection": self._test_connection,
            "arduino_identity": self._test_identity,
            "arduino_gpio_test": self._test_gpio,
            "arduino_adc_test": self._test_adc,
            "arduino_pwm_test": self._test_pwm,
            "arduino_i2c_scan": self._test_i2c,
            "arduino_spi_init": self._test_spi,
            "arduino_uart_test": self._test_uart,
            "arduino_eeprom_test": self._test_eeprom,
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
        entry = TestResultEntry(test_id="arduino_connection", test_name="Connection Test",
                                description="Verify serial connection to Arduino")
        if not proto:
            entry.result = TestResult.FAIL
            entry.error_detail = "No protocol connection"
            return entry
        resp = proto.hello()
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
        else:
            entry.result = TestResult.FAIL
            entry.error_detail = "Agent not responding"
            entry.recommendation = "Flash the Arduino test agent sketch"
        return entry

    def _test_identity(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="arduino_identity", test_name="Identity Test",
                                description="Read board identity")
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
        entry = TestResultEntry(test_id="arduino_gpio_test", test_name="GPIO Test",
                                description="Test digital I/O (software-level)")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        safe_pins = [p for p in profile.digital_pins if p not in profile.reserved_pins]
        if not safe_pins:
            entry.result = TestResult.SKIPPED
            return entry
        pin = safe_pins[0]
        r1 = proto.set_pin_mode(pin, "OUTPUT")
        r2 = proto.write_pin(pin, 1)
        r3 = proto.write_pin(pin, 0)
        if all(r and r.get("status") == "ok" for r in [r1, r2, r3]):
            entry.result = TestResult.PASS
            entry.log.append(f"Pin D{pin}: write HIGH/LOW OK")
        else:
            entry.result = TestResult.WARNING
        return entry

    def _test_adc(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="arduino_adc_test", test_name="ADC Test",
                                description="Test analog input reading")
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
        entry = TestResultEntry(test_id="arduino_pwm_test", test_name="PWM Test",
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
        entry = TestResultEntry(test_id="arduino_i2c_scan", test_name="I2C Scan",
                                description="Scan I2C bus")
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
        entry = TestResultEntry(test_id="arduino_spi_init", test_name="SPI Init",
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

    def _test_uart(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="arduino_uart_test", test_name="UART Test",
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

    def _test_eeprom(self, proto, profile) -> TestResultEntry:
        entry = TestResultEntry(test_id="arduino_eeprom_test", test_name="EEPROM Test",
                                description="Basic EEPROM read/write test")
        if not proto:
            entry.result = TestResult.FAIL
            return entry
        resp = proto.send_command("TEST_EEPROM")
        if resp and resp.get("status") == "ok":
            entry.result = TestResult.PASS
            entry.data = resp.get("data", {})
        else:
            entry.result = TestResult.WARNING
        return entry
