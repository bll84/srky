# DeviceProbe - Setup Guide

## Requirements
- Python 3.10+
- pip

## Desktop Application Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Device Agent Setup

### ESP32 Agent
1. Open `agents/esp32_agent/esp32_test_agent.ino` in Arduino IDE or PlatformIO
2. Install ArduinoJson library (v6+)
3. Select your ESP32 board
4. Flash the sketch
5. Set baud rate to 115200

### Arduino Agent
1. Open `agents/arduino_agent/arduino_test_agent.ino` in Arduino IDE
2. Select your board (Uno/Nano/Mega)
3. Flash the sketch
4. Set baud rate to 115200

### Raspberry Pi Pico Agent
1. Flash MicroPython to your Pico
2. Copy `agents/pico_agent/pico_test_agent.py` to the Pico as `main.py`
3. The agent starts automatically on boot

### Raspberry Pi (Linux) Agent
Option A - Direct SSH (no agent needed):
- DeviceProbe connects via SSH and runs commands directly

Option B - Enhanced diagnostics:
```bash
# Copy to your Pi
scp agents/rpi_agent/rpi_diagnostic_agent.py pi@raspberrypi.local:~/

# Run on Pi
python3 rpi_diagnostic_agent.py --test-all --json
```

## Troubleshooting

### Serial port access (Linux)
```bash
sudo usermod -a -G dialout $USER
# Logout and login again
```

### macOS serial permissions
Grant terminal app access in System Settings > Privacy & Security > Developer Tools

### Windows COM port
Install the appropriate USB driver:
- CP210x: Silicon Labs driver
- CH340: WCH driver
- FTDI: FTDI VCP driver
