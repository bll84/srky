"""Device discovery via USB/Serial enumeration and network scanning."""

from __future__ import annotations

import logging
import socket
import subprocess
import threading
from typing import Callable

import serial.tools.list_ports

from core.models import ConnectionType, DeviceFamily, DiscoveredDevice

logger = logging.getLogger(__name__)

# Known USB VID/PID mappings
VID_PID_MAP: dict[tuple[int, int], tuple[DeviceFamily, str, float]] = {
    # Espressif
    (0x303A, 0x1001): (DeviceFamily.ESP32, "ESP32-S2", 0.90),
    (0x303A, 0x1002): (DeviceFamily.ESP32, "ESP32-S3", 0.90),
    (0x303A, 0x0002): (DeviceFamily.ESP32, "ESP32-S2", 0.88),
    (0x303A, 0x80D1): (DeviceFamily.ESP32, "ESP32-C3", 0.88),
    # Silicon Labs CP210x (common for ESP32)
    (0x10C4, 0xEA60): (DeviceFamily.ESP32, "ESP32 (CP2102)", 0.70),
    (0x10C4, 0xEA70): (DeviceFamily.ESP32, "ESP32 (CP2105)", 0.65),
    # WCH CH340 (common for Arduino clones and ESP32)
    (0x1A86, 0x7523): (DeviceFamily.ARDUINO, "Arduino (CH340)", 0.60),
    (0x1A86, 0x55D4): (DeviceFamily.ESP32, "ESP32 (CH343)", 0.65),
    # FTDI
    (0x0403, 0x6001): (DeviceFamily.GENERIC_SERIAL, "FTDI FT232R", 0.50),
    (0x0403, 0x6010): (DeviceFamily.GENERIC_SERIAL, "FTDI FT2232", 0.50),
    (0x0403, 0x6015): (DeviceFamily.GENERIC_SERIAL, "FTDI FT230X", 0.50),
    # Arduino official
    (0x2341, 0x0043): (DeviceFamily.ARDUINO, "Arduino Uno", 0.95),
    (0x2341, 0x0001): (DeviceFamily.ARDUINO, "Arduino Uno", 0.95),
    (0x2341, 0x0010): (DeviceFamily.ARDUINO, "Arduino Mega 2560", 0.95),
    (0x2341, 0x0042): (DeviceFamily.ARDUINO, "Arduino Mega 2560", 0.95),
    (0x2341, 0x0243): (DeviceFamily.ARDUINO, "Arduino Mega 2560", 0.93),
    (0x2341, 0x8036): (DeviceFamily.ARDUINO, "Arduino Leonardo", 0.95),
    (0x2341, 0x8037): (DeviceFamily.ARDUINO, "Arduino Micro", 0.95),
    (0x2A03, 0x0043): (DeviceFamily.ARDUINO, "Arduino Uno (clone)", 0.90),
    (0x2A03, 0x0010): (DeviceFamily.ARDUINO, "Arduino Mega (clone)", 0.90),
    # Arduino Nano (various clones)
    (0x0403, 0x6001): (DeviceFamily.ARDUINO, "Arduino Nano (FTDI)", 0.65),
    # Raspberry Pi Pico
    (0x2E8A, 0x0005): (DeviceFamily.RASPBERRY_PI_PICO, "Raspberry Pi Pico", 0.95),
    (0x2E8A, 0x000A): (DeviceFamily.RASPBERRY_PI_PICO, "Raspberry Pi Pico W", 0.95),
    (0x2E8A, 0x0003): (DeviceFamily.RASPBERRY_PI_PICO, "RP2040 Board", 0.85),
    (0x2E8A, 0x000F): (DeviceFamily.RASPBERRY_PI_PICO, "Raspberry Pi Pico (MicroPython)", 0.92),
}

# Manufacturer string hints
MANUFACTURER_HINTS: list[tuple[str, DeviceFamily, str, float]] = [
    ("Espressif", DeviceFamily.ESP32, "ESP32", 0.80),
    ("Silicon Labs", DeviceFamily.ESP32, "ESP32 (SiLabs)", 0.55),
    ("Arduino", DeviceFamily.ARDUINO, "Arduino", 0.85),
    ("wch.cn", DeviceFamily.ARDUINO, "Arduino (CH340)", 0.50),
    ("Raspberry Pi", DeviceFamily.RASPBERRY_PI_PICO, "Raspberry Pi Pico", 0.85),
    ("MicroPython", DeviceFamily.RASPBERRY_PI_PICO, "MicroPython Board", 0.70),
    ("FTDI", DeviceFamily.GENERIC_SERIAL, "FTDI Device", 0.40),
]

# Product description hints
PRODUCT_HINTS: list[tuple[str, DeviceFamily, str, float]] = [
    ("ESP32", DeviceFamily.ESP32, "ESP32", 0.85),
    ("ESP32-S2", DeviceFamily.ESP32, "ESP32-S2", 0.88),
    ("ESP32-S3", DeviceFamily.ESP32, "ESP32-S3", 0.88),
    ("ESP32-C3", DeviceFamily.ESP32, "ESP32-C3", 0.88),
    ("Arduino Uno", DeviceFamily.ARDUINO, "Arduino Uno", 0.90),
    ("Arduino Mega", DeviceFamily.ARDUINO, "Arduino Mega", 0.90),
    ("Arduino Nano", DeviceFamily.ARDUINO, "Arduino Nano", 0.90),
    ("Arduino Leonardo", DeviceFamily.ARDUINO, "Arduino Leonardo", 0.90),
    ("Pico", DeviceFamily.RASPBERRY_PI_PICO, "Raspberry Pi Pico", 0.80),
    ("RP2040", DeviceFamily.RASPBERRY_PI_PICO, "RP2040 Board", 0.82),
]


