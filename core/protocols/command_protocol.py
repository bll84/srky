"""Command protocol for communicating with device test agents."""

from __future__ import annotations

import json
import logging
import time

import serial

logger = logging.getLogger(__name__)


class CommandProtocol:
    """JSON-based command protocol for device test agents.

    Sends commands like HELLO, GET_INFO, etc. and parses JSON responses.
    """

    TIMEOUT = 5.0
    BAUD_RATES = [115200, 9600, 57600, 38400, 460800]

    def __init__(self, ser: serial.Serial) -> None:
        self.ser = ser
        self._buffer = ""

    def send_command(self, command: str, **params) -> dict | None:
        """Send a command and wait for JSON response."""
        msg = command
        if params:
            param_str = " ".join(f"{k}={v}" for k, v in params.items())
            msg = f"{command} {param_str}"

        try:
            self.ser.reset_input_buffer()
            self.ser.write((msg + "\n").encode("utf-8"))
            self.ser.flush()
            return self._read_response()
        except serial.SerialException as e:
            logger.error("Serial error sending '%s': %s", command, e)
            return None
        except Exception as e:
            logger.error("Error sending '%s': %s", command, e)
            return None

    def _read_response(self) -> dict | None:
        """Read and parse a JSON response from the device."""
        deadline = time.time() + self.TIMEOUT
        buf = ""
        brace_depth = 0
        in_json = False

        while time.time() < deadline:
            if self.ser.in_waiting > 0:
                chunk = self.ser.read(self.ser.in_waiting).decode("utf-8", errors="replace")
                for ch in chunk:
                    if ch == "{":
                        in_json = True
                        brace_depth += 1
                        buf += ch
                    elif in_json:
                        buf += ch
                        if ch == "{":
                            brace_depth += 1
                        elif ch == "}":
                            brace_depth -= 1
                            if brace_depth == 0:
                                try:
                                    return json.loads(buf)
                                except json.JSONDecodeError:
                                    logger.warning("Invalid JSON: %s", buf[:200])
                                    return None
            else:
                time.sleep(0.01)
        logger.warning("Response timeout")
        return None

    def hello(self) -> dict | None:
        return self.send_command("HELLO")

    def get_info(self) -> dict | None:
        return self.send_command("GET_INFO")

    def list_capabilities(self) -> dict | None:
        return self.send_command("LIST_CAPABILITIES")

    def list_pins(self) -> dict | None:
        return self.send_command("LIST_PINS")

    def set_pin_mode(self, pin: int, mode: str) -> dict | None:
        return self.send_command("SET_PIN_MODE", pin=pin, mode=mode)

    def write_pin(self, pin: int, value: int) -> dict | None:
        return self.send_command("WRITE_PIN", pin=pin, value=value)

    def read_pin(self, pin: int) -> dict | None:
        return self.send_command("READ_PIN", pin=pin)

    def test_pwm(self, pin: int) -> dict | None:
        return self.send_command("TEST_PWM", pin=pin)

    def test_adc(self, pin: int) -> dict | None:
        return self.send_command("TEST_ADC", pin=pin)

    def run_i2c_scan(self) -> dict | None:
        return self.send_command("RUN_I2C_SCAN")

    def run_spi_init(self) -> dict | None:
        return self.send_command("RUN_SPI_INIT")

    def run_uart_test(self) -> dict | None:
        return self.send_command("RUN_UART_TEST")

    def run_wifi_scan(self) -> dict | None:
        return self.send_command("RUN_WIFI_SCAN")

    def run_ble_init(self) -> dict | None:
        return self.send_command("RUN_BLE_INIT")

    def run_memory_test(self) -> dict | None:
        return self.send_command("RUN_MEMORY_TEST")

    def reboot(self) -> dict | None:
        return self.send_command("REBOOT")


class SSHCommandAdapter:
    """Execute commands on Raspberry Pi Linux devices via SSH."""

    def __init__(self, ssh_client) -> None:
        self.ssh = ssh_client

    def exec(self, command: str, timeout: float = 10.0) -> tuple[str, str, int]:
        """Execute a remote command. Returns (stdout, stderr, exit_code)."""
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            return stdout.read().decode(), stderr.read().decode(), exit_code
        except Exception as e:
            logger.error("SSH exec error: %s", e)
            return "", str(e), -1

    def get_system_info(self) -> dict:
        """Gather comprehensive system information."""
        info = {}
        commands = {
            "hostname": "hostname",
            "model": "cat /proc/device-tree/model 2>/dev/null || echo unknown",
            "os": "cat /etc/os-release 2>/dev/null | head -5",
            "kernel": "uname -r",
            "arch": "uname -m",
            "cpu_info": "lscpu | head -20",
            "memory": "free -m | head -3",
            "disk": "df -h / | tail -1",
            "temperature": "vcgencmd measure_temp 2>/dev/null || cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo N/A",
            "uptime": "uptime",
            "ip_addresses": "hostname -I 2>/dev/null || echo N/A",
        }
        for key, cmd in commands.items():
            stdout, _, _ = self.exec(cmd)
            info[key] = stdout.strip()
        return info

    def check_gpio(self) -> dict:
        """Check GPIO availability and interface status."""
        checks = {}
        gpio_commands = {
            "gpio_available": "ls /sys/class/gpio 2>/dev/null && echo yes || echo no",
            "gpiochip": "ls /dev/gpiochip* 2>/dev/null || echo none",
            "i2c_enabled": "ls /dev/i2c-* 2>/dev/null && echo yes || echo no",
            "spi_enabled": "ls /dev/spidev* 2>/dev/null && echo yes || echo no",
            "uart_enabled": "ls /dev/ttyAMA* /dev/ttyS* 2>/dev/null || echo none",
            "i2c_devices": "i2cdetect -y 1 2>/dev/null | tail -8 || echo N/A",
            "wifi_status": "iwconfig wlan0 2>/dev/null | head -5 || echo N/A",
            "bluetooth": "hciconfig 2>/dev/null | head -5 || echo N/A",
        }
        for key, cmd in gpio_commands.items():
            stdout, _, _ = self.exec(cmd)
            checks[key] = stdout.strip()
        return checks
