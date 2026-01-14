# Deneyap Kart 1A v2 - Pin Şeması ve Bağlantılar

Deneyap Kart 1A v2'nin tüm pinlerinin detaylı açıklaması ve bağlantı örnekleri.

## 📌 Genel Pin Bilgileri

### Teknik Özellikler
- **Toplam GPIO:** 23 adet
- **Analog Input (ADC):** 13 adet (12-bit, 0-3.3V)
- **PWM Çıkış:** 26 pin
- **Kapasitif Dokunma:** 9 pin
- **UART:** 2 port
- **SPI:** 1 port (HSPI)
- **I2C:** 1 port
- **I2S:** Destekli
- **DAC:** 2 kanal (GPIO25, GPIO26)

### Voltaj Seviyeleri
- **Logic Level:** 3.3V
- **Input Voltage (USB):** 5V
- **Maksimum Pin Akımı:** 40mA
- **Toplam Maksimum Akım:** 1.2A

⚠️ **UYARI:** 5V cihazları doğrudan bağlamayın! Level shifter kullanın.

---

## 🔌 Pin Layout

```
                    Deneyap Kart 1A v2
                   ┌─────────────────┐
              3V3 ─┤ 1          40 ├─ GND
     (A0)  GPIO36 ─┤ 2          39 ├─ GPIO4   (A10, T0)
     (A1)  GPIO39 ─┤ 3          38 ├─ GPIO0   (BOOT)
     (A2)  GPIO34 ─┤ 4          37 ├─ GPIO2   (A12, T2)
     (A3)  GPIO35 ─┤ 5          36 ├─ GPIO15  (A13, T3)
     (A4)  GPIO32 ─┤ 6          35 ├─ GPIO8   (SPI CS)
     (A5)  GPIO33 ─┤ 7          34 ├─ GPIO7   (SPI MOSI)
(DAC1,A6) GPIO25 ─┤ 8          33 ├─ GPIO6   (SPI CLK)
(DAC2,A7) GPIO26 ─┤ 9          32 ├─ GPIO5   (SPI MISO, T5)
     (A8)  GPIO27 ─┤10          31 ├─ GPIO3   (RX)
     (A9)  GPIO14 ─┤11          30 ├─ GPIO1   (TX, T1)
           GPIO12 ─┤12          29 ├─ GPIO13
    (SCL)  GPIO22 ─┤13          28 ├─ GPIO9   (T9)
    (SDA)  GPIO21 ─┤14          27 ├─ GPIO10  (T10)
            RX16 ─┤15          26 ├─ GPIO11  (T11)
            TX17 ─┤16          25 ├─ GPIO23
           GPIO16 ─┤17          24 ├─ GPIO19
           GPIO18 ─┤18          23 ├─ EN (RESET)
              GND ─┤19          22 ├─ GPIO37
              5V  ─┤20          21 ├─ GND
                   └─────────────────┘
                        [USB-C]
```

---

## 📊 Pin Özellikleri Tablosu

