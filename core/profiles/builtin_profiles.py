"""Built-in device profiles for supported boards."""

from core.models import (
    ConnectionType,
    DeviceFamily,
    DeviceProfile,
    PinDefinition,
    PinFunction,
)
from core.profiles.profile_registry import ProfileRegistry


def _esp32_pins() -> list[PinDefinition]:
    """ESP32 DevKit V1 pin definitions."""
    pins = []
    gpio_info = {
        0: ("GPIO0", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC, PinFunction.TOUCH], True, False, "Boot pin - pulled HIGH for normal boot"),
        1: ("TX0", [PinFunction.UART_TX], True, False, "UART0 TX - used for programming"),
        2: ("GPIO2", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC, PinFunction.TOUCH], False, False, "Built-in LED on some boards"),
        3: ("RX0", [PinFunction.UART_RX], True, False, "UART0 RX - used for programming"),
        4: ("GPIO4", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC, PinFunction.TOUCH], False, False, ""),
        5: ("GPIO5", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.PWM], False, False, "VSPI CS0"),
        12: ("GPIO12", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC, PinFunction.TOUCH, PinFunction.PWM], False, True, "Boot fail if pulled HIGH"),
        13: ("GPIO13", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC, PinFunction.TOUCH, PinFunction.PWM], False, False, ""),
        14: ("GPIO14", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC, PinFunction.TOUCH, PinFunction.PWM], False, False, ""),
        15: ("GPIO15", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC, PinFunction.TOUCH, PinFunction.PWM], False, False, ""),
        16: ("GPIO16", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.PWM], False, False, "UART2 RX"),
        17: ("GPIO17", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.PWM], False, False, "UART2 TX"),
        18: ("GPIO18", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.PWM, PinFunction.SPI_SCK], False, False, "VSPI SCK"),
        19: ("GPIO19", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.PWM, PinFunction.SPI_MISO], False, False, "VSPI MISO"),
        21: ("GPIO21", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.I2C_SDA], False, False, "Default I2C SDA"),
        22: ("GPIO22", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.I2C_SCL], False, False, "Default I2C SCL"),
        23: ("GPIO23", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.PWM, PinFunction.SPI_MOSI], False, False, "VSPI MOSI"),
        25: ("GPIO25", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC, PinFunction.DAC], False, False, "DAC1"),
        26: ("GPIO26", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC, PinFunction.DAC], False, False, "DAC2"),
        27: ("GPIO27", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC, PinFunction.TOUCH, PinFunction.PWM], False, False, ""),
        32: ("GPIO32", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC, PinFunction.TOUCH, PinFunction.PWM], False, False, ""),
        33: ("GPIO33", [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC, PinFunction.TOUCH, PinFunction.PWM], False, False, ""),
        34: ("GPIO34", [PinFunction.DIGITAL_IN, PinFunction.ADC], False, False, "Input only - no internal pull-up"),
        35: ("GPIO35", [PinFunction.DIGITAL_IN, PinFunction.ADC], False, False, "Input only - no internal pull-up"),
        36: ("SVP", [PinFunction.DIGITAL_IN, PinFunction.ADC], False, False, "Input only - no internal pull-up"),
        39: ("SVN", [PinFunction.DIGITAL_IN, PinFunction.ADC], False, False, "Input only - no internal pull-up"),
    }

    for gpio_num, (name, funcs, is_boot, is_unsafe, notes) in gpio_info.items():
        pins.append(PinDefinition(
            number=gpio_num,
            name=name,
            gpio_number=gpio_num,
            functions=funcs,
            is_reserved=is_boot and gpio_num in (1, 3),
            is_boot_pin=is_boot,
            is_unsafe=is_unsafe,
            voltage_level=3.3,
            notes=notes,
        ))

    return pins


