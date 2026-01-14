/*
 * Örnek: LED PWM Kontrolü
 *
 * Bu örnek, PWM kullanarak bir LED'in parlaklığını kontrol eder.
 * n8n'den MQTT mesajı ile parlaklık ayarlanabilir.
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi Ayarları
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Ayarları
const char* mqtt_server = "YOUR_MQTT_BROKER";
const int mqtt_port = 1883;

// PWM Ayarları
const int LED_PIN = 13;
const int PWM_CHANNEL = 0;
const int PWM_FREQ = 5000;
const int PWM_RESOLUTION = 8;  // 0-255

WiFiClient wifiClient;
PubSubClient client(wifiClient);

void setup() {
  Serial.begin(115200);

  // PWM Setup
  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(LED_PIN, PWM_CHANNEL);

  // WiFi Bağlantısı
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi bağlandı!");

  // MQTT Bağlantısı
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
  reconnect();
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  // JSON parse
  StaticJsonDocument<256> doc;
  deserializeJson(doc, message);

  if (String(topic) == "deneyap/control/pwm") {
    int pin = doc["pin"];
    int brightness = doc["value"];  // 0-255

    if (pin == LED_PIN) {
      ledcWrite(PWM_CHANNEL, brightness);
      Serial.println("LED Parlaklık: " + String(brightness));
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("MQTT bağlanılıyor...");
    if (client.connect("deneyap-pwm-example")) {
      Serial.println(" bağlandı!");
      client.subscribe("deneyap/control/pwm");
    } else {
      Serial.print(" hata! rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

/*
 * n8n Workflow Örneği:
 *
 * 1. HTTP Request node ile parlaklık değeri al
 * 2. Function node ile JSON hazırla:
 *    {
 *      "pin": 13,
 *      "value": 128,  // 0-255 arası
 *      "channel": 0
 *    }
 * 3. MQTT node ile "deneyap/control/pwm" topic'ine publish et
 */
