# Supported Devices

## ESP32 Family
| Board | MCU | USB Bridge | Status |
|-------|-----|-----------|--------|
| Generic ESP32 | ESP32 | CP2102/CH340 | Full Support |
| ESP32 DevKit V1 | ESP32-WROOM-32 | CP2102 | Full Support |
| ESP32-S2 | ESP32-S2 | Native USB | Profile Ready |
| ESP32-S3 | ESP32-S3 | Native USB | Profile Ready |
| ESP32-C3 | ESP32-C3 | Native USB | Profile Ready |

## Arduino Family
| Board | MCU | Tests Available |
|-------|-----|----------------|
| Arduino Uno | ATmega328P | GPIO, ADC, PWM, I2C, SPI, EEPROM |
| Arduino Nano | ATmega328P | GPIO, ADC, PWM, I2C, SPI, EEPROM |
| Arduino Mega 2560 | ATmega2560 | GPIO, ADC, PWM, I2C, SPI, UART x4, EEPROM |
| Arduino Leonardo | ATmega32U4 | GPIO, ADC, PWM, I2C, SPI |

## Raspberry Pi Pico
| Board | MCU | Features |
|-------|-----|----------|
| Raspberry Pi Pico | RP2040 | GPIO, ADC, PWM, I2C, SPI, UART |
| Raspberry Pi Pico W | RP2040 + CYW43439 | + Wi-Fi, Bluetooth |

## Raspberry Pi Linux
| Board | Connection | Tests |
|-------|-----------|-------|
| Raspberry Pi 3/4/5 | SSH | System info, GPIO check, I2C, SPI, UART, Wi-Fi, BT, Temp |

## Generic Serial
Any USB serial device is detected and basic connection testing is available.

## Adding New Devices
Create a new plugin in `device_plugins/` implementing the `DevicePlugin` interface.
Add a profile in `core/profiles/builtin_profiles.py`.
