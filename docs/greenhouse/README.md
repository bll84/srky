# 🌱 Akıllı Sera Otomasyonu

Deneyap Kart 1A v2 tabanlı, tam otomatik sera yönetim sistemi.

## 📋 Genel Bakış

Bu sistem, seranızdaki tüm kritik parametreleri 24/7 izler ve otomatik olarak kontrol eder:

- 🌡️ **Sıcaklık & Nem İzleme** (DHT22)
- 💧 **4 Zonlu Toprak Nem Takibi**
- ☀️ **Işık Seviyesi Ölçümü** (LDR)
- 💦 **Otomatik Sulama Sistemi** (4 zone)
- 🌀 **Akıllı Havalandırma** (Fan + Pencere)
- 🔥 **Isıtma/Soğutma Kontrolü**
- 💡 **Bitki Aydınlatma Sistemi**
- 📱 **n8n Otomasyon Entegrasyonu**
- 🔔 **Telegram/Email Alarmları**

## 🎯 Özellikler

### Otomatik Kontrol Sistemleri

#### 1. Akıllı Sulama
- 4 bağımsız sulama zone'u
- Toprak nem seviyesine göre otomatik sulama
- Sıcaklık/nem koşullarına göre sulama süresi ayarlama
- Gece sulamayı otomatik erteleme
- Zone bazlı sulama zamanı optimizasyonu

#### 2. İklim Kontrolü
- Hedef sıcaklık ayarı (histerezis kontrolü ile)
- Otomatik ısıtıcı/soğutucu aktivasyonu
- Çakışma önleme (ısıtıcı ve soğutucu aynı anda çalışmaz)
- Enerji tasarrufu modu

#### 3. Havalandırma Sistemi
- PWM kontrollü değişken hızlı fan
- Servo motor ile otomatik pencere kontrolü
- Sıcaklık ve nem bazlı otomatik havalandırma
- Üç seviye havalandırma (düşük/orta/yüksek)

#### 4. Aydınlatma Kontrolü
- Bitki büyütme lambası (grow light)
- PWM ile parlaklık kontrolü
- Gündüz/gece döngüsü uyumlu
- Doğal ışık yetersizse otomatik devreye girer

### Sensörler ve İzleme

#### DHT22 - Sıcaklık/Nem
- Hassas sıcaklık ölçümü (±0.5°C)
- Nem ölçümü (±2%)
- Heat index hesaplama
- Alarm eşikleri (15-35°C, %40-80)

#### Toprak Nem Sensörleri (4 Zone)
- Bağımsız zone takibi
- Yüzdelik nem hesaplama
- Zone bazlı sulama ihtiyacı tespiti
- Özelleştirilebilir zone isimleri

#### LDR - Işık Sensörü
- Doğal ışık seviyesi ölçümü
- Günlük ışık integral (DLI) hesaplama
- Gündüz/gece tespiti
- Yapay aydınlatma ihtiyacı analizi

## 🔌 Donanım Gereksinimleri

### Zorunlu Bileşenler

| Bileşen | Model | Bağlantı | Açıklama |
|---------|-------|----------|----------|
| Ana Kart | Deneyap Kart 1A v2 | - | ESP32-S3 tabanlı |
| Sıcaklık/Nem | DHT22 | GPIO 4 | Kırmızı sensör |
| Toprak Nem x4 | Capacitive Soil | A0-A3 | Paslanmaz tip önerilir |
| Işık Sensörü | LDR + 10kΩ | A1 | Fotoresistör |
| Röle Modülü x4 | 5V Relay | GPIO 12-15 | Sulama valve'leri |
| Fan | 12V DC Fan | GPIO 25 (PWM) | Havalandırma |
| Servo Motor | SG90 | GPIO 26 | Pencere açma |
| Isıtıcı Röle | 5V Relay | GPIO 27 | 100-500W ısıtıcı |
| Soğutucu Röle | 5V Relay | GPIO 32 | Fan/klima |
| Grow Light | LED Strip | GPIO 33 (PWM) | 12V LED |

### Opsiyonel Bileşenler

- **LCD Ekran** (16x2 I2C) - Lokal durum gösterimi
- **SD Kart Modülü** - Offline veri loglama
- **RTC Modülü** (DS3231) - Hassas zaman takibi
- **CO2 Sensörü** (MH-Z19) - Karbondioksit ölçümü
- **Water Flow Sensor** - Su tüketimi takibi

## 📦 Yazılım Gereksinimleri

### Arduino IDE Kütüphaneleri

```bash
# Library Manager'dan kurun:
- DHT sensor library (by Adafruit)
- Adafruit Unified Sensor
- PubSubClient (MQTT)
- ArduinoJson
- WiFi (built-in)
- ESP32Servo
```

### n8n Kurulumu

```bash
# Docker ile (önerilen)
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  --network host \
  n8nio/n8n

# Tarayıcıda aç
http://localhost:5678
```

### MQTT Broker

