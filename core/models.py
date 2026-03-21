"""Core data models for DeviceProbe."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DeviceFamily(Enum):
    ESP32 = "esp32"
    ARDUINO = "arduino"
    RASPBERRY_PI_PICO = "raspberry_pi_pico"
    RASPBERRY_PI_LINUX = "raspberry_pi_linux"
    GENERIC_SERIAL = "generic_serial"
    UNKNOWN = "unknown"


class ConnectionType(Enum):
    USB_SERIAL = "usb_serial"
    RAW_SERIAL = "raw_serial"
    SSH = "ssh"
    MANUAL = "manual"


class TestResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class PinFunction(Enum):
    DIGITAL_IN = "digital_in"
    DIGITAL_OUT = "digital_out"
    ANALOG_IN = "analog_in"
    ANALOG_OUT = "analog_out"
    PWM = "pwm"
    ADC = "adc"
    DAC = "dac"
    I2C_SDA = "i2c_sda"
    I2C_SCL = "i2c_scl"
    SPI_MOSI = "spi_mosi"
    SPI_MISO = "spi_miso"
    SPI_SCK = "spi_sck"
    SPI_CS = "spi_cs"
    UART_TX = "uart_tx"
    UART_RX = "uart_rx"
    TOUCH = "touch"
    BOOT = "boot"
    RESERVED = "reserved"


class PinStatus(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    WARNING = "warning"
    PASSED = "passed"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"
    UNTESTED = "untested"


@dataclass
class PinDefinition:
    number: int
    name: str
    gpio_number: int | None = None
    functions: list[PinFunction] = field(default_factory=list)
    is_reserved: bool = False
    is_boot_pin: bool = False
    is_unsafe: bool = False
    voltage_level: float = 3.3
    notes: str = ""
    status: PinStatus = PinStatus.UNTESTED


@dataclass
class DeviceProfile:
    family: DeviceFamily = DeviceFamily.UNKNOWN
    model: str = ""
    mcu: str = ""
    connection_modes: list[ConnectionType] = field(default_factory=list)
    pins: list[PinDefinition] = field(default_factory=list)
    digital_pins: list[int] = field(default_factory=list)
    analog_pins: list[int] = field(default_factory=list)
    pwm_pins: list[int] = field(default_factory=list)
    adc_pins: list[int] = field(default_factory=list)
    dac_pins: list[int] = field(default_factory=list)
    i2c_default: dict[str, int] = field(default_factory=dict)
    spi_default: dict[str, int] = field(default_factory=dict)
    uart_ports: list[dict[str, int]] = field(default_factory=list)
    reserved_pins: list[int] = field(default_factory=list)
    boot_pins: list[int] = field(default_factory=list)
    unsafe_pins: list[int] = field(default_factory=list)
    supported_tests: list[str] = field(default_factory=list)
    notes: str = ""
    flash_size_mb: int = 0
    ram_kb: int = 0
    psram: bool = False
    wifi: bool = False
    bluetooth: bool = False
    usb_vid: list[int] = field(default_factory=list)
    usb_pid: list[int] = field(default_factory=list)


@dataclass
class DiscoveredDevice:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    port: str = ""
    ip_address: str = ""
    family: DeviceFamily = DeviceFamily.UNKNOWN
    board_model: str = "Unknown"
    connection_type: ConnectionType = ConnectionType.USB_SERIAL
    confidence: float = 0.0
    vid: int | None = None
    pid: int | None = None
    manufacturer: str = ""
    product: str = ""
    serial_number: str = ""
    description: str = ""
    profile: DeviceProfile | None = None
    is_connected: bool = False


@dataclass
class TestCase:
    id: str = ""
    name: str = ""
    description: str = ""
    category: str = ""
    device_families: list[DeviceFamily] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    requires_user_action: bool = False
    user_instruction: str = ""
    is_destructive: bool = False
    timeout_seconds: float = 30.0


@dataclass
class TestResultEntry:
    test_id: str = ""
    test_name: str = ""
    description: str = ""
    device_type: str = ""
    prerequisites: list[str] = field(default_factory=list)
    result: TestResult = TestResult.SKIPPED
    error_detail: str = ""
    recommendation: str = ""
    duration_seconds: float = 0.0
    log: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class TestReport:
    device_summary: str = ""
    device_family: str = ""
    board_model: str = ""
    connection_type: str = ""
    confidence: float = 0.0
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    skipped: int = 0
    unsupported: int = 0
    errors: int = 0
    results: list[TestResultEntry] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    duration_seconds: float = 0.0
    raw_logs: list[str] = field(default_factory=list)


@dataclass
class SSHCredentials:
    host: str = ""
    port: int = 22
    username: str = "pi"
    password: str = ""
    key_file: str = ""
