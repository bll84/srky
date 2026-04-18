import RPi.GPIO as GPIO
import time

# GPIO modunu ayarla
GPIO.setmode(GPIO.BCM)

# LED pinini tanımla
LED_PIN = 17

# LED pinini çıkış olarak ayarla
GPIO.setup(LED_PIN, GPIO.OUT)

def led_yak(pin):
    """LED'i yakar."""
    GPIO.output(pin, GPIO.HIGH)

def led_sondur(pin):
    """LED'i söndürür."""
    GPIO.output(pin, GPIO.LOW)

if __name__ == "__main__":
    try:
        for _ in range(5):
            print("LED AÇIK")
            led_yak(LED_PIN)
            time.sleep(1)

            print("LED KAPALI")
            led_sondur(LED_PIN)
            time.sleep(1)

    except KeyboardInterrupt:
        print("Çıkılıyor...")
    finally:
        GPIO.cleanup()
        print("GPIO temizleme tamamlandı.")