```bash
# Mosquitto kurulumu (Ubuntu/Debian)
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto

# Test
mosquitto_sub -t "greenhouse/#"
```

## 🚀 Hızlı Başlangıç

### 1. Donanım Montajı

[Detaylı bağlantı şeması için: `wiring-diagram.md`](wiring-diagram.md)

**Temel Bağlantılar:**

```
DHT22:
  VCC -> 3.3V
  DATA -> GPIO 4
  GND -> GND

Toprak Nem Zone 1:
  VCC -> 3.3V
  AOUT -> A0 (GPIO 36)
  GND -> GND

Röle Modülü (Sulama Zone 1):
  VCC -> 5V
  IN -> GPIO 12
  GND -> GND
```

### 2. Firmware Yükleme

1. Arduino IDE'yi açın
2. `firmware/greenhouse/greenhouse.ino` dosyasını açın
3. WiFi ve MQTT ayarlarını düzenleyin:

```cpp
#define WIFI_SSID "sizin_wifi"
#define WIFI_PASSWORD "sizin_sifre"
#define MQTT_BROKER "192.168.1.100"
```

4. Board: **Deneyap Kart 1A v2** seçin
5. Port'u seçin ve Upload edin

### 3. İlk Çalıştırma

Serial Monitor'ü açın (115200 baud):

```
╔══════════════════════════════════════╗
║   Akıllı Deneyap Sistemi             ║
║   SERA OTOMASYONU v1.0               ║
╚══════════════════════════════════════╝

📡 Sensörler başlatılıyor...
✓ DHT22 sensörü başlatıldı
✓ Toprak nem sensörleri başlatıldı (4 zone)
✓ Işık sensörü (LDR) başlatıldı

🎮 Kontrol sistemleri başlatılıyor...
✓ Sulama sistemi başlatıldı (4 zone)
✓ Havalandırma sistemi başlatıldı
✓ İklim kontrol sistemi başlatıldı
✓ Bitki aydınlatma sistemi başlatıldı

📶 WiFi'ye bağlanılıyor...
✓ WiFi bağlantısı başarılı!
IP Adresi: 192.168.1.150

🔗 MQTT'ye bağlanılıyor...
✓ Bağlandı!
✓ MQTT topic'leri dinleniyor

🌐 HTTP Server başlatılıyor...
✓ HTTP Server: http://192.168.1.150

✅ Sera otomasyon sistemi hazır!
```

### 4. n8n Workflow'ları İçe Aktar

1. n8n arayüzüne gidin (`http://localhost:5678`)
2. **Workflows → Import from File**
3. Bu dosyaları import edin:
   - `n8n-workflows/greenhouse/greenhouse-monitoring.json`
   - `n8n-workflows/greenhouse/greenhouse-auto-irrigation.json`
   - `n8n-workflows/greenhouse/greenhouse-manual-control.json`

4. Her workflow'da MQTT credential ayarlarını yapın

### 5. Test

```bash
# Sensör verilerini dinle
mosquitto_sub -t "greenhouse/sensors/#"

# Manuel sulama başlat
curl -X POST http://192.168.1.150/api/irrigation \
  -H "Content-Type: application/json" \
  -d '{"action":"start","zone":0,"duration":30000}'

# Sistem durumunu sorgula
curl http://192.168.1.150/api/status
```

## 🎮 Kullanım Kılavuzu

### MQTT Kontrol

#### Sulama Başlat
```json
Topic: greenhouse/control/irrigation
{
  "action": "start",
  "zone": 0,
  "duration": 60000
}
```

#### İklim Ayarla
```json
Topic: greenhouse/control/climate
{
  "action": "set_target_temp",
  "temperature": 24.5
}
```

#### Fan Kontrolü
```json
Topic: greenhouse/control/ventilation
{
  "action": "fan",
  "speed": 75
}
```

### HTTP API

#### Tüm Sensörleri Oku
```bash
GET http://KART_IP/api/sensors

Response:
{
  "temperature_humidity": {
    "temperature": 24.5,
    "humidity": 65,
    "heat_index": 25.2
  },
  "soil_moisture": [
    {"zone": 0, "name": "Domates Bölgesi", "moisture": 45, "status": "Normal"},
    ...
  ],
  "light": {
    "percent": 70,
    "level": "Aydınlık"
  }
}
```

### Webhook Kontrolü (n8n)

```bash
POST http://N8N_URL/webhook/greenhouse/control

Body:
{
  "system": "irrigation",
  "action": "start",
  "zone": 2,
  "duration": 45000
}
```

## 📊 Otomasyon Kuralları

### Otomatik Sulama Mantığı

```
IF toprak_nem < %20:
  sulama_suresi = 90 saniye (çok kuru)

ELSE IF toprak_nem < %30:
  sulama_suresi = 60 saniye (kuru)

IF sicaklik > 30°C:
  sulama_suresi *= 1.3 (sıcak hava)

IF nem > %70:
  sulama_suresi *= 0.8 (yüksek nem)

IF gece_vakti (22:00-06:00):
  sulamayi_ertele()
```

