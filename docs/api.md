# API Dokümantasyonu

Akıllı Deneyap Sistemi için MQTT ve HTTP REST API referansı.

## 📡 MQTT API

### Topic Yapısı

Tüm MQTT topic'leri şu yapıdadır:
```
deneyap/{kategori}/{özellik}
```

### 📊 Sensör Verileri (Publish - Kart → n8n)

#### 1. Sıcaklık Sensörü

**Topic:** `deneyap/sensors/temperature`

**Payload:**
```json
{
  "temperature": 23.5,
  "unit": "C",
  "timestamp": 123456789
}
```

**n8n Kullanım:**
```javascript
// MQTT Trigger node
const data = JSON.parse($json.payload);
const temp = data.temperature;

if (temp > 30) {
  // Yüksek sıcaklık alarmı
}
```

---

#### 2. Analog Sensörler

**Topic:** `deneyap/sensors/analog`

**Payload:**
```json
{
  "analog": [
    {
      "pin": "A0",
      "value": 2048,
      "voltage": 1.65
    },
    {
      "pin": "A1",
      "value": 3500,
      "voltage": 2.82
    }
  ],
  "timestamp": 123456789
}
```

**n8n Kullanım:**
```javascript
// Parse analog verisi
const sensors = JSON.parse($json.payload).analog;
const soilMoisture = sensors.find(s => s.pin === 'A0');

if (soilMoisture.value < 1000) {
  // Toprak kuru, sulama başlat
}
```

---

#### 3. Digital GPIO Durumları

**Topic:** `deneyap/gpio/digital`

**Payload:**
```json
{
  "digital": [
    {"pin": 15, "state": "HIGH"},
    {"pin": 16, "state": "LOW"},
    {"pin": 17, "state": "HIGH"}
  ]
}
```

---

#### 4. Touch (Kapasitif Dokunma)

**Topic:** `deneyap/sensors/touch`

**Payload:**
```json
{
  "touch": [
    {
      "pin": "T1",
      "value": 25,
      "touched": true
    },
    {
      "pin": "T2",
      "value": 80,
      "touched": false
    }
  ]
}
```

**n8n Kullanım:**
```javascript
// Touch button handler
const touchData = JSON.parse($json.payload).touch;

touchData.forEach(button => {
  if (button.touched) {
    // Button basıldı, aksiyon al
  }
});
```

---

#### 5. Cihaz Durumu

**Topic:** `deneyap/status`

**Payload:**
```json
{
  "device": "Deneyap Kart 1A v2",
  "firmware": "1.0.0",
  "device_id": "DK1A-001",
  "uptime": 3600,
  "wifi_connected": true,
  "mqtt_connected": true,
  "ip_address": "192.168.1.100",
  "rssi": -45,
  "free_heap": 280000
}
```

---

### 🎮 Kontrol Komutları (Subscribe - n8n → Kart)

#### 1. GPIO Kontrolü

**Topic:** `deneyap/control/gpio`

**Payload Format:**
```json
{
  "pin": 13,
  "action": "ON"
}
```

**action değerleri:**
- `"ON"` veya `"HIGH"` - GPIO HIGH (3.3V)
- `"OFF"` veya `"LOW"` - GPIO LOW (0V)
- `"TOGGLE"` - Durumu tersine çevir

**n8n MQTT Publish Örneği:**
```javascript
// Function node
return {
  json: {
    pin: 12,
    action: "ON"
  }
};

// MQTT node'da:
// Topic: deneyap/control/gpio
// Message: {{JSON.stringify($json)}}
```

**MQTT Command Line:**
```bash
# LED'i aç
mosquitto_pub -h localhost -t "deneyap/control/gpio" \
  -m '{"pin":13,"action":"ON"}'

# Röle kapat
mosquitto_pub -h localhost -t "deneyap/control/gpio" \
  -m '{"pin":12,"action":"OFF"}'

# Toggle
mosquitto_pub -h localhost -t "deneyap/control/gpio" \
  -m '{"pin":14,"action":"TOGGLE"}'
```

