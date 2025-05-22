# LED Control Script

This script controls an LED connected to a Raspberry Pi's GPIO pin.

## Hardware Setup

1.  Connect an LED to GPIO pin 17 (or the pin specified in `led_control.py`).
    *   Connect the longer leg (anode) of the LED to GPIO pin 17.
    *   Connect the shorter leg (cathode) of the LED to a resistor (e.g., 330 Ohms).
    *   Connect the other end of the resistor to a Ground (GND) pin on the Raspberry Pi.

## Running the Script

1.  Ensure you have the RPi.GPIO library installed. If not, install it using:
    ```bash
    pip install RPi.GPIO
    ```
2.  Run the script using Python:
    ```bash
    python led_control.py
    ```
    You might need to use `sudo python led_control.py` if you encounter permission issues.

## Script Overview

The `led_control.py` script will:
*   Initialize the GPIO pins.
*   Blink the LED connected to the specified pin 5 times with a 1-second interval.
*   Clean up the GPIO settings on exit.