### İklim Kontrolü

```
Hedef Sıcaklık = 24°C
Histerezis = ±1°C

IF sicaklik < 23°C:
  isitici_ac()

IF sicaklik > 25°C:
  sogutucu_ac()
```

### Havalandırma

```
IF sicaklik > 30°C:
  fan_hizi = %100
  pencere_acisi = 90°

ELSE IF sicaklik > 26°C:
  fan_hizi = %60
  pencere_acisi = 45°

IF nem > %80:
  fan_hizi = max(fan_hizi, %70)
```

## 🔔 Alarm ve Bildirimler

### Kritik Alarmlar (Email + Telegram)
- Sıcaklık < 15°C veya > 35°C
- Nem < %30 veya > %90
- Toprak nem < %15 (çok kuru)
- Sistem offline (5 dakika)

### Uyarılar (Sadece Telegram)
- Sıcaklık normal aralık dışı (18-30°C)
- Nem normal aralık dışı (40-80%)
- Sulama gerekli (%30 altı)
- Gündüz ışık yetersiz

## 📈 Veri Loglama

### Veritabanı Şeması (PostgreSQL)

```sql
-- Sensör verileri
CREATE TABLE greenhouse_sensor_data (
  id SERIAL PRIMARY KEY,
  sensor_type VARCHAR(50),
  data JSONB,
  severity VARCHAR(20),
  timestamp TIMESTAMP
);

-- Sulama logları
CREATE TABLE irrigation_log (
  id SERIAL PRIMARY KEY,
  zones JSONB,
  temperature FLOAT,
  humidity FLOAT,
  timestamp TIMESTAMP
);

-- Manuel kontrol logları
CREATE TABLE manual_control_log (
  id SERIAL PRIMARY KEY,
  system VARCHAR(50),
  action VARCHAR(50),
  data JSONB,
  timestamp TIMESTAMP
);
```

## 🔧 Gelişmiş Ayarlar

### Zone İsimlendirme

`firmware/greenhouse/sensors_soil.h` içinde:

```cpp
const String ZONE_NAMES[] = {
  "Domates Bölgesi",
  "Salatalık Bölgesi",
  "Biber Bölgesi",
  "Fide Bölgesi"
};
```

### Alarm Eşikleri

Ana firmware'de (`greenhouse.ino`):

```cpp
// Sıcaklık alarmı
isTemperatureAlarm(15, 35)  // Min: 15°C, Max: 35°C

// Nem alarmı
isHumidityAlarm(40, 80)     // Min: %40, Max: %80
```

### Sulama Zamanlaması

```cpp
// Otomatik sulama minimum aralığı (4 saat)
if (millis() - irrigationZones[i].lastWatering > 14400000) {
  startIrrigation(i, 60000);
}
```

## 📱 Mobil Uygulama Entegrasyonu

### Telegram Bot Komutları

n8n üzerinden oluşturulabilir:

```
/sera_durum - Anlık sensör değerleri
/sulama_zone1 - Zone 1'i sula
/sicaklik_ayarla 24 - Hedef sıcaklık ayarla
/fan_hizi 80 - Fan hızını %80 yap
/oto_sulama_ac - Otomatik sulamayı aç
```

## 🐛 Sorun Giderme

### DHT22 Okuma Hatası
```
Semptom: "DHT22 okuma hatası!"
Çözüm:
  - Data pin bağlantısını kontrol edin
  - 4.7kΩ pull-up direnci ekleyin (DATA - VCC arası)
  - Sensör arızalı olabilir, değiştirin
```

### MQTT Bağlanamıyor
```
Semptom: "MQTT bağlanamıyor... rc=-2"
Çözüm:
  - Broker IP doğru mu?
  - Mosquitto çalışıyor mu? (mosquitto -v)
  - Firewall port 1883'ü engelliyor olabilir
```

### Sulama Çalışmıyor
```
Semptom: Sulama komutu gönderildi ama valve açılmıyor
Çözüm:
  - Röle pinini multimetre ile test edin
  - Röle modülü 5V alıyor mu kontrol edin
  - Röle trigger modu: Active LOW mu HIGH mu?
  - Solenoid valve gücü yeterli mi?
```

## 📚 Ek Kaynaklar

- [Pin Bağlantı Detayları](wiring-diagram.md)
- [n8n Workflow Örnekleri](../n8n-workflows/greenhouse/)
- [API Referansı](../api.md)
- [Sensör Kalibrasyon Rehberi](calibration.md)

## 🤝 Katkıda Bulunma

Projeye katkıda bulunmak için pull request gönderebilirsiniz.

## 📄 Lisans

MIT License

---

**Not:** Bu sistem 24/7 çalışacak şekilde tasarlanmıştır. Güvenilirlik için UPS (kesintisiz güç kaynağı) kullanmanız önerilir.
