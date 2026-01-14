/*
 * Akıllı Deneyap Sistemi - Sera Otomasyonu
 * DHT22 Sıcaklık & Nem Sensörü Modülü
 */

#ifndef SENSORS_DHT22_H
#define SENSORS_DHT22_H

#include <DHT.h>

// DHT22 Pin Konfigürasyonu
#define DHT_PIN 4
#define DHT_TYPE DHT22

// DHT sensör nesnesi
DHT dht(DHT_PIN, DHT_TYPE);

// Sensör verileri
struct DHTData {
  float temperature;
  float humidity;
  float heatIndex;
  bool valid;
  unsigned long lastRead;
};

DHTData dhtData;

// DHT sensörü başlat
void initDHT() {
  dht.begin();
  dhtData.valid = false;
  dhtData.lastRead = 0;
  Serial.println("✓ DHT22 sensörü başlatıldı");
}

// DHT sensöründen veri oku
bool readDHT() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  // Okuma başarısız mı?
  if (isnan(h) || isnan(t)) {
    Serial.println("✗ DHT22 okuma hatası!");
    dhtData.valid = false;
    return false;
  }

  // Heat index hesapla (hissedilen sıcaklık)
  float hi = dht.computeHeatIndex(t, h, false);

  dhtData.temperature = t;
  dhtData.humidity = h;
  dhtData.heatIndex = hi;
  dhtData.valid = true;
  dhtData.lastRead = millis();

  return true;
}

// JSON formatında DHT verisi oluştur
String getDHTJSON() {
  StaticJsonDocument<256> doc;

  doc["temperature"] = round(dhtData.temperature * 10) / 10.0;
  doc["humidity"] = round(dhtData.humidity * 10) / 10.0;
  doc["heatIndex"] = round(dhtData.heatIndex * 10) / 10.0;
  doc["valid"] = dhtData.valid;
  doc["sensor"] = "DHT22";
  doc["unit_temp"] = "C";
  doc["unit_humidity"] = "%";
  doc["timestamp"] = millis();

  String output;
  serializeJson(doc, output);
  return output;
}

// Sıcaklık alarmı kontrolü
bool isTemperatureAlarm(float minTemp, float maxTemp) {
  if (!dhtData.valid) return false;
  return (dhtData.temperature < minTemp || dhtData.temperature > maxTemp);
}

// Nem alarmı kontrolü
bool isHumidityAlarm(float minHumidity, float maxHumidity) {
  if (!dhtData.valid) return false;
  return (dhtData.humidity < minHumidity || dhtData.humidity > maxHumidity);
}

#endif