class DeviceScanner:
    """Scans for connected devices via USB/Serial and network."""

    def __init__(self) -> None:
        self._stop_event = threading.Event()

    def scan_serial_ports(self) -> list[DiscoveredDevice]:
        """Enumerate all serial ports and classify devices."""
        devices: list[DiscoveredDevice] = []
        try:
            ports = serial.tools.list_ports.comports()
        except Exception as e:
            logger.error("Failed to enumerate serial ports: %s", e)
            return devices

        for port_info in ports:
            device = self._classify_serial_port(port_info)
            devices.append(device)

        return devices

    def _classify_serial_port(self, port_info) -> DiscoveredDevice:
        """Classify a serial port into a device."""
        device = DiscoveredDevice(
            port=port_info.device,
            connection_type=ConnectionType.USB_SERIAL,
            vid=port_info.vid,
            pid=port_info.pid,
            manufacturer=port_info.manufacturer or "",
            product=port_info.product or "",
            serial_number=port_info.serial_number or "",
            description=port_info.description or "",
        )

        best_confidence = 0.0
        best_family = DeviceFamily.UNKNOWN
        best_model = "Unknown Serial Device"

        # Strategy 1: VID/PID match
        if port_info.vid is not None and port_info.pid is not None:
            key = (port_info.vid, port_info.pid)
            if key in VID_PID_MAP:
                family, model, conf = VID_PID_MAP[key]
                if conf > best_confidence:
                    best_confidence = conf
                    best_family = family
                    best_model = model

        # Strategy 2: Manufacturer string
        if port_info.manufacturer:
            mfr = port_info.manufacturer.lower()
            for hint, family, model, conf in MANUFACTURER_HINTS:
                if hint.lower() in mfr and conf > best_confidence:
                    best_confidence = conf
                    best_family = family
                    best_model = model

        # Strategy 3: Product / description string
        for text in [port_info.product or "", port_info.description or ""]:
            if text:
                text_lower = text.lower()
                for hint, family, model, conf in PRODUCT_HINTS:
                    if hint.lower() in text_lower and conf > best_confidence:
                        best_confidence = conf
                        best_family = family
                        best_model = model

        # Generic fallback
        if best_family == DeviceFamily.UNKNOWN:
            best_confidence = max(best_confidence, 0.20)
            best_family = DeviceFamily.GENERIC_SERIAL
            best_model = "Unknown Serial Device"

        device.family = best_family
        device.board_model = best_model
        device.confidence = best_confidence

        return device

    def scan_ssh_hosts(
        self,
        hosts: list[str] | None = None,
        subnet: str = "",
        port: int = 22,
        timeout: float = 2.0,
    ) -> list[DiscoveredDevice]:
        """Scan for Raspberry Pi Linux devices via SSH."""
        devices: list[DiscoveredDevice] = []

        if hosts is None:
            hosts = []

        # Try common Raspberry Pi hostnames
        default_hosts = ["raspberrypi.local", "raspberry.local"]
        all_hosts = list(hosts) + default_hosts

        # If subnet provided, scan range
        if subnet:
            try:
                base = subnet.rsplit(".", 1)[0]
                all_hosts.extend(f"{base}.{i}" for i in range(1, 255))
            except (ValueError, IndexError):
                pass

        for host in all_hosts:
            if self._stop_event.is_set():
                break
            if self._check_ssh_port(host, port, timeout):
                device = DiscoveredDevice(
                    ip_address=host,
                    family=DeviceFamily.RASPBERRY_PI_LINUX,
                    board_model="Raspberry Pi (SSH)",
                    connection_type=ConnectionType.SSH,
                    confidence=0.75,
                    description=f"SSH host at {host}:{port}",
                )
                devices.append(device)
                logger.info("Found SSH device at %s", host)

        return devices

    def _check_ssh_port(self, host: str, port: int, timeout: float) -> bool:
        """Check if SSH port is open on a host."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except (socket.error, OSError):
            return False

    def scan_all(
        self,
        ssh_hosts: list[str] | None = None,
        ssh_subnet: str = "",
        progress_callback: Callable[[str], None] | None = None,
    ) -> list[DiscoveredDevice]:
        """Run full device scan (serial + SSH)."""
        devices: list[DiscoveredDevice] = []

        if progress_callback:
            progress_callback("Scanning serial ports...")
        serial_devices = self.scan_serial_ports()
        devices.extend(serial_devices)

        if progress_callback:
            progress_callback("Scanning SSH hosts...")
        ssh_devices = self.scan_ssh_hosts(hosts=ssh_hosts, subnet=ssh_subnet)
        devices.extend(ssh_devices)

        if progress_callback:
            progress_callback(f"Scan complete. Found {len(devices)} device(s).")

        return devices

    def stop(self) -> None:
        self._stop_event.set()