| GPIO | Analog | Touch | PWM | UART | SPI | I2C | Özel Fonksiyon | Notlar |
|------|--------|-------|-----|------|-----|-----|----------------|--------|
| 0    | ✓ (A10)| T0    | ✓   | -    | -   | -   | BOOT Button    | Boot modu |
| 1    | -      | T1    | ✓   | TX   | -   | -   | UART TX        | Serial |
| 2    | ✓ (A12)| T2    | ✓   | -    | -   | -   | LED_BUILTIN    | Yerleşik LED |
| 3    | -      | -     | ✓   | RX   | -   | -   | UART RX        | Serial |
| 4    | ✓ (A10)| T0    | ✓   | -    | -   | -   | -              | |
| 5    | -      | T5    | ✓   | -    | MISO| -   | SPI MISO       | |
| 6    | -      | -     | ✓   | -    | CLK | -   | SPI CLK        | |
| 7    | -      | -     | ✓   | -    | MOSI| -   | SPI MOSI       | |
| 8    | -      | -     | ✓   | -    | CS  | -   | SPI CS         | |
| 9    | -      | T9    | ✓   | -    | -   | -   | -              | |
| 10   | -      | T10   | ✓   | -    | -   | -   | -              | |
| 11   | -      | T11   | ✓   | -    | -   | -   | -              | |
| 12   | -      | -     | ✓   | -    | -   | -   | -              | |
| 13   | -      | -     | ✓   | -    | -   | -   | -              | |
| 14   | ✓ (A8) | -     | ✓   | -    | -   | -   | -              | |
| 15   | ✓ (A13)| T3    | ✓   | -    | -   | -   | -              | |
| 16   | -      | -     | ✓   | RX2  | -   | -   | UART2 RX       | |
| 17   | -      | -     | ✓   | TX2  | -   | -   | UART2 TX       | |
| 18   | -      | -     | ✓   | -    | -   | -   | -              | |
| 19   | -      | -     | ✓   | -    | -   | -   | -              | |
| 21   | -      | -     | ✓   | -    | -   | SDA | I2C SDA        | |
| 22   | -      | -     | ✓   | -    | -   | SCL | I2C SCL        | |
| 23   | -      | -     | ✓   | -    | -   | -   | -              | |
| 25   | ✓ (A6) | -     | ✓   | -    | -   | -   | DAC1           | Analog çıkış |
| 26   | ✓ (A7) | -     | ✓   | -    | -   | -   | DAC2           | Analog çıkış |
| 27   | ✓ (A8) | -     | ✓   | -    | -   | -   | -              | |
| 32   | ✓ (A4) | -     | ✓   | -    | -   | -   | -              | |
| 33   | ✓ (A5) | -     | ✓   | -    | -   | -   | -              | |
| 34   | ✓ (A2) | -     | -   | -    | -   | -   | INPUT ONLY     | No pullup |
| 35   | ✓ (A3) | -     | -   | -    | -   | -   | INPUT ONLY     | No pullup |
| 36   | ✓ (A0) | -     | -   | -    | -   | -   | INPUT ONLY     | No pullup |
| 39   | ✓ (A1) | -     | -   | -    | -   | -   | INPUT ONLY     | No pullup |

---

## 🔌 Bağlantı Örnekleri

### 1. LED Bağlantısı

```
GPIO13 ─── 220Ω ─── LED Anode (+)
                    LED Cathode (-)
                         │
                        GND
```

**Kod:**
```cpp
pinMode(13, OUTPUT);
digitalWrite(13, HIGH);  // LED yanar
```

---

### 2. Buton Bağlantısı (Pull-up)

```
              ┌── 3.3V
              │
             10kΩ (Pull-up)
              │
GPIO15 ───────┼─── Buton ─── GND
```

**Kod:**
```cpp
pinMode(15, INPUT_PULLUP);
int buttonState = digitalRead(15);
// Basılı: LOW, Basılı değil: HIGH
```

---

### 3. Röle Modülü

```
Röle VCC ──── 3.3V (veya 5V)
Röle GND ──── GND
Röle IN  ──── GPIO12
```

**Kod:**
```cpp
pinMode(12, OUTPUT);
digitalWrite(12, HIGH);  // Röle aktif
delay(5000);
digitalWrite(12, LOW);   // Röle pasif
```

⚠️ **Not:** Yüksek akımlı röleler için transistör/optocoupler kullanın.

---

### 4. Toprak Nem Sensörü (Analog)

```
Sensör VCC ──── 3.3V
Sensör GND ──── GND
Sensör AO  ──── GPIO36 (A0)
```

**Kod:**
```cpp
int soilMoisture = analogRead(36);  // 0-4095
float voltage = (soilMoisture / 4095.0) * 3.3;
int percent = map(soilMoisture, 0, 4095, 0, 100);
```

---

### 5. LDR (Işık Sensörü)

```
       3.3V
         │
        LDR
         │
GPIO39 ──┼─── 10kΩ ─── GND
```

**Kod:**
```cpp
int lightLevel = analogRead(39);
if (lightLevel < 1000) {
  // Karanlık, LED'i aç
  digitalWrite(13, HIGH);
}
```

---

### 6. DHT22 (Sıcaklık/Nem Sensörü)

```
DHT22 VCC ──── 3.3V
DHT22 DATA ─── GPIO4 ─── 4.7kΩ Pull-up ─── 3.3V
DHT22 GND ──── GND
```

**Kod:**
```cpp
#include <DHT.h>
DHT dht(4, DHT22);

dht.begin();
float temp = dht.readTemperature();
float humidity = dht.readHumidity();
```

---

### 7. I2C OLED Display (SSD1306)

