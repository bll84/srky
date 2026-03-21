"""Generic serial device plugin for unknown/unclassified devices."""

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


class GenericSerialPlugin(DevicePlugin):
    @property
    def family_name(self) -> str:
        return "Generic Serial"

    @property
    def supported_families(self) -> list[str]:
        return [DeviceFamily.GENERIC_SERIAL.value, DeviceFamily.UNKNOWN.value]

    def can_handle(self, device: DiscoveredDevice) -> bool:
        return device.family in (DeviceFamily.GENERIC_SERIAL, DeviceFamily.UNKNOWN)

    def identify(self, device: DiscoveredDevice, conn_manager: ConnectionManager) -> dict:
        proto = conn_manager.get_protocol(device.id)
        if not proto:
            return {"port": device.port, "vid": device.vid, "pid": device.pid}
        resp = proto.hello()
        if resp and resp.get("status") == "ok":
            return resp.get("data", {})
        return {"port": device.port, "status": "no_agent_response"}

    def get_quick_tests(self, profile: DeviceProfile) -> list[str]:
        return ["generic_connection", "generic_identity"]

    def get_full_tests(self, profile: DeviceProfile) -> list[str]:
        return ["generic_connection", "generic_identity", "generic_baud_probe"]

    def run_test(
        self,
        test_id: str,
        device: DiscoveredDevice,
        conn_manager: ConnectionManager,
        profile: DeviceProfile,
    ) -> TestResultEntry:
        proto = conn_manager.get_protocol(device.id)
        dispatch = {
            "generic_connection": self._test_connection,
            "generic_identity": self._test_identity,
            "generic_baud_probe": self._test_baud_probe,
        }
        handler = dispatch.get(test_id)
        if not handler:
            return TestResultEntry(test_id=test_id, test_name=test_id, result=TestResult.NOT_SUPPORTED)
        start = time.time()
        result = handler(proto, device, conn_manager)
        result.duration_seconds = time.time() - start
        result.device_type = device.board_model
        return result

    def _test_connection(self, proto, device, conn_manager) -> TestResultEntry:
        entry = TestResultEntry(test_id="generic_connection", test_name="Connection Test",
                                description="Test basic serial port access")
        ser = conn_manager.get_serial(device.id)
        if ser and ser.is_open:
            entry.result = TestResult.PASS
            entry.log.append(f"Port {device.port} is open")
        else:
            entry.result = TestResult.FAIL
            entry.error_detail = "Could not open serial port"
        return entry

    def _test_identity(self, proto, device, conn_manager) -> TestResultEntry:
        entry = TestResultEntry(test_id="generic_identity", test_name="Identity Probe",
                                description="Attempt to identify device")
        entry.data = {
            "port": device.port,
            "vid": f"0x{device.vid:04X}" if device.vid else "N/A",
            "pid": f"0x{device.pid:04X}" if device.pid else "N/A",
            "manufacturer": device.manufacturer,
            "product": device.product,
            "serial": device.serial_number,
        }

        if proto:
            resp = proto.hello()
            if resp and resp.get("status") == "ok":
                entry.result = TestResult.PASS
                entry.data["agent_response"] = resp
                return entry

        entry.result = TestResult.WARNING
        entry.error_detail = "Device does not respond to agent protocol"
        entry.recommendation = "This may be a device without test agent firmware"
        return entry

    def _test_baud_probe(self, proto, device, conn_manager) -> TestResultEntry:
        entry = TestResultEntry(test_id="generic_baud_probe", test_name="Baud Rate Probe",
                                description="Try different baud rates for communication")
        ser = conn_manager.get_serial(device.id)
        if not ser:
            entry.result = TestResult.FAIL
            return entry

        working_bauds = []
        original_baud = ser.baudrate

        for baud in [9600, 19200, 38400, 57600, 115200, 230400, 460800]:
            try:
                ser.baudrate = baud
                ser.reset_input_buffer()
                ser.write(b"HELLO\n")
                time.sleep(0.3)
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    try:
                        text = data.decode("utf-8", errors="replace")
                        if any(c.isalpha() for c in text):
                            working_bauds.append(baud)
                    except Exception:
                        pass
            except Exception:
                pass

        ser.baudrate = original_baud

        entry.data = {"working_baud_rates": working_bauds}
        if working_bauds:
            entry.result = TestResult.PASS
            entry.log.append(f"Responsive at: {working_bauds}")
        else:
            entry.result = TestResult.WARNING
            entry.error_detail = "No baud rate produced readable response"
        return entry
