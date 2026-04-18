# LED Kontrol Script'i

Bu script, Raspberry Pi'nin GPIO pinine bağlı bir LED'i kontrol eder.

## Donanım Kurulumu

1.  LED'i GPIO pin 17'ye (veya `led_control.py` içinde belirtilen pine) bağlayın.
    *   LED'in uzun bacağını (anot) GPIO pin 17'ye bağlayın.
    *   LED'in kısa bacağını (katot) bir dirence (örn. 330 Ohm) bağlayın.
    *   Direncin diğer ucunu Raspberry Pi'deki bir Toprak (GND) pinine bağlayın.

## Script'i Çalıştırma

1.  RPi.GPIO kütüphanesinin kurulu olduğundan emin olun. Kurulu değilse şu komutla yükleyin:
    ```bash
    pip install RPi.GPIO
    ```
2.  Script'i Python ile çalıştırın:
    ```bash
    python led_control.py
    ```
    İzin sorunu yaşarsanız `sudo python led_control.py` kullanmanız gerekebilir.

## Script'e Genel Bakış

`led_control.py` script'i şunları yapar:
*   GPIO pinlerini başlatır.
*   Belirtilen pine bağlı LED'i 1 saniye aralıklarla 5 kez yakıp söndürür.
*   Çıkışta GPIO ayarlarını temizler.
