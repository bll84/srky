# Safety Guidelines

## Voltage Levels
- **ESP32**: 3.3V logic. Do NOT connect to 5V signals directly.
- **Arduino Uno/Nano/Mega**: 5V logic. Use level shifters with 3.3V devices.
- **Raspberry Pi Pico**: 3.3V logic. 5V tolerant on VBUS only.
- **Raspberry Pi GPIO**: 3.3V logic. 5V on GPIO WILL DAMAGE the SoC.

## Reserved Pins
Each device profile marks pins as:
- **Reserved**: Used by USB/serial communication, do not test
- **Boot pins**: Affect boot behavior, test with caution
- **Unsafe pins**: Connected to internal flash or critical peripherals

## Physical Testing Limitations
Software tests verify:
- Firmware responds to pin commands correctly
- Internal peripherals initialize successfully
- Communication protocols are functional

Software tests CANNOT verify:
- Physical solder quality
- Actual electrical output on pins
- External circuit connections
- Damaged traces or broken connections

For physical verification, use loopback tests (jumper wire between two pins).

## Loopback Testing
1. The application will specify which two pins to connect
2. Use a jumper wire between the specified pins
3. The test writes to one pin and reads from the other
4. PASS = signal propagates correctly
5. Always remove jumpers after testing

## Best Practices
- Never connect pins to external circuits during automated testing
- Disconnect all peripherals before running full GPIO tests
- Review pin matrix for reserved/boot pins before physical testing
- Use current-limiting resistors when testing with LEDs
- Never short VCC to GND