def _arduino_uno_pins() -> list[PinDefinition]:
    """Arduino Uno pin definitions."""
    pins = []
    # Digital pins D0-D13
    for i in range(14):
        funcs = [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT]
        is_reserved = i in (0, 1)  # TX/RX
        notes = ""
        if i == 0:
            funcs.append(PinFunction.UART_RX)
            notes = "Serial RX"
        elif i == 1:
            funcs.append(PinFunction.UART_TX)
            notes = "Serial TX"
        elif i in (3, 5, 6, 9, 10, 11):
            funcs.append(PinFunction.PWM)
        if i == 10:
            funcs.append(PinFunction.SPI_CS)
            notes = "SPI SS"
        elif i == 11:
            funcs.append(PinFunction.SPI_MOSI)
            notes = "SPI MOSI"
        elif i == 12:
            funcs.append(PinFunction.SPI_MISO)
            notes = "SPI MISO"
        elif i == 13:
            funcs.append(PinFunction.SPI_SCK)
            notes = "SPI SCK / Built-in LED"

        pins.append(PinDefinition(
            number=i, name=f"D{i}", gpio_number=i,
            functions=funcs, is_reserved=is_reserved,
            voltage_level=5.0, notes=notes,
        ))

    # Analog pins A0-A5
    for i in range(6):
        funcs = [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC]
        notes = ""
        if i == 4:
            funcs.append(PinFunction.I2C_SDA)
            notes = "I2C SDA"
        elif i == 5:
            funcs.append(PinFunction.I2C_SCL)
            notes = "I2C SCL"
        pins.append(PinDefinition(
            number=14 + i, name=f"A{i}", gpio_number=14 + i,
            functions=funcs, voltage_level=5.0, notes=notes,
        ))

    return pins


def _arduino_nano_pins() -> list[PinDefinition]:
    """Arduino Nano - same pin layout as Uno with A6/A7 extra analog."""
    pins = _arduino_uno_pins()
    for i in range(6, 8):
        pins.append(PinDefinition(
            number=14 + i, name=f"A{i}", gpio_number=14 + i,
            functions=[PinFunction.ADC],
            voltage_level=5.0, notes="Analog input only",
        ))
    return pins


def _arduino_mega_pins() -> list[PinDefinition]:
    """Arduino Mega 2560 pin definitions."""
    pins = []
    # Digital 0-53
    pwm_pins = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 44, 45, 46}
    for i in range(54):
        funcs = [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT]
        is_reserved = i in (0, 1)
        notes = ""
        if i == 0:
            funcs.append(PinFunction.UART_RX)
            notes = "Serial RX"
        elif i == 1:
            funcs.append(PinFunction.UART_TX)
            notes = "Serial TX"
        if i in pwm_pins:
            funcs.append(PinFunction.PWM)
        if i == 20:
            funcs.append(PinFunction.I2C_SDA)
            notes = "I2C SDA"
        elif i == 21:
            funcs.append(PinFunction.I2C_SCL)
            notes = "I2C SCL"
        if i == 50:
            funcs.append(PinFunction.SPI_MISO)
        elif i == 51:
            funcs.append(PinFunction.SPI_MOSI)
        elif i == 52:
            funcs.append(PinFunction.SPI_SCK)
        elif i == 53:
            funcs.append(PinFunction.SPI_CS)

        pins.append(PinDefinition(
            number=i, name=f"D{i}", gpio_number=i,
            functions=funcs, is_reserved=is_reserved,
            voltage_level=5.0, notes=notes,
        ))

    # Analog A0-A15
    for i in range(16):
        funcs = [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.ADC]
        pins.append(PinDefinition(
            number=54 + i, name=f"A{i}", gpio_number=54 + i,
            functions=funcs, voltage_level=5.0,
        ))

    return pins


