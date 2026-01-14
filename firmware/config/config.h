/*
 * Akıllı Deneyap Sistemi
 * Konfigürasyon Dosyası
 */

#ifndef CONFIG_H
#define CONFIG_H

// WiFi Ayarları
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define WIFI_TIMEOUT 20000  // 20 saniye

// MQTT Ayarları
#define MQTT_BROKER "YOUR_MQTT_BROKER_IP"  // Örn: "192.168.1.100" veya "mqtt.example.com"
#define MQTT_PORT 1883
#define MQTT_USER "YOUR_MQTT_USER"         // Opsiyonel
#define MQTT_PASSWORD "YOUR_MQTT_PASSWORD" // Opsiyonel
#define MQTT_CLIENT_ID "deneyap-kart-01"
#define MQTT_KEEPALIVE 60

// MQTT Topic'leri
#define TOPIC_TEMP "deneyap/sensors/temperature"
#define TOPIC_ANALOG "deneyap/sensors/analog"
#define TOPIC_DIGITAL "deneyap/gpio/digital"
#define TOPIC_CONTROL_GPIO "deneyap/control/gpio"
#define TOPIC_CONTROL_PWM "deneyap/control/pwm"
#define TOPIC_STATUS "deneyap/status"
#define TOPIC_TOUCH "deneyap/sensors/touch"

// HTTP REST API Ayarları
#define HTTP_PORT 80
#define API_ENABLED true

// Sensör Güncelleme Aralıkları (ms)
#define TEMP_UPDATE_INTERVAL 5000      // Her 5 saniye
#define ANALOG_UPDATE_INTERVAL 2000    // Her 2 saniye
#define DIGITAL_UPDATE_INTERVAL 1000   // Her 1 saniye
#define TOUCH_UPDATE_INTERVAL 500      // Her 500ms

// Pin Tanımlamaları (Örnekler)
#define LED_PIN 13
#define RELAY_PIN 12
#define BUZZER_PIN 14

// Analog Pin'ler
#define ANALOG_PIN_1 A0
#define ANALOG_PIN_2 A1
#define ANALOG_PIN_3 A2

// Touch Pin'ler
#define TOUCH_PIN_1 T1
#define TOUCH_PIN_2 T2
#define TOUCH_PIN_3 T3

// PWM Ayarları
#define PWM_FREQ 5000
#define PWM_RESOLUTION 8  // 0-255

// Debug Modu
#define DEBUG_MODE true
#define DEBUG_SERIAL_SPEED 115200

// Cihaz Bilgileri
#define DEVICE_NAME "Deneyap Kart 1A v2"
#define FIRMWARE_VERSION "1.0.0"
#define DEVICE_ID "DK1A-001"

#endif
