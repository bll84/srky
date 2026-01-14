/*
 * Akıllı Deneyap Sistemi - Sera Otomasyonu
 * Kontrol Sistemleri (Sulama, Havalandırma, Isıtma/Soğutma)
 */

#ifndef CONTROL_SYSTEMS_H
#define CONTROL_SYSTEMS_H

// ==================== PIN TANIMLARI ====================

// Sulama Sistemi (4 zone)
const int IRRIGATION_PINS[] = {12, 13, 14, 15};  // Röle pinleri
const int IRRIGATION_ZONE_COUNT = 4;

// Havalandırma Sistemi
#define FAN_PIN 25           // Fan kontrolü (PWM)
#define FAN_PWM_CHANNEL 0
#define WINDOW_SERVO_PIN 26  // Servo motor (pencere açma)

// Isıtma/Soğutma Sistemi
#define HEATER_PIN 27        // Isıtıcı röle
#define COOLER_PIN 32        // Soğutucu/Klima röle

// Aydınlatma Sistemi
#define GROW_LIGHT_PIN 33    // Bitki yetiştirme lambası
#define LIGHT_PWM_CHANNEL 1

// ==================== SULAMA SİSTEMİ ====================

struct IrrigationZone {
  int pin;
  bool active;
  unsigned long startTime;
  unsigned long duration;      // Sulama süresi (ms)
  unsigned long lastWatering;  // Son sulama zamanı
  String zoneName;
};

IrrigationZone irrigationZones[4];

// Sulama sistemini başlat
void initIrrigationSystem() {
  for (int i = 0; i < IRRIGATION_ZONE_COUNT; i++) {
    pinMode(IRRIGATION_PINS[i], OUTPUT);
    digitalWrite(IRRIGATION_PINS[i], LOW);

    irrigationZones[i].pin = IRRIGATION_PINS[i];
    irrigationZones[i].active = false;
    irrigationZones[i].duration = 60000;  // Varsayılan 60 saniye
    irrigationZones[i].lastWatering = 0;
    irrigationZones[i].zoneName = ZONE_NAMES[i];
  }
  Serial.println("✓ Sulama sistemi başlatıldı (" + String(IRRIGATION_ZONE_COUNT) + " zone)");
}

// Sulama başlat (belirli zone)
void startIrrigation(int zone, unsigned long duration = 60000) {
  if (zone < 0 || zone >= IRRIGATION_ZONE_COUNT) return;

  digitalWrite(irrigationZones[zone].pin, HIGH);
  irrigationZones[zone].active = true;
  irrigationZones[zone].startTime = millis();
  irrigationZones[zone].duration = duration;

  Serial.println("💧 Sulama başlatıldı: " + irrigationZones[zone].zoneName + " (" + String(duration / 1000) + "s)");
}

// Sulama durdur
void stopIrrigation(int zone) {
  if (zone < 0 || zone >= IRRIGATION_ZONE_COUNT) return;

  digitalWrite(irrigationZones[zone].pin, LOW);
  irrigationZones[zone].active = false;
  irrigationZones[zone].lastWatering = millis();

  Serial.println("💧 Sulama durduruldu: " + irrigationZones[zone].zoneName);
}

// Tüm sulamayı durdur
void stopAllIrrigation() {
  for (int i = 0; i < IRRIGATION_ZONE_COUNT; i++) {
    if (irrigationZones[i].active) {
      stopIrrigation(i);
    }
  }
}

// Sulama timer kontrolü (loop'ta çağrılmalı)
void updateIrrigationSystem() {
  unsigned long currentTime = millis();

  for (int i = 0; i < IRRIGATION_ZONE_COUNT; i++) {
    if (irrigationZones[i].active) {
      // Süre doldu mu?
      if (currentTime - irrigationZones[i].startTime >= irrigationZones[i].duration) {
        stopIrrigation(i);
      }
    }
  }
}

// ==================== HAVALANDIRMA SİSTEMİ ====================

struct VentilationSystem {
  int fanSpeed;        // 0-255 (PWM)
  bool fanActive;
  int windowPosition;  // 0-180 (servo açısı)
  bool autoMode;
};

VentilationSystem ventilation;

