/*
 * Akıllı Deneyap Sistemi
 * SERA OTOMASYONU - Ana Firmware
 *
 * Özellikler:
 * - DHT22 Sıcaklık/Nem İzleme
 * - 4 Zone Toprak Nem Sensörleri
 * - Işık Sensörü (LDR)
 * - Otomatik Sulama Sistemi (4 zone)
 * - Havalandırma Kontrolü (Fan + Pencere)
 * - Isıtma/Soğutma Kontrolü
 * - Bitki Aydınlatma Sistemi
 * - MQTT & HTTP API Entegrasyonu
 * - n8n Otomasyon Desteği
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <DHT.h>

// Sensör ve kontrol modülleri
#include "sensors_dht22.h"
#include "sensors_soil.h"
#include "sensors_light.h"
#include "control_systems.h"

// ==================== KONFİGÜRASYON ====================

// WiFi Ayarları
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// MQTT Ayarları
#define MQTT_BROKER "YOUR_MQTT_BROKER_IP"
#define MQTT_PORT 1883
#define MQTT_USER ""
#define MQTT_PASSWORD ""
#define MQTT_CLIENT_ID "greenhouse-01"

// MQTT Topic'leri
#define TOPIC_GREENHOUSE_TEMP "greenhouse/sensors/temperature"
#define TOPIC_GREENHOUSE_SOIL "greenhouse/sensors/soil"
#define TOPIC_GREENHOUSE_LIGHT "greenhouse/sensors/light"
#define TOPIC_GREENHOUSE_STATUS "greenhouse/status"
#define TOPIC_GREENHOUSE_CONTROL "greenhouse/control/#"
#define TOPIC_GREENHOUSE_IRRIGATION "greenhouse/control/irrigation"
#define TOPIC_GREENHOUSE_CLIMATE "greenhouse/control/climate"
#define TOPIC_GREENHOUSE_VENTILATION "greenhouse/control/ventilation"
#define TOPIC_GREENHOUSE_ALERTS "greenhouse/alerts"

// HTTP Server
#define HTTP_PORT 80

// Güncelleme aralıkları (ms)
#define UPDATE_INTERVAL_TEMP 5000      // 5 saniye
#define UPDATE_INTERVAL_SOIL 10000     // 10 saniye
#define UPDATE_INTERVAL_LIGHT 3000     // 3 saniye
#define UPDATE_INTERVAL_STATUS 30000   // 30 saniye
#define UPDATE_INTERVAL_CONTROL 1000   // 1 saniye

// Otomasyon modu
bool autoIrrigationEnabled = true;
bool autoClimateEnabled = true;
bool autoVentilationEnabled = true;
bool autoLightingEnabled = true;

// ==================== GLOBAL OBJELER ====================

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
WebServer server(HTTP_PORT);

// Zamanlayıcılar
unsigned long lastTempUpdate = 0;
unsigned long lastSoilUpdate = 0;
unsigned long lastLightUpdate = 0;
unsigned long lastStatusUpdate = 0;
unsigned long lastControlUpdate = 0;

// ==================== SETUP ====================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n\n╔══════════════════════════════════════╗");
  Serial.println("║   Akıllı Deneyap Sistemi             ║");
  Serial.println("║   SERA OTOMASYONU v1.0               ║");
  Serial.println("╚══════════════════════════════════════╝\n");

  // Sensörleri başlat
  Serial.println("📡 Sensörler başlatılıyor...");
  initDHT();
  initSoilSensors();
  initLightSensor();

  // Kontrol sistemlerini başlat
  Serial.println("\n🎮 Kontrol sistemleri başlatılıyor...");
  initIrrigationSystem();
  initVentilationSystem();
  initClimateControl();
  initGrowLightSystem();

  // WiFi bağlantısı
  Serial.println("\n📶 WiFi'ye bağlanılıyor...");
  setupWiFi();

  // MQTT bağlantısı
  Serial.println("🔗 MQTT'ye bağlanılıyor...");
  setupMQTT();

  // HTTP Server
  Serial.println("🌐 HTTP Server başlatılıyor...");
  setupHTTPServer();

  Serial.println("\n✅ Sera otomasyon sistemi hazır!\n");
  Serial.println("═══════════════════════════════════════\n");
}

// ==================== MAIN LOOP ====================

void loop() {
  unsigned long currentMillis = millis();

  // WiFi kontrolü
  if (WiFi.status() != WL_CONNECTED) {
    reconnectWiFi();
  }

  // MQTT kontrolü
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  // HTTP Server
  server.handleClient();

  // Sensör okumaları ve MQTT publish
  if (currentMillis - lastTempUpdate >= UPDATE_INTERVAL_TEMP) {
    lastTempUpdate = currentMillis;
    updateTemperatureHumidity();
  }

  if (currentMillis - lastSoilUpdate >= UPDATE_INTERVAL_SOIL) {
    lastSoilUpdate = currentMillis;
    updateSoilMoisture();
  }

  if (currentMillis - lastLightUpdate >= UPDATE_INTERVAL_LIGHT) {
    lastLightUpdate = currentMillis;
    updateLightLevel();
  }

  if (currentMillis - lastStatusUpdate >= UPDATE_INTERVAL_STATUS) {
    lastStatusUpdate = currentMillis;
    sendStatusUpdate();
  }

  // Otomatik kontrol sistemleri
  if (currentMillis - lastControlUpdate >= UPDATE_INTERVAL_CONTROL) {
    lastControlUpdate = currentMillis;
    runAutomationControl();
  }

  // Sulama timer kontrolü
  updateIrrigationSystem();
}

// ==================== SENSÖR OKUMA FONKSİYONLARI ====================

void updateTemperatureHumidity() {
  if (readDHT()) {
    String json = getDHTJSON();
    mqttClient.publish(TOPIC_GREENHOUSE_TEMP, json.c_str());

    Serial.print("🌡️  Sıcaklık: ");
    Serial.print(dhtData.temperature);
    Serial.print("°C | Nem: %");
    Serial.println(dhtData.humidity);

    // Alarm kontrolü
    if (isTemperatureAlarm(15, 35)) {
      sendAlert("temperature", "Sıcaklık normal aralığın dışında!");
    }
    if (isHumidityAlarm(40, 80)) {
      sendAlert("humidity", "Nem normal aralığın dışında!");
    }
  }
}

void updateSoilMoisture() {
  readAllSoilZones();
  String json = getSoilJSON();
  mqttClient.publish(TOPIC_GREENHOUSE_SOIL, json.c_str());

  Serial.println("💧 Toprak Nem:");
  for (int i = 0; i < SOIL_ZONE_COUNT; i++) {
    Serial.print("   Zone ");
    Serial.print(i + 1);
    Serial.print(" (");
    Serial.print(soilZones[i].zoneName);
    Serial.print("): %");
    Serial.print(soilZones[i].moisturePercent);
    Serial.print(" - ");
    Serial.println(getZoneStatus(i));
  }

  // Sulama gerekli mi?
  if (autoIrrigationEnabled && hasZonesNeedingWater()) {
    String zones = getZonesNeedingWater();
    sendAlert("irrigation", "Sulama gerekli: " + zones);
  }
}

void updateLightLevel() {
  if (readLightSensor()) {
    String json = getLightJSON();
    mqttClient.publish(TOPIC_GREENHOUSE_LIGHT, json.c_str());

    Serial.print("☀️  Işık Seviyesi: %");
    Serial.print(lightData.lightPercent);
    Serial.print(" - ");
    Serial.println(lightData.lightLevel);
  }
}

void sendStatusUpdate() {
  String json = getAllSystemsStatusJSON();
  mqttClient.publish(TOPIC_GREENHOUSE_STATUS, json.c_str());

  Serial.println("📊 Durum raporu gönderildi");
}

// ==================== OTOMASYON KONTROL ====================

void runAutomationControl() {
  // Otomatik iklim kontrolü
  if (autoClimateEnabled && dhtData.valid) {
    autoClimateControl(dhtData.temperature);
  }

  // Otomatik havalandırma
  if (autoVentilationEnabled && dhtData.valid) {
    autoVentilationControl(dhtData.temperature, dhtData.humidity);
  }

  // Otomatik aydınlatma
  if (autoLightingEnabled) {
    int hour = getHourOfDay();
    autoGrowLightControl(lightData.lightPercent, hour);
  }

  // Otomatik sulama (toprak nemi düşükse)
  if (autoIrrigationEnabled) {
    for (int i = 0; i < SOIL_ZONE_COUNT; i++) {
      if (soilZones[i].needsWatering && !irrigationZones[i].active) {
        // Son sulamadan en az 4 saat geçmişse
        if (millis() - irrigationZones[i].lastWatering > 14400000) {
          startIrrigation(i, 60000);  // 60 saniye sula
        }
      }
    }
  }
}

// ==================== ALARM/UYARI SİSTEMİ ====================

void sendAlert(String type, String message) {
  StaticJsonDocument<256> doc;
  doc["type"] = type;
  doc["message"] = message;
  doc["timestamp"] = millis();
  doc["severity"] = "warning";

  String output;
  serializeJson(doc, output);

  mqttClient.publish(TOPIC_GREENHOUSE_ALERTS, output.c_str());

  Serial.print("⚠️  ALARM: ");
  Serial.println(message);
}

// ==================== WiFi FONKSİYONLARI ====================

void setupWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi bağlantısı başarılı!");
    Serial.print("IP Adresi: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n✗ WiFi bağlantısı başarısız!");
  }
}

void reconnectWiFi() {
  Serial.println("WiFi yeniden bağlanılıyor...");
  WiFi.disconnect();
  delay(1000);
  setupWiFi();
}

// ==================== MQTT FONKSİYONLARI ====================

void setupMQTT() {
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  reconnectMQTT();
}

void reconnectMQTT() {
  if (WiFi.status() != WL_CONNECTED) return;

  if (!mqttClient.connected()) {
    Serial.print("MQTT bağlanılıyor...");

    if (mqttClient.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASSWORD)) {
      Serial.println(" ✓");

      // Kontrol topic'lerini dinle
      mqttClient.subscribe(TOPIC_GREENHOUSE_IRRIGATION);
      mqttClient.subscribe(TOPIC_GREENHOUSE_CLIMATE);
      mqttClient.subscribe(TOPIC_GREENHOUSE_VENTILATION);

      Serial.println("✓ MQTT topic'leri dinleniyor");
    } else {
      Serial.print(" ✗ Hata! rc=");
      Serial.println(mqttClient.state());
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("📩 MQTT: [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(message);

  // JSON parse
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.println("JSON parse hatası!");
    return;
  }

  // Sulama kontrolü
  if (String(topic) == TOPIC_GREENHOUSE_IRRIGATION) {
    handleIrrigationCommand(doc);
  }
  // İklim kontrolü
  else if (String(topic) == TOPIC_GREENHOUSE_CLIMATE) {
    handleClimateCommand(doc);
  }
  // Havalandırma kontrolü
  else if (String(topic) == TOPIC_GREENHOUSE_VENTILATION) {
    handleVentilationCommand(doc);
  }
}

// ==================== MQTT KOMUT İŞLEYİCİLERİ ====================

void handleIrrigationCommand(JsonDocument& doc) {
  String action = doc["action"];

  if (action == "start") {
    int zone = doc["zone"];
    int duration = doc["duration"] | 60000;
    startIrrigation(zone, duration);
  }
  else if (action == "stop") {
    int zone = doc["zone"];
    stopIrrigation(zone);
  }
  else if (action == "stop_all") {
    stopAllIrrigation();
  }
  else if (action == "set_auto") {
    autoIrrigationEnabled = doc["enabled"];
    Serial.println(autoIrrigationEnabled ? "Otomatik sulama AÇIK" : "Otomatik sulama KAPALI");
  }
}

void handleClimateCommand(JsonDocument& doc) {
  String action = doc["action"];

  if (action == "set_target_temp") {
    float temp = doc["temperature"];
    setTargetTemperature(temp);
  }
  else if (action == "heater") {
    bool state = doc["state"];
    setHeater(state);
  }
  else if (action == "cooler") {
    bool state = doc["state"];
    setCooler(state);
  }
  else if (action == "set_auto") {
    autoClimateEnabled = doc["enabled"];
    Serial.println(autoClimateEnabled ? "Otomatik iklim AÇIK" : "Otomatik iklim KAPALI");
  }
}

void handleVentilationCommand(JsonDocument& doc) {
  String action = doc["action"];

  if (action == "fan") {
    int speed = doc["speed"];
    setFanSpeed(speed);
  }
  else if (action == "window") {
    int angle = doc["angle"];
    setWindowPosition(angle);
  }
  else if (action == "set_auto") {
    autoVentilationEnabled = doc["enabled"];
    Serial.println(autoVentilationEnabled ? "Otomatik havalandırma AÇIK" : "Otomatik havalandırma KAPALI");
  }
}

// ==================== HTTP SERVER ====================

void setupHTTPServer() {
  server.on("/", handleRoot);
  server.on("/api/sensors", handleAPISensors);
  server.on("/api/status", handleAPIStatus);
  server.on("/api/irrigation", HTTP_POST, handleAPIIrrigation);
  server.on("/api/climate", HTTP_POST, handleAPIClimate);

  server.begin();
  Serial.println("✓ HTTP Server: http://" + WiFi.localIP().toString());
}

void handleRoot() {
  String html = "<html><head><meta charset='UTF-8'></head><body>";
  html += "<h1>🌱 Akıllı Sera Sistemi</h1>";
  html += "<h2>Sensör Değerleri</h2>";
  html += "<p>Sıcaklık: " + String(dhtData.temperature) + "°C</p>";
  html += "<p>Nem: %" + String(dhtData.humidity) + "</p>";
  html += "<p>Işık: %" + String(lightData.lightPercent) + " - " + lightData.lightLevel + "</p>";
  html += "<h2>API Endpoints</h2>";
  html += "<ul>";
  html += "<li>GET /api/sensors - Tüm sensör verileri</li>";
  html += "<li>GET /api/status - Sistem durumu</li>";
  html += "<li>POST /api/irrigation - Sulama kontrolü</li>";
  html += "<li>POST /api/climate - İklim kontrolü</li>";
  html += "</ul>";
  html += "</body></html>";

  server.send(200, "text/html; charset=UTF-8", html);
}

void handleAPISensors() {
  StaticJsonDocument<2048> doc;

  // Sıcaklık/Nem
  JsonObject temp = doc.createNestedObject("temperature_humidity");
  temp["temperature"] = dhtData.temperature;
  temp["humidity"] = dhtData.humidity;
  temp["heat_index"] = dhtData.heatIndex;

  // Toprak nem
  JsonArray soil = doc.createNestedArray("soil_moisture");
  for (int i = 0; i < SOIL_ZONE_COUNT; i++) {
    JsonObject zone = soil.createNestedObject();
    zone["zone"] = i;
    zone["name"] = soilZones[i].zoneName;
    zone["moisture"] = soilZones[i].moisturePercent;
    zone["status"] = getZoneStatus(i);
  }

  // Işık
  JsonObject light = doc.createNestedObject("light");
  light["percent"] = lightData.lightPercent;
  light["level"] = lightData.lightLevel;

  String output;
  serializeJson(doc, output);
  server.send(200, "application/json", output);
}

void handleAPIStatus() {
  String json = getAllSystemsStatusJSON();
  server.send(200, "application/json", json);
}

void handleAPIIrrigation() {
  if (!server.hasArg("plain")) {
    server.send(400, "application/json", "{\"error\":\"No body\"}");
    return;
  }

  String body = server.arg("plain");
  StaticJsonDocument<256> doc;
  deserializeJson(doc, body);

  handleIrrigationCommand(doc);
  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

void handleAPIClimate() {
  if (!server.hasArg("plain")) {
    server.send(400, "application/json", "{\"error\":\"No body\"}");
    return;
  }

  String body = server.arg("plain");
  StaticJsonDocument<256> doc;
  deserializeJson(doc, body);

  handleClimateCommand(doc);
  server.send(200, "application/json", "{\"status\":\"ok\"}");
}
