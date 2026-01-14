# Kurulum Kılavuzu

Deneyap Kart 1A v2 + n8n IoT Otomasyon Sistemi'ni kurmak için adım adım rehber.

## 📋 Gereksinimler

### Donanım
- ✅ Deneyap Kart 1A v2 (Type-C)
- ✅ USB Type-C kablosu
- ✅ Sensörler (opsiyonel): toprak nem, LDR, NTC sıcaklık, vb.
- ✅ Röle modülü (opsiyonel)
- ✅ LED'ler, dirençler, breadboard

### Yazılım
- ✅ Arduino IDE 2.x veya üzeri
- ✅ n8n (Docker veya npm)
- ✅ MQTT Broker (Mosquitto önerilir)
- ✅ Git

## 🔧 1. Arduino IDE Kurulumu

### 1.1. Arduino IDE'yi İndir
https://www.arduino.cc/en/software adresinden işletim sisteminize uygun versiyonu indirin.

### 1.2. Deneyap Kart Desteği Ekle

1. Arduino IDE'yi açın
2. **File → Preferences** menüsüne gidin
3. **Additional Boards Manager URLs** alanına şunu ekleyin:
   ```
   https://raw.githubusercontent.com/deneyapkart/deneyapkart-arduino-core/master/package_deneyapkart_index.json
   ```
4. **OK** ile kaydedin

### 1.3. Board Package'ı Kur

1. **Tools → Board → Boards Manager** menüsüne gidin
2. Arama kutusuna "deneyap" yazın
3. **"Deneyap Development Boards"** paketini bulun ve **Install** edin
4. Kurulum tamamlanınca kapat

### 1.4. USB Driver Kurulumu

**Windows için:**
- [CP210x USB to UART Driver](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers) indirin ve kurun

**Linux için:**
```bash
sudo usermod -a -G dialout $USER
# Çıkış yapıp tekrar giriş yapın
```

**macOS için:**
- Genellikle otomatik yüklenir, sorun olursa CP210x driver kurun

### 1.5. Board Seçimi

1. Deneyap Kart'ı USB ile bilgisayara bağlayın
2. **Tools → Board → Deneyap Development Boards → Deneyap Kart 1A v2** seçin
3. **Tools → Port** menüsünden kartın bağlı olduğu portu seçin (örn: COM3, /dev/ttyUSB0)
4. **Tools → Upload Speed → 921600** önerilir

## 🐳 2. MQTT Broker Kurulumu (Mosquitto)

### Docker ile (Önerilen)

```bash
# Mosquitto'yu Docker ile çalıştır
docker run -d \
  --name mosquitto \
  -p 1883:1883 \
  -p 9001:9001 \
  -v $(pwd)/mosquitto.conf:/mosquitto/config/mosquitto.conf \
  eclipse-mosquitto
```

### Manuel Kurulum

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

**Windows:**
- https://mosquitto.org/download/ adresinden Windows installer'ı indirin
- Kurulumu yapın ve servis olarak başlatın

**macOS:**
```bash
brew install mosquitto
brew services start mosquitto
```

### Mosquitto Konfigürasyonu

`mosquitto.conf` dosyası oluşturun:

```conf
# mosquitto.conf
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
```

## 🔄 3. n8n Kurulumu

### Docker ile (Önerilen)

```bash
# n8n'i Docker ile çalıştır
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  --network host \
  n8nio/n8n
```

Tarayıcıda http://localhost:5678 adresine gidin.

### npm ile

```bash
npm install -g n8n
n8n start
```

### n8n MQTT Credential Ayarı

