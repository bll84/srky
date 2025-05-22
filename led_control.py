import RPi.GPIO as GPIO
import time

# Set GPIO mode
GPIO.setmode(GPIO.BCM)

# Define LED pin
LED_PIN = 17

# Set up LED pin as output
GPIO.setup(LED_PIN, GPIO.OUT)

def led_on(pin):
    """Turns the LED on."""
    GPIO.output(pin, GPIO.HIGH)

def led_off(pin):
    """Turns the LED off."""
    GPIO.output(pin, GPIO.LOW)

if __name__ == "__main__":
    try:
        for _ in range(5):
            print("LED ON")
            led_on(LED_PIN)
            time.sleep(1)
            
            print("LED OFF")
            led_off(LED_PIN)
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()
        print("GPIO cleanup complete.")
