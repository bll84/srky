/*
 * Örnek: Analog Sensör İzleme
 *
 * Bu örnek, analog sensörlerden (potansiyometre, LDR, toprak nem sensörü vb.)
 * veri okur ve n8n'e MQTT ile gönderir.
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi Ayarları
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Ayarları
const char* mqtt_server = "YOUR_MQTT_BROKER";

// Analog Pinler (Deneyap Kart 1A v2'de 13 adet)
const int SENSOR_PINS[] = {A0, A1, A2, A3, A4, A5};
const int NUM_SENSORS = 6;

// Sensör isimleri (özelleştirilebilir)
const String SENSOR_NAMES[] = {
  "Toprak Nem",
  "Işık Sensörü",
  "Potansiyometre",
  "Sıcaklık (NTC)",
  "Gaz Sensörü",
  "Basınç"
};

// Güncelleme aralığı
const unsigned long UPDATE_INTERVAL = 2000;  // 2 saniye
unsigned long lastUpdate = 0;

WiFiClient wifiClient;
PubSubClient client(wifiClient);

void setup() {
  Serial.begin(115200);

  // Analog pinleri ayarla
  for (int i = 0; i < NUM_SENSORS; i++) {
    pinMode(SENSOR_PINS[i], INPUT);
  }

  // WiFi Bağlantısı
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi bağlandı!");

  // MQTT Bağlantısı
  client.setServer(mqtt_server, 1883);
  reconnect();
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long currentMillis = millis();
  if (currentMillis - lastUpdate >= UPDATE_INTERVAL) {
    lastUpdate = currentMillis;
    readAndSendSensors();
  }
}

void readAndSendSensors() {
  // JSON dokümantı oluştur
  StaticJsonDocument<1024> doc;
  JsonArray sensors = doc.createNestedArray("sensors");

  // Tüm sensörleri oku
  for (int i = 0; i < NUM_SENSORS; i++) {
    int rawValue = analogRead(SENSOR_PINS[i]);
    float voltage = (rawValue / 4095.0) * 3.3;  // ESP32: 12-bit ADC, 3.3V
    int percentage = map(rawValue, 0, 4095, 0, 100);

    JsonObject sensor = sensors.createNestedObject();
    sensor["name"] = SENSOR_NAMES[i];
    sensor["pin"] = String("A") + String(i);
    sensor["raw"] = rawValue;
    sensor["voltage"] = round(voltage * 100) / 100.0;  // 2 ondalık
    sensor["percentage"] = percentage;

    // Serial çıktı
    Serial.print(SENSOR_NAMES[i]);
    Serial.print(": ");
    Serial.print(rawValue);
    Serial.print(" (");
    Serial.print(voltage);
    Serial.print("V, ");
    Serial.print(percentage);
    Serial.println("%)");
  }

  doc["timestamp"] = millis();
  doc["device"] = "deneyap-01";

  // JSON'u string'e çevir
  String output;
  serializeJson(doc, output);

  // MQTT'ye publish et
  client.publish("deneyap/sensors/analog", output.c_str());

  Serial.println("Veri gönderildi!\n");
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("MQTT bağlanılıyor...");
    if (client.connect("deneyap-analog-monitor")) {
      Serial.println(" bağlandı!");
    } else {
      Serial.print(" hata! rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

/*
 * SENSÖR BAĞLANTI ÖRNEKLERİ:
 *
 * 1. TOPRAK NEM SENSÖRÜ (A0):
 *    - VCC -> 3.3V
 *    - GND -> GND
 *    - Signal -> A0
 *
 * 2. LDR (Işık Sensörü) (A1):
 *    - LDR bir bacak -> 3.3V
 *    - LDR diğer bacak -> A1 ve 10kΩ direnç (GND'ye)
 *
 * 3. POTANSİYOMETRE (A2):
 *    - Sol bacak -> 3.3V
 *    - Orta bacak -> A2
 *    - Sağ bacak -> GND
 *
 * 4. NTC SICAKLIK SENSÖRÜ (A3):
 *    - NTC bir bacak -> 3.3V
 *    - NTC diğer bacak -> A3 ve 10kΩ direnç (GND'ye)
 *
 * n8n WORKFLOW ÖRNEĞİ:
 *
 * 1. MQTT Trigger: "deneyap/sensors/analog" topic'ini dinle
 * 2. Function: Her sensör için ayrı işlem yap
 * 3. Switch: Sensör değerlerine göre aksiyon al
 *    - Toprak nem < 30% -> Sulama başlat
 *    - Işık < 20% -> Aydınlatmayı aç
 *    - Sıcaklık > 30°C -> Fan çalıştır
 * 4. Database: Tüm verileri logla
 * 5. Notification: Alarm durumlarında bildirim gönder
 */
