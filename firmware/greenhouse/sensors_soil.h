/*
 * Akıllı Deneyap Sistemi - Sera Otomasyonu
 * Toprak Nem Sensörü Modülü
 */

#ifndef SENSORS_SOIL_H
#define SENSORS_SOIL_H

// Toprak nem sensörü pinleri (4 zone destekli)
const int SOIL_PINS[] = {36, 39, 34, 35};  // A0, A1, A2, A3
const int SOIL_ZONE_COUNT = 4;

// Kalibrasyon değerleri (sensörünüze göre ayarlayın)
const int SOIL_DRY_VALUE = 3500;      // Kuru toprak (yüksek değer)
const int SOIL_WET_VALUE = 1000;      // Islak toprak (düşük değer)

// Zone isimleri
const String ZONE_NAMES[] = {
  "Domates Bölgesi",
  "Salatalık Bölgesi",
  "Biber Bölgesi",
  "Fide Bölgesi"
};

// Toprak nem verisi
struct SoilData {
  int rawValue;
  int moisturePercent;
  bool needsWatering;
  String zoneName;
  unsigned long lastRead;
};

SoilData soilZones[4];

// Toprak nem sensörlerini başlat
void initSoilSensors() {
  for (int i = 0; i < SOIL_ZONE_COUNT; i++) {
    pinMode(SOIL_PINS[i], INPUT);
    soilZones[i].zoneName = ZONE_NAMES[i];
    soilZones[i].lastRead = 0;
  }
  Serial.println("✓ Toprak nem sensörleri başlatıldı (" + String(SOIL_ZONE_COUNT) + " zone)");
}

// Tek bir zone'dan okuma yap
bool readSoilZone(int zone) {
  if (zone < 0 || zone >= SOIL_ZONE_COUNT) return false;

  int raw = analogRead(SOIL_PINS[zone]);

  // Yüzdelik hesaplama (ters oran: yüksek değer = kuru)
  int percent = map(raw, SOIL_DRY_VALUE, SOIL_WET_VALUE, 0, 100);
  percent = constrain(percent, 0, 100);

  soilZones[zone].rawValue = raw;
  soilZones[zone].moisturePercent = percent;
  soilZones[zone].needsWatering = (percent < 30);  // %30'un altında sulama gerek
  soilZones[zone].lastRead = millis();

  return true;
}

// Tüm zone'ları oku
void readAllSoilZones() {
  for (int i = 0; i < SOIL_ZONE_COUNT; i++) {
    readSoilZone(i);
  }
}

// JSON formatında toprak nem verisi
String getSoilJSON() {
  StaticJsonDocument<1024> doc;
  JsonArray zones = doc.createNestedArray("zones");

  for (int i = 0; i < SOIL_ZONE_COUNT; i++) {
    JsonObject zone = zones.createNestedObject();
    zone["id"] = i;
    zone["name"] = soilZones[i].zoneName;
    zone["moisture"] = soilZones[i].moisturePercent;
    zone["raw"] = soilZones[i].rawValue;
    zone["needs_watering"] = soilZones[i].needsWatering;
    zone["status"] = getZoneStatus(i);
  }

  doc["timestamp"] = millis();

  String output;
  serializeJson(doc, output);
  return output;
}

// Belirli bir zone için JSON
String getSoilZoneJSON(int zone) {
  if (zone < 0 || zone >= SOIL_ZONE_COUNT) return "{}";

  StaticJsonDocument<256> doc;
  doc["zone_id"] = zone;
  doc["zone_name"] = soilZones[zone].zoneName;
  doc["moisture"] = soilZones[zone].moisturePercent;
  doc["raw"] = soilZones[zone].rawValue;
  doc["needs_watering"] = soilZones[zone].needsWatering;
  doc["status"] = getZoneStatus(zone);
  doc["timestamp"] = millis();

  String output;
  serializeJson(doc, output);
  return output;
}

// Zone durumu metni
String getZoneStatus(int zone) {
  int moisture = soilZones[zone].moisturePercent;

  if (moisture < 20) return "Çok Kuru";
  else if (moisture < 40) return "Kuru";
  else if (moisture < 60) return "Normal";
  else if (moisture < 80) return "Nemli";
  else return "Çok Nemli";
}

// Sulama gereken zone'ları kontrol et
bool hasZonesNeedingWater() {
  for (int i = 0; i < SOIL_ZONE_COUNT; i++) {
    if (soilZones[i].needsWatering) return true;
  }
  return false;
}

// Sulama gereken zone listesi
String getZonesNeedingWater() {
  String zones = "";
  for (int i = 0; i < SOIL_ZONE_COUNT; i++) {
    if (soilZones[i].needsWatering) {
      if (zones.length() > 0) zones += ", ";
      zones += soilZones[i].zoneName;
    }
  }
  return zones;
}

#endif