1. n8n arayüzünde **Credentials** menüsüne gidin
2. **New Credential → MQTT** seçin
3. Ayarları girin:
   - **Protocol**: mqtt
   - **Host**: localhost (veya broker IP'niz)
   - **Port**: 1883
   - **Username**: (varsa)
   - **Password**: (varsa)
4. **Save** edin

## 📦 4. Arduino Kütüphanelerini Kur

Arduino IDE'de **Sketch → Include Library → Manage Libraries** menüsüne gidin ve şunları kurun:

- **PubSubClient** (by Nick O'Leary) - MQTT kütüphanesi
- **ArduinoJson** (by Benoit Blanchon) - JSON işleme

## 🚀 5. Firmware Yükleme

### 5.1. Projeyi Klonla

```bash
git clone https://github.com/YOURUSERNAME/srky.git
cd srky
```

### 5.2. Konfigürasyonu Düzenle

`firmware/config/config.h` dosyasını düzenleyin:

```cpp
// WiFi Ayarları
#define WIFI_SSID "sizin_wifi_adiniz"
#define WIFI_PASSWORD "sizin_wifi_sifreniz"

// MQTT Ayarları
#define MQTT_BROKER "192.168.1.100"  // Broker IP'nizi yazın
```

### 5.3. İlk Yükleme (Boot Mode)

**ÖNEMLİ:** İlk kez firmware yüklerken manuel boot modu gerekli:

1. Arduino IDE'de **Upload** butonuna basın
2. Serial monitörde **"Connecting…"** yazısını bekleyin
3. Şu adımları yapın:
   - **BUT** butonuna basılı tutun
   - **RES** butonuna basın ve bırakın
   - **BUT** butonunu bırakın
4. Yükleme başlayacak

İkinci yüklemelerden sonra bu işlem gerekmez.

### 5.4. Test Et

1. **Tools → Serial Monitor** açın (115200 baud)
2. Kartı reset edin
3. WiFi ve MQTT bağlantı mesajlarını görmelisiniz:
   ```
   WiFi bağlandı!
   IP Adresi: 192.168.1.XXX
   MQTT bağlandı!
   ```

## 🔌 6. Donanım Bağlantıları

### Temel LED Testi

```
LED Anodu (+) -> 220Ω Direnç -> GPIO 13
LED Katodu (-) -> GND
```

### Röle Modülü

```
Röle VCC -> 3.3V
Röle GND -> GND
Röle IN  -> GPIO 12
```

### Analog Sensör (örn: Toprak Nem)

```
Sensör VCC -> 3.3V
Sensör GND -> GND
Sensör Signal -> A0
```

### Touch Button

```
Bakır folyo -> 1MΩ direnç -> GPIO (T1)
```

## 📊 7. n8n Workflow'ları İmport Et

1. n8n arayüzünde **Workflows** menüsüne gidin
2. **Import from File** seçin
3. `n8n-workflows/` klasöründeki JSON dosyalarını import edin:
   - `temperature-monitoring.json`
   - `gpio-control-webhook.json`
   - `smart-irrigation.json`

## ✅ 8. Test Senaryoları

### Test 1: Sıcaklık Okuma

```bash
# MQTT topic'ini dinle
mosquitto_sub -h localhost -t "deneyap/sensors/temperature"
```

Kart her 5 saniyede bir sıcaklık verisi gönderecek.

### Test 2: GPIO Kontrolü

```bash
# LED'i aç
mosquitto_pub -h localhost -t "deneyap/control/gpio" \
  -m '{"pin":13,"action":"ON"}'

# LED'i kapat
mosquitto_pub -h localhost -t "deneyap/control/gpio" \
  -m '{"pin":13,"action":"OFF"}'
```

### Test 3: HTTP API

```bash
# Durum sorgula
curl http://KART_IP_ADRESI/api/status

# GPIO kontrolü
curl -X POST http://KART_IP_ADRESI/api/gpio \
  -H "Content-Type: application/json" \
  -d '{"pin":13,"action":"ON"}'
```

## 🔍 Sorun Giderme

### Kart Tanınmıyor
- USB kablosunu değiştirin (veri kablosu olmalı)
- Driver'ları yeniden kurun
- Farklı USB portuna takın

### WiFi Bağlanamıyor
- SSID ve şifre doğru mu kontrol edin
- 2.4GHz WiFi kullanın (5GHz desteklenmez)
- Router'ın SSID broadcast açık olmalı

### MQTT Bağlanamıyor
- Broker IP doğru mu kontrol edin
- Broker çalışıyor mu: `mosquitto -v`
- Firewall MQTT portunu (1883) engelliyor olabilir

### Upload Hatası
- Boot modu adımlarını doğru yapın
- Reset butonuna basıp tekrar deneyin
- Upload speed'i düşürün (921600 → 115200)

## 📚 Ek Kaynaklar

- [Deneyap Kart Resmi Dokümantasyon](https://deneyapkart.org/en/docs/deneyap-kart-1a-v2)
- [n8n Dokümantasyon](https://docs.n8n.io/)
- [MQTT Essentials](https://www.hivemq.com/mqtt-essentials/)
- [Arduino JSON](https://arduinojson.org/)

## 🆘 Destek

Sorun yaşıyorsanız:
- GitHub Issues: [Proje Issues](https://github.com/YOURUSERNAME/srky/issues)
- Deneyap Forum: [forum.deneyapkart.org](https://forum.deneyapkart.org/)

---

**Sonraki adım:** [API Dokümantasyonu](api.md) ile n8n entegrasyon detaylarını öğrenin.