def _pico_pins() -> list[PinDefinition]:
    """Raspberry Pi Pico pin definitions."""
    pins = []
    adc_pins = {26, 27, 28}
    i2c_sda = {0, 4, 8, 12, 16, 20}
    i2c_scl = {1, 5, 9, 13, 17, 21}

    for i in range(29):
        funcs = [PinFunction.DIGITAL_IN, PinFunction.DIGITAL_OUT, PinFunction.PWM]
        notes = ""
        if i in adc_pins:
            funcs.append(PinFunction.ADC)
            notes = f"ADC{i - 26}"
        if i in i2c_sda:
            funcs.append(PinFunction.I2C_SDA)
        if i in i2c_scl:
            funcs.append(PinFunction.I2C_SCL)
        if i in (0, 4, 8, 12, 16, 20):
            funcs.append(PinFunction.UART_TX)
        if i in (1, 5, 9, 13, 17, 21):
            funcs.append(PinFunction.UART_RX)
        if i in (3, 7, 11, 15, 19):
            funcs.append(PinFunction.SPI_MOSI)
        if i in (0, 4, 8, 12, 16):
            funcs.append(PinFunction.SPI_MISO)
        if i in (2, 6, 10, 14, 18):
            funcs.append(PinFunction.SPI_SCK)

        pins.append(PinDefinition(
            number=i, name=f"GP{i}", gpio_number=i,
            functions=funcs, voltage_level=3.3, notes=notes,
        ))

    return pins


