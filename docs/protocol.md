# DeviceProbe Communication Protocol

## Overview
DeviceProbe uses a text-based command/response protocol over serial (USB) or SSH.

## Serial Protocol

### Commands (Host → Device)
```
COMMAND [param=value param=value ...]
```

### Response (Device → Host)
```json
{"status":"ok","command":"COMMAND","device":"DeviceType","data":{...}}
```

### Error Response
```json
{"status":"error","command":"COMMAND","error":"Description"}
```

## Command Reference

| Command | Parameters | Description |
|---------|-----------|-------------|
| HELLO | - | Check agent presence |
| GET_INFO | - | Get device info |
| LIST_CAPABILITIES | - | List supported features |
| LIST_PINS | - | List pin configuration |
| SET_PIN_MODE | pin, mode | Set pin mode (INPUT/OUTPUT/INPUT_PULLUP) |
| WRITE_PIN | pin, value | Write digital value (0/1) |
| READ_PIN | pin | Read digital value |
| TEST_PWM | pin | Test PWM on pin |
| TEST_ADC | pin | Read ADC value |
| RUN_I2C_SCAN | - | Scan I2C bus |
| RUN_SPI_INIT | - | Initialize SPI |
| RUN_UART_TEST | - | Test UART |
| RUN_WIFI_SCAN | - | Scan Wi-Fi networks |
| RUN_BLE_INIT | - | Initialize BLE |
| RUN_MEMORY_TEST | - | Check memory |
| REBOOT | - | Reboot device |

## SSH Protocol (Raspberry Pi Linux)
Standard shell commands executed via SSH. The optional diagnostic agent
provides the same JSON protocol via stdin/stdout.

## Safety Rules
- Never drive reserved/boot pins without explicit user confirmation
- Flash-connected pins (ESP32 GPIO 6-11) are never tested
- Boot pins are marked WARNING, not automatically tested
- 3.3V/5V logic level differences are documented per profile