---

#### 2. PWM Kontrolü

**Topic:** `deneyap/control/pwm`

**Payload Format:**
```json
{
  "pin": 13,
  "value": 128,
  "channel": 0
}
```

**Parametreler:**
- `pin`: GPIO pin numarası
- `value`: PWM değeri (0-255)
  - 0 = Tamamen kapalı
  - 128 = %50 duty cycle
  - 255 = Tamamen açık
- `channel`: PWM kanalı (0-15)

**n8n Örnek:**
```javascript
// LED parlaklık kontrolü
const brightness = 180;  // 0-255

return {
  json: {
    pin: 13,
    value: brightness,
    channel: 0
  }
};
```

**MQTT Command Line:**
```bash
# LED %50 parlaklık
mosquitto_pub -h localhost -t "deneyap/control/pwm" \
  -m '{"pin":13,"value":128,"channel":0}'

# Motor hızı %75
mosquitto_pub -h localhost -t "deneyap/control/pwm" \
  -m '{"pin":25,"value":191,"channel":1}'
```

---

## 🌐 HTTP REST API

### Base URL
```
http://{KART_IP_ADRESI}/api
```

### Endpoints

#### 1. GET /api/status

Cihaz durumu ve sistem bilgilerini döner.

**Request:**
```bash
curl http://192.168.1.100/api/status
```

**Response:**
```json
{
  "device": "Deneyap Kart 1A v2",
  "firmware": "1.0.0",
  "uptime": 3600,
  "wifi_rssi": -45,
  "ip": "192.168.1.100",
  "free_heap": 280000
}
```

---

#### 2. GET /api/sensors

Tüm sensör verilerini döner.

**Request:**
```bash
curl http://192.168.1.100/api/sensors
```

**Response:**
```json
{
  "temperature": 24.5,
  "analog": [2048, 1500, 3200, 0, 0, 0],
  "touch": [30, 85, 42, 90, 75]
}
```

**n8n HTTP Request Node:**
```javascript
// HTTP Request node ayarları
Method: GET
URL: http://192.168.1.100/api/sensors
Authentication: None
Response Format: JSON
```

---

#### 3. POST /api/gpio

GPIO pin'ini kontrol eder.

**Request:**
```bash
curl -X POST http://192.168.1.100/api/gpio \
  -H "Content-Type: application/json" \
  -d '{"pin":13,"action":"ON"}'
```

**Request Body:**
```json
{
  "pin": 13,
  "action": "ON"
}
```

**Response:**
```json
{
  "status": "ok"
}
```

**n8n HTTP Request Node:**
```javascript
// Function node - prepare data
return {
  json: {
    pin: 12,
    action: "TOGGLE"
  }
};

// HTTP Request node
Method: POST
URL: http://192.168.1.100/api/gpio
Body Content Type: JSON
Body: {{JSON.stringify($json)}}
```

---

#### 4. POST /api/pwm

PWM çıkışını ayarlar.

**Request:**
```bash
curl -X POST http://192.168.1.100/api/pwm \
  -H "Content-Type: application/json" \
  -d '{"pin":13,"value":200,"channel":0}'
```

**Request Body:**
```json
{
  "pin": 13,
  "value": 200,
  "channel": 0
}
```

**Response:**
```json
{
  "status": "ok"
}
```

---

#### 5. GET /api/analog?pin={PIN}

Belirli bir analog pin'den okuma yapar.

**Request:**
```bash
curl http://192.168.1.100/api/analog?pin=36
```

**Response:**
```json
{
  "pin": 36,
  "value": 2048,
  "voltage": 1.65
}
```

---

## 🔄 n8n Workflow Örnekleri

### Örnek 1: Webhook ile LED Kontrolü