```
OLED VCC ──── 3.3V
OLED GND ──── GND
OLED SCL ──── GPIO22 (I2C SCL)
OLED SDA ──── GPIO21 (I2C SDA)
```

**Kod:**
```cpp
#include <Wire.h>
#include <Adafruit_SSD1306.h>

Adafruit_SSD1306 display(128, 64, &Wire);
display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
display.println("Deneyap Kart");
display.display();
```

---

### 8. Servo Motor

```
Servo Orange (Signal) ──── GPIO23
Servo Red (VCC) ────────── 5V (Harici güç önerilir)
Servo Brown (GND) ───────── GND
```

**Kod:**
```cpp
#include <ESP32Servo.h>

Servo myServo;
myServo.attach(23);
myServo.write(90);  // 90 derece
```

---

### 9. Kapasitif Dokunma

```
GPIO4 (T0) ──── 1MΩ ──── Bakır Folyo
```

**Kod:**
```cpp
int touchValue = touchRead(T0);  // T0 = GPIO4
if (touchValue < 40) {
  // Dokunuldu!
}
```

---

### 10. RGB LED (Common Cathode)

```
GPIO25 (R) ─── 220Ω ─── Red Anode
GPIO26 (G) ─── 220Ω ─── Green Anode
GPIO27 (B) ─── 220Ω ─── Blue Anode
GND ───────────────── Common Cathode
```

**Kod (PWM):**
```cpp
ledcSetup(0, 5000, 8);  // Kanal 0, 5kHz, 8-bit
ledcSetup(1, 5000, 8);  // Kanal 1
ledcSetup(2, 5000, 8);  // Kanal 2

ledcAttachPin(25, 0);  // R
ledcAttachPin(26, 1);  // G
ledcAttachPin(27, 2);  // B

// Mor renk
ledcWrite(0, 255);  // Red
ledcWrite(1, 0);    // Green
ledcWrite(2, 255);  // Blue
```

---

## ⚠️ Önemli Notlar

### Kullanılmaması Gereken Pinler

| Pin | Neden |
|-----|-------|
| GPIO0 | BOOT butonu, LOW ise boot modu |
| GPIO1 | Serial TX (debugging için gerekli) |
| GPIO3 | Serial RX (debugging için gerekli) |
| GPIO34-39 | Sadece INPUT, OUTPUT yapılamaz |

### Strapping Pinler

Bu pinler boot sırasında özel anlamlara sahiptir:
- **GPIO0:** LOW = Download mode, HIGH = Normal boot
- **GPIO2:** Boot sırasında floating olmalı

### Boot Sırasında Kaçının

- GPIO12: LOW olmalı (3.3V flash için)
- GPIO15: HIGH olmalı
- GPIO2: Floating

### Maksimum Akım

- **Pin başına:** 40mA
- **Tüm GPIO'lar toplam:** 1200mA
- Yüksek akım için transistör/MOSFET kullanın

---

## 🔧 İpuçları

### 1. Pull-up/Pull-down Dirençleri

```cpp
pinMode(pin, INPUT_PULLUP);   // Dahili pull-up aktif
pinMode(pin, INPUT_PULLDOWN); // Dahili pull-down aktif
```

### 2. ADC Kalibrasyonu

ADC okumaları tam doğru olmayabilir, kalibrasyon gerekebilir:

```cpp
// Ham okuma
int raw = analogRead(36);

// Kalibrasyon
float calibrated = raw * CALIB_FACTOR + CALIB_OFFSET;
```

### 3. PWM Frekans Seçimi

- **LED dimming:** 5000 Hz
- **Servo motor:** 50 Hz
- **Motor kontrol:** 20000 Hz (20 kHz)

### 4. Electrostatic Discharge (ESD) Koruması

GPIO pinleri ESD'ye duyarlıdır. Üretim kartlarında:
- TVS diyotları kullanın
- Uygun topraklama yapın
- Kablo uzunluklarını minimumda tutun

---

## 📚 Kaynaklar

- [ESP32-S3 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)
- [Deneyap Kart Pinout Resmi](https://deneyapkart.org)
- [ESP32 Pin Reference](https://randomnerdtutorials.com/esp32-pinout-reference-gpios/)

---

**Önceki:** [API Dokümantasyonu](api.md) | **Ana Sayfa:** [README](../README.md)
