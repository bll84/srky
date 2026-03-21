#!/usr/bin/env python3
"""
DeviceProbe - Raspberry Pi Linux Diagnostic Agent

Deploy this script to your Raspberry Pi for enhanced local testing.
Can be run directly or invoked via SSH by the DeviceProbe desktop app.

Usage:
    python3 rpi_diagnostic_agent.py              # Interactive mode
    python3 rpi_diagnostic_agent.py --json        # JSON output mode
    python3 rpi_diagnostic_agent.py --test-all    # Run all tests
    python3 rpi_diagnostic_agent.py --test gpio   # Run specific test
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


AGENT_VERSION = "1.0.0"


def run_cmd(cmd: str, timeout: float = 10.0) -> tuple[str, int]:
    """Run a shell command and return (output, exit_code)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", -1
    except Exception as e:
        return str(e), -1


def get_model() -> dict:
    model, _ = run_cmd("cat /proc/device-tree/model 2>/dev/null")
    model = model.rstrip("\x00")
    return {
        "test": "model",
        "result": "PASS" if model else "WARNING",
        "data": {"model": model or "unknown"},
    }


def get_system_info() -> dict:
    hostname, _ = run_cmd("hostname")
    kernel, _ = run_cmd("uname -r")
    arch, _ = run_cmd("uname -m")
    uptime, _ = run_cmd("uptime -p 2>/dev/null || uptime")

    os_info = {}
    os_release, code = run_cmd("cat /etc/os-release")
    if code == 0:
        for line in os_release.split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                os_info[k] = v.strip('"')

    return {
        "test": "system_info",
        "result": "PASS",
        "data": {
            "hostname": hostname,
            "kernel": kernel,
            "arch": arch,
            "uptime": uptime,
            "os_name": os_info.get("PRETTY_NAME", "unknown"),
            "os_id": os_info.get("ID", "unknown"),
        },
    }


def get_cpu_info() -> dict:
    cpu_model, _ = run_cmd("lscpu | grep 'Model name' | sed 's/.*: *//'")
    cpu_count, _ = run_cmd("nproc")
    cpu_freq, _ = run_cmd("lscpu | grep 'CPU max MHz' | sed 's/.*: *//' || cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq 2>/dev/null")

    return {
        "test": "cpu",
        "result": "PASS",
        "data": {
            "model": cpu_model,
            "cores": cpu_count,
            "max_freq": cpu_freq,
        },
    }


def get_memory_info() -> dict:
    mem_out, _ = run_cmd("free -m")
    lines = mem_out.split("\n")
    data = {}
    if len(lines) >= 2:
        parts = lines[1].split()
        if len(parts) >= 3:
            data["total_mb"] = int(parts[1])
            data["used_mb"] = int(parts[2])
            data["free_mb"] = int(parts[3]) if len(parts) > 3 else 0

    return {
        "test": "memory",
        "result": "PASS",
        "data": data,
    }


def get_storage_info() -> dict:
    df_out, _ = run_cmd("df -h / | tail -1")
    parts = df_out.split()
    data = {}
    if len(parts) >= 5:
        data["total"] = parts[1]
        data["used"] = parts[2]
        data["available"] = parts[3]
        data["use_pct"] = parts[4]

    return {
        "test": "storage",
        "result": "PASS",
        "data": data,
    }


def get_temperature() -> dict:
    temp_str, code = run_cmd("vcgencmd measure_temp 2>/dev/null")
    if code != 0 or not temp_str:
        temp_raw, code = run_cmd("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null")
        if code == 0 and temp_raw:
            try:
                temp_c = int(temp_raw) / 1000.0
                temp_str = f"{temp_c:.1f}'C"
            except ValueError:
                temp_str = "N/A"

    result = "PASS"
    try:
        if "=" in temp_str:
            val = float(temp_str.split("=")[1].replace("'C", ""))
        elif "'C" in temp_str:
            val = float(temp_str.replace("'C", ""))
        else:
            val = 0
        if val > 80:
            result = "WARNING"
    except (ValueError, IndexError):
        pass

    return {
        "test": "temperature",
        "result": result,
        "data": {"temperature": temp_str},
    }


