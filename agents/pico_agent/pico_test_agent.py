"""
DeviceProbe - Raspberry Pi Pico Test Agent (MicroPython)

Upload this to your Pico running MicroPython to enable full testing.

Protocol: Serial JSON command/response
Baud: 115200
"""

import gc
import json
import sys
import time

import machine

AGENT_VERSION = "1.0.0"

# Try to import optional modules
try:
    from machine import ADC, PWM, Pin, I2C, SPI, UART
except ImportError:
    pass

try:
    import network
    HAS_WIFI = True
except ImportError:
    HAS_WIFI = False


def send_response(status, command, data=None):
    resp = {
        "status": status,
        "command": command,
        "device": "Pico",
        "data": data or {},
    }
    print(json.dumps(resp))


def send_ok(command, data=None):
    send_response("ok", command, data)


def send_error(command, error):
    resp = {
        "status": "error",
        "command": command,
        "error": error,
    }
    print(json.dumps(resp))


def parse_params(parts):
    params = {}
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            try:
                params[k] = int(v)
            except ValueError:
                params[k] = v
    return params


def handle_hello():
    send_ok("HELLO", {
        "agent": "pico_test_agent",
        "version": AGENT_VERSION,
        "uptime_ms": time.ticks_ms(),
    })


def handle_get_info():
    import os
    uname = os.uname()
    gc.collect()
    data = {
        "board": uname.machine,
        "sysname": uname.sysname,
        "release": uname.release,
        "version": uname.version,
        "cpu_freq_mhz": machine.freq() // 1_000_000,
        "free_mem": gc.mem_free(),
        "alloc_mem": gc.mem_alloc(),
        "unique_id": "".join("{:02x}".format(b) for b in machine.unique_id()),
    }
    send_ok("GET_INFO", data)


def handle_list_capabilities():
    caps = ["gpio", "adc", "pwm", "i2c", "spi", "uart"]
    if HAS_WIFI:
        caps.append("wifi")
    send_ok("LIST_CAPABILITIES", {"capabilities": caps})


def handle_set_pin_mode(params):
    pin_num = params.get("pin")
    mode = params.get("mode", "")
    if pin_num is None:
        send_error("SET_PIN_MODE", "Missing pin parameter")
        return

    if mode == "INPUT":
        Pin(pin_num, Pin.IN)
    elif mode == "OUTPUT":
        Pin(pin_num, Pin.OUT)
    elif mode == "INPUT_PULLUP":
        Pin(pin_num, Pin.IN, Pin.PULL_UP)
    elif mode == "INPUT_PULLDOWN":
        Pin(pin_num, Pin.IN, Pin.PULL_DOWN)
    else:
        send_error("SET_PIN_MODE", "Invalid mode: " + mode)
        return

    send_ok("SET_PIN_MODE", {"pin": pin_num, "mode": mode})


def handle_write_pin(params):
    pin_num = params.get("pin")
    value = params.get("value", 0)
    if pin_num is None:
        send_error("WRITE_PIN", "Missing pin")
        return

    p = Pin(pin_num, Pin.OUT)
    p.value(1 if value else 0)
    send_ok("WRITE_PIN", {"pin": pin_num, "value": value})


def handle_read_pin(params):
    pin_num = params.get("pin")
    if pin_num is None:
        send_error("READ_PIN", "Missing pin")
        return

    p = Pin(pin_num, Pin.IN)
    val = p.value()
    send_ok("READ_PIN", {"pin": pin_num, "value": val})


def handle_test_pwm(params):
    pin_num = params.get("pin")
    if pin_num is None:
        send_error("TEST_PWM", "Missing pin")
        return

    pwm = PWM(Pin(pin_num))
    pwm.freq(5000)
    pwm.duty_u16(32768)  # 50% duty
    time.sleep_ms(100)
    pwm.duty_u16(0)
    pwm.deinit()

    send_ok("TEST_PWM", {"pin": pin_num, "frequency": 5000, "duty_pct": 50})


def handle_test_adc(params):
    pin_num = params.get("pin")
    if pin_num is None:
        send_error("TEST_ADC", "Missing pin")
        return

    adc = ADC(Pin(pin_num))
    raw = adc.read_u16()
    voltage = (raw / 65535.0) * 3.3

    send_ok("TEST_ADC", {
        "pin": pin_num,
        "raw": raw,
        "voltage": round(voltage, 3),
        "resolution_bits": 16,
    })


def handle_i2c_scan():
    i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
    devices = i2c.scan()
    send_ok("RUN_I2C_SCAN", {
        "devices": ["0x{:02X}".format(d) for d in devices],
        "count": len(devices),
    })


def handle_spi_init():
    spi = SPI(0, baudrate=1000000, polarity=0, phase=0,
              sck=Pin(2), mosi=Pin(3), miso=Pin(0))
    spi.deinit()
    send_ok("RUN_SPI_INIT", {"spi_initialized": True})


def handle_uart_test():
    send_ok("RUN_UART_TEST", {
        "uart0": "in_use_for_agent",
        "uart1_available": True,
        "note": "UART1 available on GP4(TX)/GP5(RX)",
    })


def handle_wifi_scan():
    if not HAS_WIFI:
        send_error("RUN_WIFI_SCAN", "Wi-Fi not available on this board")
        return

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    networks = wlan.scan()

    net_list = []
    for net in networks[:15]:
        net_list.append({
            "ssid": net[0].decode() if isinstance(net[0], bytes) else net[0],
            "rssi": net[3],
            "channel": net[2],
        })

    send_ok("RUN_WIFI_SCAN", {
        "network_count": len(networks),
        "networks": net_list,
    })


def handle_memory_test():
    gc.collect()
    send_ok("RUN_MEMORY_TEST", {
        "free_mem": gc.mem_free(),
        "alloc_mem": gc.mem_alloc(),
        "total_mem": gc.mem_free() + gc.mem_alloc(),
    })


def handle_reboot():
    send_ok("REBOOT", {"rebooting": True})
    time.sleep_ms(100)
    machine.reset()


COMMANDS = {
    "HELLO": lambda p: handle_hello(),
    "GET_INFO": lambda p: handle_get_info(),
    "LIST_CAPABILITIES": lambda p: handle_list_capabilities(),
    "SET_PIN_MODE": handle_set_pin_mode,
    "WRITE_PIN": handle_write_pin,
    "READ_PIN": handle_read_pin,
    "TEST_PWM": handle_test_pwm,
    "TEST_ADC": handle_test_adc,
    "RUN_I2C_SCAN": lambda p: handle_i2c_scan(),
    "RUN_SPI_INIT": lambda p: handle_spi_init(),
    "RUN_UART_TEST": lambda p: handle_uart_test(),
    "RUN_WIFI_SCAN": lambda p: handle_wifi_scan(),
    "RUN_MEMORY_TEST": lambda p: handle_memory_test(),
    "REBOOT": lambda p: handle_reboot(),
}


def process_command(line):
    parts = line.strip().split()
    if not parts:
        return
    cmd = parts[0].upper()
    params = parse_params(parts[1:])

    handler = COMMANDS.get(cmd)
    if handler:
        try:
            handler(params)
        except Exception as e:
            send_error(cmd, str(e))
    else:
        send_error("UNKNOWN", "Unknown command: " + cmd)


def main():
    # Boot announcement
    send_ok("BOOT", {"agent": "pico_test_agent", "version": AGENT_VERSION})

    while True:
        try:
            line = sys.stdin.readline()
            if line:
                process_command(line)
        except KeyboardInterrupt:
            break
        except Exception as e:
            send_error("RUNTIME", str(e))


if __name__ == "__main__":
    main()
