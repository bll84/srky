/*
 * Örnek: Kapasitif Dokunmatik Butonlar
 *
 * ESP32-S3'ün 9 kapasitif dokunma sensörünü kullanarak
 * dokunmatik buton arayüzü oluşturur.
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi & MQTT
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "YOUR_MQTT_BROKER";

WiFiClient wifiClient;
PubSubClient client(wifiClient);

// Touch Pin'ler (ESP32-S3)
const int TOUCH_PINS[] = {T1, T2, T3, T4, T5};
const int NUM_TOUCH = 5;

// Touch buton isimleri
const String TOUCH_NAMES[] = {
  "Buton 1",
  "Buton 2",
  "Buton 3",
  "Buton 4",
  "Buton 5"
};

// Eşik değeri (değer bunun altına düşerse "dokunuldu" sayılır)
const int TOUCH_THRESHOLD = 40;

// Önceki durumlar (debouncing için)
bool previousTouchStates[5] = {false, false, false, false, false};
unsigned long lastTouchTime[5] = {0, 0, 0, 0, 0};
const unsigned long DEBOUNCE_DELAY = 300;  // 300ms

void setup() {
  Serial.begin(115200);

  // WiFi Bağlantısı
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi bağlandı!");

  // MQTT
  client.setServer(mqtt_server, 1883);
  client.setCallback(mqttCallback);
  reconnect();

  Serial.println("Dokunmatik butonlar hazır!");
  Serial.println("Touch sensörlere dokunun...\n");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Tüm touch sensörleri kontrol et
  for (int i = 0; i < NUM_TOUCH; i++) {
    checkTouch(i);
  }

  delay(50);  // Hafif gecikme
}

void checkTouch(int index) {
  int touchValue = touchRead(TOUCH_PINS[index]);
  bool isTouched = (touchValue < TOUCH_THRESHOLD);

  unsigned long currentMillis = millis();

  // Debouncing: Durum değişti mi ve yeterli zaman geçti mi?
  if (isTouched != previousTouchStates[index] &&
      currentMillis - lastTouchTime[index] > DEBOUNCE_DELAY) {

    previousTouchStates[index] = isTouched;
    lastTouchTime[index] = currentMillis;

    if (isTouched) {
      // Dokunma algılandı
      handleTouchEvent(index, touchValue);
    }
  }
}

void handleTouchEvent(int buttonIndex, int touchValue) {
  Serial.print("✓ ");
  Serial.print(TOUCH_NAMES[buttonIndex]);
  Serial.print(" dokunuldu! (değer: ");
  Serial.print(touchValue);
  Serial.println(")");

  // MQTT'ye gönder
  StaticJsonDocument<256> doc;
  doc["button"] = buttonIndex + 1;
  doc["name"] = TOUCH_NAMES[buttonIndex];
  doc["value"] = touchValue;
  doc["timestamp"] = millis();
  doc["event"] = "touch";

  String output;
  serializeJson(doc, output);
  client.publish("deneyap/sensors/touch", output.c_str());

  // Buton özel aksiyonları (özelleştirilebilir)
  executeButtonAction(buttonIndex);
}

void executeButtonAction(int buttonIndex) {
  // Her buton için farklı aksiyon tanımlayabilirsiniz
  switch(buttonIndex) {
    case 0:  // Buton 1 - LED toggle
      {
        StaticJsonDocument<128> cmd;
        cmd["pin"] = 13;
        cmd["action"] = "TOGGLE";
        String output;
        serializeJson(cmd, output);
        client.publish("deneyap/control/gpio", output.c_str());
        Serial.println("→ LED toggle komutu gönderildi");
      }
      break;

    case 1:  // Buton 2 - Röle ON
      {
        StaticJsonDocument<128> cmd;
        cmd["pin"] = 12;
        cmd["action"] = "ON";
        String output;
        serializeJson(cmd, output);
        client.publish("deneyap/control/gpio", output.c_str());
        Serial.println("→ Röle açıldı");
      }
      break;

    case 2:  // Buton 3 - Röle OFF
      {
        StaticJsonDocument<128> cmd;
        cmd["pin"] = 12;
        cmd["action"] = "OFF";
        String output;
        serializeJson(cmd, output);
        client.publish("deneyap/control/gpio", output.c_str());
        Serial.println("→ Röle kapatıldı");
      }
      break;

    case 3:  // Buton 4 - Alarm tetikle
      {
        StaticJsonDocument<128> cmd;
        cmd["alarm"] = "fire";
        cmd["level"] = "high";
        String output;
        serializeJson(cmd, output);
        client.publish("deneyap/alerts", output.c_str());
        Serial.println("→ Alarm tetiklendi!");
      }
      break;

    case 4:  // Buton 5 - Durum raporu
      {
        StaticJsonDocument<256> status;
        status["action"] = "status_request";
        status["button"] = 5;
        String output;
        serializeJson(status, output);
        client.publish("deneyap/status", output.c_str());
        Serial.println("→ Durum raporu istendi");
      }
      break;
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // İsteğe bağlı: n8n'den gelen komutları işle
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("MQTT bağlanılıyor...");
    if (client.connect("deneyap-touch")) {
      Serial.println(" bağlandı!");
      client.subscribe("deneyap/control/#");
    } else {
      Serial.print(" hata! rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

/*
 * DOKUNMATIK SENSÖR BAĞLANTI:
 *
 * ESP32-S3'te kapasitif dokunma sensörleri doğrudan GPIO pin'lere bağlıdır.
 * Harici bağlantı gerekmez, ama daha iyi hassasiyet için:
 *
 * 1. Bakır folyo veya metal plaka kullanın
 * 2. Pin -> 1MΩ direnç -> Dokunma yüzeyi
 * 3. Dokunma yüzeyi arkasına GND (ground plane) ekleyin
 *
 * Touch Pin Eşlemeleri (Deneyap Kart 1A v2):
 * T1  = GPIO1
 * T2  = GPIO2
 * T3  = GPIO3
 * T4  = GPIO4
 * T5  = GPIO5
 * ... (T14'e kadar)
 *
 * n8n WORKFLOW ÖRNEĞİ:
 *
 * 1. MQTT Trigger: "deneyap/sensors/touch" dinle
 * 2. Switch Node: Button numarasına göre aksiyon:
 *    - Button 1 → Işıkları aç/kapa
 *    - Button 2 → Müzik başlat
 *    - Button 3 → Alarm kapat
 *    - Button 4 → Telegram bildirimi gönder
 *    - Button 5 → Durum raporu email'le
 * 3. Database: Tüm buton basışlarını logla
 * 4. Analytics: Kullanım istatistikleri
 */