def register_builtin_profiles(registry: ProfileRegistry) -> None:
    """Register all built-in device profiles."""

    # ── ESP32 Generic ──
    registry.register("generic_esp32", DeviceProfile(
        family=DeviceFamily.ESP32,
        model="Generic ESP32",
        mcu="ESP32",
        connection_modes=[ConnectionType.USB_SERIAL],
        pins=_esp32_pins(),
        digital_pins=[0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33],
        analog_pins=[32, 33, 34, 35, 36, 39, 25, 26, 27, 14, 12, 13, 15, 2, 4, 0],
        pwm_pins=[2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33],
        adc_pins=[32, 33, 34, 35, 36, 39, 25, 26, 27, 14, 12, 13, 15, 2, 4, 0],
        dac_pins=[25, 26],
        i2c_default={"sda": 21, "scl": 22},
        spi_default={"mosi": 23, "miso": 19, "sck": 18, "cs": 5},
        uart_ports=[{"tx": 1, "rx": 3}, {"tx": 17, "rx": 16}],
        reserved_pins=[1, 3, 6, 7, 8, 9, 10, 11],
        boot_pins=[0, 2, 12, 15],
        unsafe_pins=[6, 7, 8, 9, 10, 11],
        supported_tests=["connection", "identity", "gpio", "adc", "dac", "pwm", "i2c", "spi", "uart", "wifi", "ble", "memory", "nvs", "flash"],
        flash_size_mb=4,
        ram_kb=520,
        psram=False,
        wifi=True,
        bluetooth=True,
        usb_vid=[0x10C4, 0x1A86, 0x303A],
        usb_pid=[0xEA60, 0x7523, 0x1001],
        notes="Generic ESP32 DevKit. GPIO 6-11 connected to internal flash - DO NOT USE.",
    ))

    # ── ESP32 DevKit V1 ──
    registry.register("esp32_devkit_v1", DeviceProfile(
        family=DeviceFamily.ESP32,
        model="ESP32 DevKit V1",
        mcu="ESP32-WROOM-32",
        connection_modes=[ConnectionType.USB_SERIAL],
        pins=_esp32_pins(),
        digital_pins=[0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33],
        analog_pins=[32, 33, 34, 35, 36, 39, 25, 26, 27, 14, 12, 13, 15, 2, 4, 0],
        pwm_pins=[2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33],
        adc_pins=[32, 33, 34, 35, 36, 39, 25, 26, 27, 14, 12, 13, 15, 2, 4, 0],
        dac_pins=[25, 26],
        i2c_default={"sda": 21, "scl": 22},
        spi_default={"mosi": 23, "miso": 19, "sck": 18, "cs": 5},
        uart_ports=[{"tx": 1, "rx": 3}, {"tx": 17, "rx": 16}],
        reserved_pins=[1, 3, 6, 7, 8, 9, 10, 11],
        boot_pins=[0, 2, 12, 15],
        unsafe_pins=[6, 7, 8, 9, 10, 11],
        supported_tests=["connection", "identity", "gpio", "adc", "dac", "pwm", "i2c", "spi", "uart", "wifi", "ble", "memory", "nvs", "flash"],
        flash_size_mb=4,
        ram_kb=520,
        psram=False,
        wifi=True,
        bluetooth=True,
        usb_vid=[0x10C4],
        usb_pid=[0xEA60],
        notes="ESP32 DevKit V1 with CP2102 USB bridge. 30/38 pin variant.",
    ))

    # ── Arduino Uno ──
    registry.register("arduino_uno", DeviceProfile(
        family=DeviceFamily.ARDUINO,
        model="Arduino Uno",
        mcu="ATmega328P",
        connection_modes=[ConnectionType.USB_SERIAL],
        pins=_arduino_uno_pins(),
        digital_pins=list(range(14)),
        analog_pins=list(range(14, 20)),
        pwm_pins=[3, 5, 6, 9, 10, 11],
        adc_pins=list(range(14, 20)),
        dac_pins=[],
        i2c_default={"sda": 18, "scl": 19},
        spi_default={"mosi": 11, "miso": 12, "sck": 13, "cs": 10},
        uart_ports=[{"tx": 1, "rx": 0}],
        reserved_pins=[0, 1],
        boot_pins=[],
        unsafe_pins=[],
        supported_tests=["connection", "identity", "gpio", "adc", "pwm", "i2c", "spi", "uart", "eeprom"],
        flash_size_mb=0,
        ram_kb=2,
        usb_vid=[0x2341, 0x2A03],
        usb_pid=[0x0043, 0x0001],
        notes="Arduino Uno. 5V logic level! Do not connect directly to 3.3V devices.",
    ))

    # ── Arduino Nano ──
    registry.register("arduino_nano", DeviceProfile(
        family=DeviceFamily.ARDUINO,
        model="Arduino Nano",
        mcu="ATmega328P",
        connection_modes=[ConnectionType.USB_SERIAL],
        pins=_arduino_nano_pins(),
        digital_pins=list(range(14)),
        analog_pins=list(range(14, 22)),
        pwm_pins=[3, 5, 6, 9, 10, 11],
        adc_pins=list(range(14, 22)),
        dac_pins=[],
        i2c_default={"sda": 18, "scl": 19},
        spi_default={"mosi": 11, "miso": 12, "sck": 13, "cs": 10},
        uart_ports=[{"tx": 1, "rx": 0}],
        reserved_pins=[0, 1],
        boot_pins=[],
        unsafe_pins=[],
        supported_tests=["connection", "identity", "gpio", "adc", "pwm", "i2c", "spi", "uart", "eeprom"],
        flash_size_mb=0,
        ram_kb=2,
        usb_vid=[0x1A86, 0x0403],
        usb_pid=[0x7523, 0x6001],
        notes="Arduino Nano. 5V logic. Often uses CH340 or FTDI USB bridge.",
    ))

    # ── Arduino Mega ──
    registry.register("arduino_mega", DeviceProfile(
        family=DeviceFamily.ARDUINO,
        model="Arduino Mega 2560",
        mcu="ATmega2560",
        connection_modes=[ConnectionType.USB_SERIAL],
        pins=_arduino_mega_pins(),
        digital_pins=list(range(54)),
        analog_pins=list(range(54, 70)),
        pwm_pins=[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 44, 45, 46],
        adc_pins=list(range(54, 70)),
        dac_pins=[],
        i2c_default={"sda": 20, "scl": 21},
        spi_default={"mosi": 51, "miso": 50, "sck": 52, "cs": 53},
        uart_ports=[{"tx": 1, "rx": 0}, {"tx": 18, "rx": 19}, {"tx": 16, "rx": 17}, {"tx": 14, "rx": 15}],
        reserved_pins=[0, 1],
        boot_pins=[],
        unsafe_pins=[],
        supported_tests=["connection", "identity", "gpio", "adc", "pwm", "i2c", "spi", "uart", "eeprom"],
        flash_size_mb=0,
        ram_kb=8,
        usb_vid=[0x2341, 0x2A03],
        usb_pid=[0x0010, 0x0042],
        notes="Arduino Mega 2560. 5V logic. 4 hardware serial ports.",
    ))

    # ── Raspberry Pi Pico ──
    registry.register("raspberry_pi_pico", DeviceProfile(
        family=DeviceFamily.RASPBERRY_PI_PICO,
        model="Raspberry Pi Pico",
        mcu="RP2040",
        connection_modes=[ConnectionType.USB_SERIAL],
        pins=_pico_pins(),
        digital_pins=list(range(29)),
        analog_pins=[26, 27, 28],
        pwm_pins=list(range(29)),
        adc_pins=[26, 27, 28],
        dac_pins=[],
        i2c_default={"sda": 0, "scl": 1},
        spi_default={"mosi": 3, "miso": 0, "sck": 2, "cs": 1},
        uart_ports=[{"tx": 0, "rx": 1}, {"tx": 4, "rx": 5}],
        reserved_pins=[],
        boot_pins=[],
        unsafe_pins=[],
        supported_tests=["connection", "identity", "gpio", "adc", "pwm", "i2c", "spi", "uart"],
        flash_size_mb=2,
        ram_kb=264,
        usb_vid=[0x2E8A],
        usb_pid=[0x0005, 0x000F],
        notes="Raspberry Pi Pico. 3.3V logic. Dual-core ARM Cortex-M0+.",
    ))

    # ── Raspberry Pi Pico W ──
    registry.register("raspberry_pi_pico_w", DeviceProfile(
        family=DeviceFamily.RASPBERRY_PI_PICO,
        model="Raspberry Pi Pico W",
        mcu="RP2040",
        connection_modes=[ConnectionType.USB_SERIAL],
        pins=_pico_pins(),
        digital_pins=list(range(29)),
        analog_pins=[26, 27, 28],
        pwm_pins=list(range(29)),
        adc_pins=[26, 27, 28],
        dac_pins=[],
        i2c_default={"sda": 0, "scl": 1},
        spi_default={"mosi": 3, "miso": 0, "sck": 2, "cs": 1},
        uart_ports=[{"tx": 0, "rx": 1}, {"tx": 4, "rx": 5}],
        reserved_pins=[23, 24, 25, 29],
        boot_pins=[],
        unsafe_pins=[23, 24, 25, 29],
        supported_tests=["connection", "identity", "gpio", "adc", "pwm", "i2c", "spi", "uart", "wifi"],
        flash_size_mb=2,
        ram_kb=264,
        wifi=True,
        bluetooth=True,
        usb_vid=[0x2E8A],
        usb_pid=[0x000A, 0x000F],
        notes="Raspberry Pi Pico W. GP23/24/25/29 used by wireless module.",
    ))

    # ── Raspberry Pi Linux (SSH) ──
    registry.register("raspberry_pi_linux", DeviceProfile(
        family=DeviceFamily.RASPBERRY_PI_LINUX,
        model="Raspberry Pi (Linux)",
        mcu="BCM2711/BCM2712",
        connection_modes=[ConnectionType.SSH],
        digital_pins=list(range(28)),
        i2c_default={"sda": 2, "scl": 3},
        spi_default={"mosi": 10, "miso": 9, "sck": 11, "cs": 8},
        uart_ports=[{"tx": 14, "rx": 15}],
        reserved_pins=[0, 1, 2, 3],
        supported_tests=["connection", "identity", "system_info", "gpio_check", "i2c_check", "spi_check", "uart_check", "wifi_check", "bluetooth_check", "temperature", "services"],
        wifi=True,
        bluetooth=True,
        notes="Raspberry Pi 3/4/5 running Linux. Tested via SSH.",
    ))

    # ── Generic Serial Device ──
    registry.register("generic_serial", DeviceProfile(
        family=DeviceFamily.GENERIC_SERIAL,
        model="Generic Serial Device",
        mcu="Unknown",
        connection_modes=[ConnectionType.USB_SERIAL, ConnectionType.RAW_SERIAL],
        supported_tests=["connection", "identity"],
        notes="Unknown serial device. Limited testing available.",
    ))