def check_gpio() -> dict:
    gpiochip, _ = run_cmd("ls /dev/gpiochip* 2>/dev/null")
    sysfs, _ = run_cmd("ls /sys/class/gpio 2>/dev/null")

    # Check for GPIO libraries
    rpigpio, _ = run_cmd("python3 -c 'import RPi.GPIO' 2>&1")
    gpiozero, _ = run_cmd("python3 -c 'import gpiozero' 2>&1")
    lgpio, _ = run_cmd("python3 -c 'import lgpio' 2>&1")

    available = bool(gpiochip) or bool(sysfs)

    return {
        "test": "gpio",
        "result": "PASS" if available else "WARNING",
        "data": {
            "gpiochip_devices": gpiochip.split() if gpiochip else [],
            "sysfs_available": bool(sysfs),
            "rpigpio_available": "Error" not in rpigpio and "No module" not in rpigpio,
            "gpiozero_available": "Error" not in gpiozero and "No module" not in gpiozero,
            "lgpio_available": "Error" not in lgpio and "No module" not in lgpio,
        },
    }


def check_i2c() -> dict:
    devices, code = run_cmd("ls /dev/i2c-* 2>/dev/null")
    enabled = code == 0 and bool(devices)
    data = {"enabled": enabled, "devices": devices.split() if devices else []}

    if enabled:
        scan, _ = run_cmd("i2cdetect -y 1 2>/dev/null")
        data["scan"] = scan

    return {
        "test": "i2c",
        "result": "PASS" if enabled else "WARNING",
        "data": data,
        "recommendation": "" if enabled else "Enable I2C via raspi-config",
    }


def check_spi() -> dict:
    devices, code = run_cmd("ls /dev/spidev* 2>/dev/null")
    enabled = code == 0 and bool(devices)

    return {
        "test": "spi",
        "result": "PASS" if enabled else "WARNING",
        "data": {"enabled": enabled, "devices": devices.split() if devices else []},
        "recommendation": "" if enabled else "Enable SPI via raspi-config",
    }


def check_uart() -> dict:
    devices, _ = run_cmd("ls /dev/ttyAMA* /dev/ttyS* 2>/dev/null")
    return {
        "test": "uart",
        "result": "PASS" if devices else "WARNING",
        "data": {"devices": devices.split() if devices else []},
    }


def check_wifi() -> dict:
    out, code = run_cmd("iwconfig wlan0 2>/dev/null")
    connected = "ESSID" in out and "off/any" not in out
    ssid = ""
    if "ESSID:" in out:
        try:
            ssid = out.split("ESSID:")[1].split('"')[1]
        except (IndexError, ValueError):
            pass

    return {
        "test": "wifi",
        "result": "PASS" if connected else "WARNING",
        "data": {"interface": "wlan0", "connected": connected, "ssid": ssid},
    }


def check_bluetooth() -> dict:
    out, code = run_cmd("hciconfig 2>/dev/null")
    available = "hci0" in out.lower() if out else False

    bt_status, _ = run_cmd("bluetoothctl show 2>/dev/null | head -10")

    return {
        "test": "bluetooth",
        "result": "PASS" if available else "WARNING",
        "data": {"available": available, "status": bt_status[:200] if bt_status else ""},
    }


def check_services() -> dict:
    services = ["ssh", "networking", "bluetooth", "avahi-daemon", "cron"]
    results = {}
    for svc in services:
        out, _ = run_cmd(f"systemctl is-active {svc} 2>/dev/null")
        results[svc] = out

    return {
        "test": "services",
        "result": "PASS",
        "data": {"services": results},
    }


def check_ip_addresses() -> dict:
    ips, _ = run_cmd("hostname -I 2>/dev/null")
    return {
        "test": "network",
        "result": "PASS" if ips else "WARNING",
        "data": {"ip_addresses": ips.split() if ips else []},
    }


# Test registry
ALL_TESTS = {
    "model": get_model,
    "system_info": get_system_info,
    "cpu": get_cpu_info,
    "memory": get_memory_info,
    "storage": get_storage_info,
    "temperature": get_temperature,
    "gpio": check_gpio,
    "i2c": check_i2c,
    "spi": check_spi,
    "uart": check_uart,
    "wifi": check_wifi,
    "bluetooth": check_bluetooth,
    "services": check_services,
    "network": check_ip_addresses,
}


