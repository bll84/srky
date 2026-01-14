/*
 * Deneyap Kart 1A v2 + n8n IoT Otomasyon Sistemi
 * Ana Firmware
 *
 * Özellikler:
 * - WiFi Bağlantısı
 * - MQTT İletişimi
 * - HTTP REST API
 * - Tüm GPIO/ADC/PWM/Touch özellikleri
 * - Built-in Sensörler
 * - n8n Entegrasyonu
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include "../config/config.h"

// WiFi & MQTT Client'lar
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
WebServer server(HTTP_PORT);

// Zamanlayıcılar
unsigned long lastTempUpdate = 0;
unsigned long lastAnalogUpdate = 0;
unsigned long lastDigitalUpdate = 0;
unsigned long lastTouchUpdate = 0;
unsigned long lastStatusUpdate = 0;

// Sensör Verileri
struct SensorData {
  float temperature;
  int analogValues[13];
  bool digitalStates[23];
  int touchValues[9];
  unsigned long uptime;
  bool wifiConnected;
  bool mqttConnected;
};

SensorData sensorData;

// ==================== SETUP ====================
void setup() {
  if (DEBUG_MODE) {
    Serial.begin(DEBUG_SERIAL_SPEED);
    Serial.println("\n\n=================================");
    Serial.println("Deneyap Kart 1A v2 + n8n");
    Serial.println("Firmware: " + String(FIRMWARE_VERSION));
    Serial.println("=================================\n");
  }

  // Pin Modlarını Ayarla
  setupPins();

  // WiFi Bağlantısı
  setupWiFi();

  // MQTT Bağlantısı
  setupMQTT();

  // HTTP Server Başlat
  setupHTTPServer();

  // Başlangıç Durumu Gönder
  sendStatus();

  Serial.println("\n✓ Sistem hazır!\n");
}

// ==================== MAIN LOOP ====================
void loop() {
  // WiFi bağlantısını kontrol et
  if (WiFi.status() != WL_CONNECTED) {
    reconnectWiFi();
  }

  // MQTT bağlantısını kontrol et
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  // HTTP isteklerini işle
  server.handleClient();

  // Sensör verilerini periyodik olarak gönder
  unsigned long currentMillis = millis();

  // Sıcaklık sensörü
  if (currentMillis - lastTempUpdate >= TEMP_UPDATE_INTERVAL) {
    lastTempUpdate = currentMillis;
    readAndSendTemperature();
  }

  // Analog sensörler
  if (currentMillis - lastAnalogUpdate >= ANALOG_UPDATE_INTERVAL) {
    lastAnalogUpdate = currentMillis;
    readAndSendAnalog();
  }

  // Digital GPIO'lar
  if (currentMillis - lastDigitalUpdate >= DIGITAL_UPDATE_INTERVAL) {
    lastDigitalUpdate = currentMillis;
    readAndSendDigital();
  }

  // Touch sensörler
  if (currentMillis - lastTouchUpdate >= TOUCH_UPDATE_INTERVAL) {
    lastTouchUpdate = currentMillis;
    readAndSendTouch();
  }

  // Durum güncellemesi (her 30 saniye)
  if (currentMillis - lastStatusUpdate >= 30000) {
    lastStatusUpdate = currentMillis;
    sendStatus();
  }
}

// ==================== WiFi FONKSIYONLARI ====================
void setupWiFi() {
  Serial.print("WiFi'ye bağlanılıyor: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startTime < WIFI_TIMEOUT) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi bağlantısı başarılı!");
    Serial.print("IP Adresi: ");
    Serial.println(WiFi.localIP());
    sensorData.wifiConnected = true;
  } else {
    Serial.println("\n✗ WiFi bağlantısı başarısız!");
    sensorData.wifiConnected = false;
  }
}

void reconnectWiFi() {
  Serial.println("WiFi bağlantısı kesildi, yeniden bağlanılıyor...");
  WiFi.disconnect();
  delay(1000);
  setupWiFi();
}

// ==================== MQTT FONKSIYONLARI ====================
void setupMQTT() {
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  mqttClient.setKeepAlive(MQTT_KEEPALIVE);
  reconnectMQTT();
}

void reconnectMQTT() {
  if (WiFi.status() != WL_CONNECTED) {
    sensorData.mqttConnected = false;
    return;
  }

  if (!mqttClient.connected()) {
    Serial.print("MQTT'ye bağlanılıyor...");

    String clientId = String(MQTT_CLIENT_ID) + "-" + String(random(0xffff), HEX);

    if (mqttClient.connect(clientId.c_str(), MQTT_USER, MQTT_PASSWORD)) {
      Serial.println(" ✓ Bağlandı!");
      sensorData.mqttConnected = true;

      // Kontrol topic'lerini subscribe et
      mqttClient.subscribe(TOPIC_CONTROL_GPIO);
      mqttClient.subscribe(TOPIC_CONTROL_PWM);

      Serial.println("✓ MQTT topic'leri dinleniyor");
    } else {
      Serial.print(" ✗ Hata! rc=");
      Serial.println(mqttClient.state());
      sensorData.mqttConnected = false;
    }
  }
}

// MQTT Mesaj Callback
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("MQTT Mesaj alındı [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(message);

  // JSON parse
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.println("JSON parse hatası!");
    return;
  }

  // GPIO Kontrolü
  if (String(topic) == TOPIC_CONTROL_GPIO) {
    handleGPIOControl(doc);
  }

  // PWM Kontrolü
  if (String(topic) == TOPIC_CONTROL_PWM) {
    handlePWMControl(doc);
  }
}

void handleGPIOControl(JsonDocument& doc) {
  int pin = doc["pin"];
  String action = doc["action"];

  if (action == "HIGH" || action == "ON") {
    digitalWrite(pin, HIGH);
    Serial.println("GPIO " + String(pin) + " -> HIGH");
  } else if (action == "LOW" || action == "OFF") {
    digitalWrite(pin, LOW);
    Serial.println("GPIO " + String(pin) + " -> LOW");
  } else if (action == "TOGGLE") {
    digitalWrite(pin, !digitalRead(pin));
    Serial.println("GPIO " + String(pin) + " -> TOGGLE");
  }
}

void handlePWMControl(JsonDocument& doc) {
  int pin = doc["pin"];
  int value = doc["value"];  // 0-255
  int channel = doc["channel"] | 0;

  ledcSetup(channel, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(pin, channel);
  ledcWrite(channel, value);

  Serial.println("PWM Pin " + String(pin) + " -> " + String(value));
}

// ==================== SENSÖR OKUMA ====================
void readAndSendTemperature() {
  // ESP32-S3 dahili sıcaklık sensörü
  // Not: Gerçek donanımda kalibre edilmeli
  float temp = temperatureRead();
  sensorData.temperature = temp;

  StaticJsonDocument<128> doc;
  doc["temperature"] = temp;
  doc["unit"] = "C";
  doc["timestamp"] = millis();

  String output;
  serializeJson(doc, output);

  mqttClient.publish(TOPIC_TEMP, output.c_str());

  if (DEBUG_MODE) {
    Serial.println("Sıcaklık: " + String(temp) + "°C");
  }
}

void readAndSendAnalog() {
  StaticJsonDocument<512> doc;
  JsonArray analogArray = doc.createNestedArray("analog");

  // 13 analog pin'i oku (örnek olarak ilk 6'sı)
  int analogPins[] = {A0, A1, A2, A3, A4, A5};

  for (int i = 0; i < 6; i++) {
    int value = analogRead(analogPins[i]);
    sensorData.analogValues[i] = value;

    JsonObject analogObj = analogArray.createNestedObject();
    analogObj["pin"] = String("A") + String(i);
    analogObj["value"] = value;
    analogObj["voltage"] = (value / 4095.0) * 3.3;  // ESP32 3.3V, 12-bit ADC
  }

  String output;
  serializeJson(doc, output);
  mqttClient.publish(TOPIC_ANALOG, output.c_str());
}

void readAndSendDigital() {
  StaticJsonDocument<1024> doc;
  JsonArray digitalArray = doc.createNestedArray("digital");

  // Digital pinleri oku (konfigüre edilmiş input'lar)
  // Örnek: birkaç pin
  int digitalInputs[] = {15, 16, 17, 18, 19};

  for (int i = 0; i < 5; i++) {
    bool state = digitalRead(digitalInputs[i]);

    JsonObject digObj = digitalArray.createNestedObject();
    digObj["pin"] = digitalInputs[i];
    digObj["state"] = state ? "HIGH" : "LOW";
  }

  String output;
  serializeJson(doc, output);
  mqttClient.publish(TOPIC_DIGITAL, output.c_str());
}

void readAndSendTouch() {
  StaticJsonDocument<512> doc;
  JsonArray touchArray = doc.createNestedArray("touch");

  // Touch pinleri oku
  int touchPins[] = {T1, T2, T3, T4, T5};

  for (int i = 0; i < 5; i++) {
    int touchValue = touchRead(touchPins[i]);
    sensorData.touchValues[i] = touchValue;

    JsonObject touchObj = touchArray.createNestedObject();
    touchObj["pin"] = String("T") + String(i+1);
    touchObj["value"] = touchValue;
    touchObj["touched"] = touchValue < 40;  // Eşik değeri
  }

  String output;
  serializeJson(doc, output);
  mqttClient.publish(TOPIC_TOUCH, output.c_str());
}

void sendStatus() {
  StaticJsonDocument<512> doc;

  doc["device"] = DEVICE_NAME;
  doc["firmware"] = FIRMWARE_VERSION;
  doc["device_id"] = DEVICE_ID;
  doc["uptime"] = millis() / 1000;
  doc["wifi_connected"] = (WiFi.status() == WL_CONNECTED);
  doc["mqtt_connected"] = mqttClient.connected();
  doc["ip_address"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();

  String output;
  serializeJson(doc, output);
  mqttClient.publish(TOPIC_STATUS, output.c_str());

  if (DEBUG_MODE) {
    Serial.println("Durum güncellendi");
  }
}

// ==================== HTTP SERVER ====================
void setupHTTPServer() {
  if (!API_ENABLED) return;

  // API Endpoints
  server.on("/", handleRoot);
  server.on("/api/status", handleAPIStatus);
  server.on("/api/sensors", handleAPISensors);
  server.on("/api/gpio", HTTP_POST, handleAPIGPIO);
  server.on("/api/pwm", HTTP_POST, handleAPIPWM);
  server.on("/api/analog", HTTP_GET, handleAPIAnalog);

  server.onNotFound(handleNotFound);

  server.begin();
  Serial.println("✓ HTTP Server başlatıldı: http://" + WiFi.localIP().toString());
}

void handleRoot() {
  String html = "<html><body>";
  html += "<h1>Deneyap Kart 1A v2 + n8n</h1>";
  html += "<p>Firmware: " + String(FIRMWARE_VERSION) + "</p>";
  html += "<h2>API Endpoints:</h2>";
  html += "<ul>";
  html += "<li>GET /api/status - Cihaz durumu</li>";
  html += "<li>GET /api/sensors - Tüm sensör verisi</li>";
  html += "<li>POST /api/gpio - GPIO kontrolü</li>";
  html += "<li>POST /api/pwm - PWM ayarla</li>";
  html += "<li>GET /api/analog - Analog okuma</li>";
  html += "</ul>";
  html += "</body></html>";

  server.send(200, "text/html", html);
}

void handleAPIStatus() {
  StaticJsonDocument<512> doc;

  doc["device"] = DEVICE_NAME;
  doc["firmware"] = FIRMWARE_VERSION;
  doc["uptime"] = millis() / 1000;
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["ip"] = WiFi.localIP().toString();
  doc["free_heap"] = ESP.getFreeHeap();

  String output;
  serializeJson(doc, output);

  server.send(200, "application/json", output);
}

void handleAPISensors() {
  StaticJsonDocument<1024> doc;

  doc["temperature"] = sensorData.temperature;

  JsonArray analog = doc.createNestedArray("analog");
  for (int i = 0; i < 6; i++) {
    analog.add(sensorData.analogValues[i]);
  }

  JsonArray touch = doc.createNestedArray("touch");
  for (int i = 0; i < 5; i++) {
    touch.add(sensorData.touchValues[i]);
  }

  String output;
  serializeJson(doc, output);

  server.send(200, "application/json", output);
}

void handleAPIGPIO() {
  if (!server.hasArg("plain")) {
    server.send(400, "application/json", "{\"error\":\"No body\"}");
    return;
  }

  String body = server.arg("plain");
  StaticJsonDocument<256> doc;
  deserializeJson(doc, body);

  handleGPIOControl(doc);

  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

void handleAPIPWM() {
  if (!server.hasArg("plain")) {
    server.send(400, "application/json", "{\"error\":\"No body\"}");
    return;
  }

  String body = server.arg("plain");
  StaticJsonDocument<256> doc;
  deserializeJson(doc, body);

  handlePWMControl(doc);

  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

void handleAPIAnalog() {
  String pinStr = server.arg("pin");
  int pin = pinStr.toInt();

  int value = analogRead(pin);
  float voltage = (value / 4095.0) * 3.3;

  StaticJsonDocument<128> doc;
  doc["pin"] = pin;
  doc["value"] = value;
  doc["voltage"] = voltage;

  String output;
  serializeJson(doc, output);

  server.send(200, "application/json", output);
}

void handleNotFound() {
  server.send(404, "application/json", "{\"error\":\"Not found\"}");
}

// ==================== PIN SETUP ====================
void setupPins() {
  // Örnek pin konfigürasyonları
  pinMode(LED_PIN, OUTPUT);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  // Digital input örnekleri
  pinMode(15, INPUT);
  pinMode(16, INPUT);
  pinMode(17, INPUT);
  pinMode(18, INPUT);
  pinMode(19, INPUT);

  Serial.println("✓ Pin'ler yapılandırıldı");
}