// Havalandırma sistemini başlat
void initVentilationSystem() {
  // Fan PWM
  ledcSetup(FAN_PWM_CHANNEL, 25000, 8);  // 25kHz, 8-bit
  ledcAttachPin(FAN_PIN, FAN_PWM_CHANNEL);
  ledcWrite(FAN_PWM_CHANNEL, 0);

  // Servo motor (pencere)
  // ESP32Servo kütüphanesi gerekli
  // myServo.attach(WINDOW_SERVO_PIN);

  ventilation.fanSpeed = 0;
  ventilation.fanActive = false;
  ventilation.windowPosition = 0;
  ventilation.autoMode = true;

  Serial.println("✓ Havalandırma sistemi başlatıldı");
}

// Fan hızı ayarla (0-100%)
void setFanSpeed(int speedPercent) {
  speedPercent = constrain(speedPercent, 0, 100);
  int pwmValue = map(speedPercent, 0, 100, 0, 255);

  ledcWrite(FAN_PWM_CHANNEL, pwmValue);
  ventilation.fanSpeed = speedPercent;
  ventilation.fanActive = (speedPercent > 0);

  Serial.println("🌀 Fan hızı: %" + String(speedPercent));
}

// Pencere açısı ayarla (0-180 derece)
void setWindowPosition(int angle) {
  angle = constrain(angle, 0, 180);
  // myServo.write(angle);
  ventilation.windowPosition = angle;

  Serial.println("🪟 Pencere açısı: " + String(angle) + "°");
}

// Otomatik havalandırma kontrolü
void autoVentilationControl(float temperature, float humidity) {
  if (!ventilation.autoMode) return;

  // Sıcaklık kontrolü
  if (temperature > 30) {
    setFanSpeed(100);  // Maksimum havalandırma
    setWindowPosition(90);  // Pencere yarı açık
  } else if (temperature > 26) {
    setFanSpeed(60);
    setWindowPosition(45);
  } else if (temperature < 18) {
    setFanSpeed(0);   // Fan kapat
    setWindowPosition(0);  // Pencere kapat
  } else {
    setFanSpeed(30);  // Düşük havalandırma
    setWindowPosition(20);
  }

  // Nem kontrolü
  if (humidity > 80) {
    setFanSpeed(max(ventilation.fanSpeed, 70));  // Yüksek nem, güçlü havalandırma
  }
}

// ==================== ISITMA/SOĞUTMA SİSTEMİ ====================

struct ClimateControl {
  bool heaterActive;
  bool coolerActive;
  float targetTemp;
  float hysteresis;  // Histerezis (±1°C)
};

ClimateControl climate;

// Isıtma/Soğutma sistemini başlat
void initClimateControl() {
  pinMode(HEATER_PIN, OUTPUT);
  pinMode(COOLER_PIN, OUTPUT);
  digitalWrite(HEATER_PIN, LOW);
  digitalWrite(COOLER_PIN, LOW);

  climate.heaterActive = false;
  climate.coolerActive = false;
  climate.targetTemp = 24.0;  // Varsayılan hedef sıcaklık
  climate.hysteresis = 1.0;

  Serial.println("✓ İklim kontrol sistemi başlatıldı");
}

// Hedef sıcaklık ayarla
void setTargetTemperature(float temp) {
  climate.targetTemp = temp;
  Serial.println("🌡️ Hedef sıcaklık: " + String(temp) + "°C");
}

// Isıtıcı kontrolü
void setHeater(bool state) {
  digitalWrite(HEATER_PIN, state ? HIGH : LOW);
  climate.heaterActive = state;

  if (state) {
    // Soğutma varsa kapat (çakışma önleme)
    if (climate.coolerActive) {
      setCooler(false);
    }
  }

  Serial.println(state ? "🔥 Isıtıcı AÇIK" : "🔥 Isıtıcı KAPALI");
}

// Soğutucu kontrolü
void setCooler(bool state) {
  digitalWrite(COOLER_PIN, state ? HIGH : LOW);
  climate.coolerActive = state;

  if (state) {
    // Isıtma varsa kapat (çakışma önleme)
    if (climate.heaterActive) {
      setHeater(false);
    }
  }

  Serial.println(state ? "❄️ Soğutucu AÇIK" : "❄️ Soğutucu KAPALI");
}

