/*
 * Akıllı Deneyap Sistemi - Sera Otomasyonu
 * Işık Sensörü (LDR) Modülü
 */

#ifndef SENSORS_LIGHT_H
#define SENSORS_LIGHT_H

// Işık sensörü pin
#define LIGHT_SENSOR_PIN 39  // A1

// Kalibrasyon değerleri
#define LIGHT_DARK_VALUE 3000    // Karanlık
#define LIGHT_BRIGHT_VALUE 500   // Aydınlık

// Işık seviyeleri
struct LightData {
  int rawValue;
  int lightPercent;
  String lightLevel;
  bool needsLight;
  unsigned long lastRead;
};

LightData lightData;

// Işık sensörünü başlat
void initLightSensor() {
  pinMode(LIGHT_SENSOR_PIN, INPUT);
  lightData.lastRead = 0;
  Serial.println("✓ Işık sensörü (LDR) başlatıldı");
}

// Işık sensöründen okuma
bool readLightSensor() {
  int raw = analogRead(LIGHT_SENSOR_PIN);

  // Yüzdelik hesaplama (ters oran: yüksek değer = karanlık)
  int percent = map(raw, LIGHT_DARK_VALUE, LIGHT_BRIGHT_VALUE, 0, 100);
  percent = constrain(percent, 0, 100);

  lightData.rawValue = raw;
  lightData.lightPercent = percent;
  lightData.lightLevel = getLightLevelText(percent);
  lightData.needsLight = (percent < 30);  // %30'un altında ışık gerekli
  lightData.lastRead = millis();

  return true;
}

// Işık seviyesi metni
String getLightLevelText(int percent) {
  if (percent < 20) return "Çok Karanlık";
  else if (percent < 40) return "Karanlık";
  else if (percent < 60) return "Normal";
  else if (percent < 80) return "Aydınlık";
  else return "Çok Aydınlık";
}

// JSON formatında ışık verisi
String getLightJSON() {
  StaticJsonDocument<256> doc;

  doc["light_percent"] = lightData.lightPercent;
  doc["raw"] = lightData.rawValue;
  doc["level"] = lightData.lightLevel;
  doc["needs_light"] = lightData.needsLight;
  doc["sensor"] = "LDR";
  doc["timestamp"] = millis();

  // Gün saatine göre öneriler
  int hour = getHourOfDay();  // Bu fonksiyonu implement etmeniz gerekir
  doc["is_daytime"] = (hour >= 6 && hour <= 18);

  String output;
  serializeJson(doc, output);
  return output;
}

// Yapay aydınlatma gerekli mi?
bool needsArtificialLight() {
  // Gündüz ve ışık yetersizse
  int hour = getHourOfDay();
  bool isDaytime = (hour >= 6 && hour <= 18);

  return isDaytime && lightData.needsLight;
}

// Gece modu mu?
bool isNightTime() {
  int hour = getHourOfDay();
  return (hour < 6 || hour > 20);
}

// Saat bilgisi (NTP ile implement edilmeli)
int getHourOfDay() {
  // Gerçek implementasyonda NTP kullanılmalı
  // Şimdilik basit bir yaklaşım
  return (millis() / 3600000) % 24;
}

// Günlük ışık saati hesapla (DLI - Daily Light Integral)
struct DailyLightStats {
  int totalMinutesAboveThreshold;
  int averageLightPercent;
  bool sufficientLight;
};

DailyLightStats dailyLightStats;

// Günlük ışık istatistiklerini güncelle
void updateDailyLightStats() {
  // Bu fonksiyon her dakika çağrılmalı
  static int minuteCounter = 0;
  static long totalLight = 0;

  if (lightData.lightPercent > 40) {
    dailyLightStats.totalMinutesAboveThreshold++;
  }

  totalLight += lightData.lightPercent;
  minuteCounter++;

  if (minuteCounter > 0) {
    dailyLightStats.averageLightPercent = totalLight / minuteCounter;
  }

  // Günde en az 8 saat yeterli ışık olmalı
  dailyLightStats.sufficientLight = (dailyLightStats.totalMinutesAboveThreshold >= 480);
}

// Günlük ışık istatistiklerini sıfırla (her gece yarısı)
void resetDailyLightStats() {
  dailyLightStats.totalMinutesAboveThreshold = 0;
  dailyLightStats.averageLightPercent = 0;
  dailyLightStats.sufficientLight = false;
}

#endif