```
1. Webhook Trigger (POST /webhook/led-control)
   Body: {"action": "on"}

2. Function Node
   const action = $json.body.action.toUpperCase();
   return {json: {pin: 13, action: action}};

3. HTTP Request Node
   POST http://192.168.1.100/api/gpio
   Body: {{JSON.stringify($json)}}

4. Respond to Webhook
   {"success": true}
```

---

### Örnek 2: Sıcaklık İzleme + Alarm

```
1. MQTT Trigger
   Topic: deneyap/sensors/temperature

2. Function - Parse Data
   const data = JSON.parse($json.payload);
   return {json: {temp: data.temperature}};

3. IF Node
   temp > 30 → true, false

4a. TRUE: Telegram Notification
    "⚠️ Yüksek sıcaklık: {{$json.temp}}°C"

4b. FALSE: Database Insert
    Log normal sıcaklık
```

---

### Örnek 3: Scheduled Veri Toplama

```
1. Schedule Trigger (Her 1 dakika)

2. HTTP Request
   GET http://192.168.1.100/api/sensors

3. Function - Transform Data
   // Veriyi database formatına çevir

4. PostgreSQL Node
   INSERT INTO sensor_data ...

5. IF - Anomaly Detection
   Anormal değer var mı?

6. Email/Telegram Notification (Opsiyonel)
```

---

### Örnek 4: Multi-Sensor Dashboard

```
1. MQTT Trigger (Wildcard)
   Topic: deneyap/sensors/#

2. Switch Node
   Route by topic:
   - temperature → Sıcaklık tablosu
   - analog → Analog tablosu
   - touch → Event log

3. Multiple Database Nodes
   Her veri tipi için ayrı tablo

4. HTTP Request to Dashboard API
   Real-time güncelleme
```

---

## 🔐 Güvenlik Önerileri

### 1. MQTT Authentication

Production ortamında MQTT'ye authentication ekleyin:

```bash
# mosquitto_passwd ile kullanıcı oluştur
mosquitto_passwd -c /etc/mosquitto/passwd deneyap_user

# mosquitto.conf
allow_anonymous false
password_file /etc/mosquitto/passwd
```

Firmware'de:
```cpp
#define MQTT_USER "deneyap_user"
#define MQTT_PASSWORD "secure_password"
```

### 2. HTTPS/TLS

Production'da HTTP yerine HTTPS kullanın veya VPN ile eriş.

### 3. Firewall

Sadece gerekli portları açın:
- 1883: MQTT
- 80/443: HTTP(S)
- 5678: n8n (sadece yerel ağ)

---

## 📊 Veri Formatları

### Timestamp Format

Unix timestamp (milisaniye):
```javascript
// n8n'de parse
const date = new Date($json.timestamp);
```

### Voltage Hesaplama

ESP32-S3: 12-bit ADC, 3.3V referans
```
voltage = (raw_value / 4095) * 3.3
```

### RSSI (WiFi Sinyal Gücü)

- **-30 dBm**: Mükemmel
- **-50 dBm**: Çok iyi
- **-60 dBm**: İyi
- **-70 dBm**: Zayıf
- **-80 dBm**: Çok zayıf

---

## 🐛 Hata Kodları

### MQTT State Codes

Firmware serial çıktısında `rc=` kodu:
- **-4**: Connection timeout
- **-3**: Connection lost
- **-2**: Connect failed
- **-1**: Disconnected
- **0**: Connected
- **1**: Protocol version mismatch
- **2**: Client ID rejected
- **3**: Server unavailable
- **4**: Bad username/password
- **5**: Not authorized

---

## 📚 Ek Kaynaklar

- [MQTT Specification](http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html)
- [n8n MQTT Node](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.mqtt/)
- [ArduinoJson Assistant](https://arduinojson.org/v6/assistant/)

---

**Önceki:** [Kurulum Kılavuzu](setup.md) | **Sonraki:** [Pin Şeması](pinout.md)