// Otomatik iklim kontrolü
void autoClimateControl(float currentTemp) {
  float lowerBound = climate.targetTemp - climate.hysteresis;
  float upperBound = climate.targetTemp + climate.hysteresis;

  // Sıcaklık çok düşük
  if (currentTemp < lowerBound && !climate.heaterActive) {
    setHeater(true);
  }
  // Sıcaklık hedefin üstüne çıktı
  else if (currentTemp > climate.targetTemp && climate.heaterActive) {
    setHeater(false);
  }

  // Sıcaklık çok yüksek
  if (currentTemp > upperBound && !climate.coolerActive) {
    setCooler(true);
  }
  // Sıcaklık hedefin altına indi
  else if (currentTemp < climate.targetTemp && climate.coolerActive) {
    setCooler(false);
  }
}

// ==================== AYDINLATMA SİSTEMİ ====================

struct GrowLightSystem {
  bool active;
  int brightness;  // 0-100%
  unsigned long onTime;
  unsigned long offTime;
  bool autoMode;
};

GrowLightSystem growLight;

// Aydınlatma sistemini başlat
void initGrowLightSystem() {
  ledcSetup(LIGHT_PWM_CHANNEL, 5000, 8);  // 5kHz, 8-bit
  ledcAttachPin(GROW_LIGHT_PIN, LIGHT_PWM_CHANNEL);
  ledcWrite(LIGHT_PWM_CHANNEL, 0);

  growLight.active = false;
  growLight.brightness = 0;
  growLight.autoMode = true;

  Serial.println("✓ Bitki aydınlatma sistemi başlatıldı");
}

// Aydınlatma parlaklığı ayarla (0-100%)
void setGrowLightBrightness(int brightnessPercent) {
  brightnessPercent = constrain(brightnessPercent, 0, 100);
  int pwmValue = map(brightnessPercent, 0, 100, 0, 255);

  ledcWrite(LIGHT_PWM_CHANNEL, pwmValue);
  growLight.brightness = brightnessPercent;
  growLight.active = (brightnessPercent > 0);

  Serial.println("💡 Aydınlatma: %" + String(brightnessPercent));
}

// Otomatik aydınlatma kontrolü
void autoGrowLightControl(int lightPercent, int hour) {
  if (!growLight.autoMode) return;

  bool isDaytime = (hour >= 6 && hour <= 18);

  if (isDaytime && lightPercent < 30) {
    // Gündüz ama ışık yetersiz
    setGrowLightBrightness(80);
  } else if (isDaytime && lightPercent < 50) {
    // Gündüz, ışık az
    setGrowLightBrightness(50);
  } else {
    // Gece veya yeterli doğal ışık var
    setGrowLightBrightness(0);
  }
}

// ==================== DURUM RAPORLAMA ====================

// Tüm sistem durumunu JSON olarak al
String getAllSystemsStatusJSON() {
  StaticJsonDocument<1024> doc;

  // Sulama
  JsonArray irrigation = doc.createNestedArray("irrigation");
  for (int i = 0; i < IRRIGATION_ZONE_COUNT; i++) {
    JsonObject zone = irrigation.createNestedObject();
    zone["id"] = i;
    zone["name"] = irrigationZones[i].zoneName;
    zone["active"] = irrigationZones[i].active;
  }

  // Havalandırma
  JsonObject vent = doc.createNestedObject("ventilation");
  vent["fan_speed"] = ventilation.fanSpeed;
  vent["fan_active"] = ventilation.fanActive;
  vent["window_position"] = ventilation.windowPosition;

  // İklim kontrolü
  JsonObject clim = doc.createNestedObject("climate");
  clim["heater"] = climate.heaterActive;
  clim["cooler"] = climate.coolerActive;
  clim["target_temp"] = climate.targetTemp;

  // Aydınlatma
  JsonObject light = doc.createNestedObject("grow_light");
  light["active"] = growLight.active;
  light["brightness"] = growLight.brightness;

  doc["timestamp"] = millis();

  String output;
  serializeJson(doc, output);
  return output;
}

#endif
