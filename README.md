# Deneyap Kart 1A v2 + n8n IoT Otomasyon Sistemi

Deneyap Kart 1A v2'nin tüm özelliklerini (kamera hariç) n8n otomasyonu ile entegre eden kapsamlı IoT projesi.

## 📋 Proje Özeti

Bu proje, Deneyap Kart 1A v2 geliştirme kartının tüm yeteneklerini kullanarak n8n workflow automation platformu ile tam entegrasyon sağlar.

### 🎯 Özellikler

#### Donanım Yetenekleri
- ✅ **23x Digital I/O** - GPIO kontrol ve okuma
- ✅ **13x Analog Input** - ADC sensör okuma (12-bit)
- ✅ **9x Capacitive Touch** - Dokunmatik arayüz
- ✅ **26x PWM Output** - LED dimming, motor kontrol
- ✅ **Built-in Temperature Sensor** - Dahili sıcaklık sensörü
- ✅ **WiFi** - Kablosuz iletişim
- ✅ **Bluetooth** - BLE iletişim
- ✅ **I2C/SPI/UART** - Harici sensör/modül bağlantısı

#### n8n Entegrasyonları
- 🔄 **MQTT Protocol** - Gerçek zamanlı veri akışı
- 🌐 **HTTP REST API** - RESTful komut interface
- 📊 **WebSocket** - Düşük gecikmeli kontrol
- 🔔 **Webhook Triggers** - Olay bazlı otomasyonlar
- 📈 **Data Logging** - Veritabanı entegrasyonu
- 📧 **Notifications** - Email/SMS/Telegram bildirimleri

## 🏗️ Proje Yapısı

```
srky/
├── firmware/               # ESP32 Arduino kodu
│   ├── main/              # Ana firmware
│   ├── config/            # Konfigürasyon dosyaları
│   ├── sensors/           # Sensör kütüphaneleri
│   └── examples/          # Örnek uygulamalar
├── n8n-workflows/         # n8n workflow dosyaları
│   ├── data-collection/   # Veri toplama workflows
│   ├── device-control/    # Cihaz kontrol workflows
│   └── automation/        # Otomasyon scenarios
├── docs/                  # Dokümantasyon
│   ├── pinout.md         # Pin bağlantı şeması
│   ├── setup.md          # Kurulum kılavuzu
│   └── api.md            # API dokümantasyonu
└── README.md

```

## 🚀 Hızlı Başlangıç

### 1. Arduino IDE Kurulumu

```bash
# Arduino IDE'ye Deneyap Kart desteği ekle
# File → Preferences → Additional Boards Manager URLs:
https://raw.githubusercontent.com/deneyapkart/deneyapkart-arduino-core/master/package_deneyapkart_index.json
```

### 2. Gerekli Kütüphaneler

- WiFi (built-in)
- PubSubClient (MQTT)
- ArduinoJson (JSON parsing)
- WebServer (HTTP server)

### 3. n8n Kurulumu

```bash
# Docker ile n8n çalıştır
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

## 📡 İletişim Protokolleri

### MQTT Konuları (Topics)

```
deneyap/sensors/temperature    # Sıcaklık verisi
deneyap/sensors/analog         # Analog sensör verisi
deneyap/gpio/digital           # Digital I/O durumu
deneyap/control/gpio           # GPIO kontrol komutları
deneyap/control/pwm            # PWM kontrol
deneyap/status                 # Cihaz durumu
```

### HTTP REST API Endpoints

```
GET  /api/status              # Cihaz durumu
GET  /api/sensors             # Tüm sensör verisi
POST /api/gpio/:pin           # GPIO kontrol
POST /api/pwm/:pin            # PWM ayarla
GET  /api/analog/:pin         # Analog okuma
```

## 🎮 Kullanım Senaryoları

### 1. Akıllı Ev Otomasyonu
- Sıcaklık bazlı klima kontrolü
- Işık sensörü ile otomatik aydınlatma
- Hareket sensörü ile güvenlik alarmı

### 2. Endüstriyel Monitoring
- Makine sıcaklık izleme
- Titreşim analizi
- Enerji tüketimi takibi

### 3. Tarım Otomasyonu
- Toprak nem sensörü → Sulama kontrolü
- Sıcaklık/nem → Sera iklim kontrolü
- Işık sensörü → Aydınlatma optimizasyonu

### 4. Data Logger
- Çoklu sensör verisi toplama
- Veritabanı kayıt
- Grafik ve raporlama

## 🔧 Teknik Detaylar

### ESP32-S3 Özellikleri
- **İşlemci**: Dual-core Xtensa LX7
- **Frekans**: 240 MHz
- **RAM**: 512 KB SRAM
- **Flash**: 4 MB
- **WiFi**: 802.11 b/g/n
- **Bluetooth**: BLE 5.0

### Pin Konfigürasyonu
Detaylı pin şeması için `docs/pinout.md` dosyasına bakın.

## 📚 Kaynaklar

- [Deneyap Kart Resmi Dokümantasyon](https://deneyapkart.org/en/docs/deneyap-kart-1a-v2)
- [Arduino Core GitHub](https://github.com/deneyapkart/deneyapkart-arduino-core)
- [n8n Dokümantasyon](https://docs.n8n.io/)

## 🤝 Katkıda Bulunma

Projeye katkıda bulunmak için pull request gönderebilirsiniz.

## 📄 Lisans

MIT License

---

**Not**: Kamera özelliği bu projede kullanılmamaktadır.