def run_all_tests() -> list[dict]:
    results = []
    for name, func in ALL_TESTS.items():
        try:
            result = func()
            results.append(result)
        except Exception as e:
            results.append({
                "test": name,
                "result": "ERROR",
                "data": {"error": str(e)},
            })
    return results


def run_single_test(name: str) -> dict:
    func = ALL_TESTS.get(name)
    if not func:
        return {"test": name, "result": "ERROR", "data": {"error": f"Unknown test: {name}"}}
    try:
        return func()
    except Exception as e:
        return {"test": name, "result": "ERROR", "data": {"error": str(e)}}


def interactive_mode():
    """Interactive command mode for SSH integration."""
    print(json.dumps({
        "status": "ok", "command": "BOOT",
        "device": "RaspberryPi",
        "data": {"agent": "rpi_diagnostic_agent", "version": AGENT_VERSION}
    }))

    while True:
        try:
            line = input().strip()
            if not line:
                continue

            parts = line.split()
            cmd = parts[0].upper()

            if cmd == "HELLO":
                print(json.dumps({"status": "ok", "command": "HELLO",
                                   "data": {"agent": "rpi_diagnostic_agent", "version": AGENT_VERSION}}))
            elif cmd == "GET_INFO":
                info = {**get_model()["data"], **get_system_info()["data"]}
                print(json.dumps({"status": "ok", "command": "GET_INFO", "data": info}))
            elif cmd == "RUN_TEST":
                test_name = parts[1] if len(parts) > 1 else "all"
                if test_name == "all":
                    results = run_all_tests()
                else:
                    results = [run_single_test(test_name)]
                print(json.dumps({"status": "ok", "command": "RUN_TEST", "data": {"results": results}}))
            elif cmd == "LIST_TESTS":
                print(json.dumps({"status": "ok", "command": "LIST_TESTS",
                                   "data": {"tests": list(ALL_TESTS.keys())}}))
            elif cmd == "EXIT" or cmd == "QUIT":
                break
            else:
                print(json.dumps({"status": "error", "command": cmd, "error": "Unknown command"}))

        except EOFError:
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))


def main():
    parser = argparse.ArgumentParser(description="DeviceProbe Raspberry Pi Diagnostic Agent")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--test-all", action="store_true", help="Run all diagnostic tests")
    parser.add_argument("--test", type=str, help="Run a specific test")
    parser.add_argument("--list-tests", action="store_true", help="List available tests")
    parser.add_argument("--interactive", action="store_true", help="Interactive command mode")
    args = parser.parse_args()

    if args.list_tests:
        for name in ALL_TESTS:
            print(name)
        return

    if args.interactive or (not args.test_all and not args.test):
        interactive_mode()
        return

    if args.test:
        result = run_single_test(args.test)
        results = [result]
    else:
        results = run_all_tests()

    if args.json:
        report = {
            "agent": "rpi_diagnostic_agent",
            "version": AGENT_VERSION,
            "results": results,
            "summary": {
                "total": len(results),
                "pass": sum(1 for r in results if r["result"] == "PASS"),
                "warning": sum(1 for r in results if r["result"] == "WARNING"),
                "fail": sum(1 for r in results if r["result"] == "FAIL"),
                "error": sum(1 for r in results if r["result"] == "ERROR"),
            },
        }
        print(json.dumps(report, indent=2))
    else:
        print("=" * 60)
        print("  Raspberry Pi Diagnostic Report")
        print("=" * 60)
        for r in results:
            icon = {"PASS": "[PASS]", "WARNING": "[WARN]", "FAIL": "[FAIL]", "ERROR": "[ERR]"}.get(r["result"], "[????]")
            print(f"  {icon} {r['test']}")
            for k, v in r.get("data", {}).items():
                if isinstance(v, (list, dict)):
                    v = json.dumps(v)
                print(f"         {k}: {v}")
            if r.get("recommendation"):
                print(f"         Rec: {r['recommendation']}")
            print()
        print("=" * 60)


if __name__ == "__main__":
    main()
