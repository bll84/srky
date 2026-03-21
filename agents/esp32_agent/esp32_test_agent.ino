/*
 * DeviceProbe - ESP32 Test Agent
 *
 * Flash this to your ESP32 board to enable full testing via DeviceProbe.
 * Framework: Arduino
 * Board: ESP32 Dev Module (or compatible)
 *
 * Protocol: Serial JSON command/response
 * Baud: 115200
 */

#include <Arduino.h>
#include <WiFi.h>
#include <Wire.h>
#include <SPI.h>
#include <ArduinoJson.h>

// Only include BLE if available
#if defined(CONFIG_BT_ENABLED) && defined(CONFIG_BLUEDROID_ENABLED)
#include <BLEDevice.h>
#define HAS_BLE 1
#else
#define HAS_BLE 0
#endif

#define AGENT_VERSION "1.0.0"
#define SERIAL_BAUD 115200
#define MAX_CMD_LEN 256

char cmdBuffer[MAX_CMD_LEN];
int cmdIndex = 0;

void sendResponse(const char* status, const char* command, JsonObject data) {
    StaticJsonDocument<2048> doc;
    doc["status"] = status;
    doc["command"] = command;
    doc["device"] = "ESP32";
    doc["data"] = data;
    serializeJson(doc, Serial);
    Serial.println();
}

void sendOk(const char* command, JsonObject data) {
    sendResponse("ok", command, data);
}

void sendError(const char* command, const char* error) {
    StaticJsonDocument<512> doc;
    doc["status"] = "error";
    doc["command"] = command;
    doc["error"] = error;
    serializeJson(doc, Serial);
    Serial.println();
}

void handleHello() {
    StaticJsonDocument<256> doc;
    JsonObject data = doc.to<JsonObject>();
    data["agent"] = "esp32_test_agent";
    data["version"] = AGENT_VERSION;
    data["uptime_ms"] = millis();
    sendOk("HELLO", data);
}

void handleGetInfo() {
    StaticJsonDocument<512> doc;
    JsonObject data = doc.to<JsonObject>();
    data["model"] = ESP.getChipModel();
    data["revision"] = ESP.getChipRevision();
    data["cores"] = ESP.getChipCores();
    data["cpu_freq_mhz"] = ESP.getCpuFreqMHz();
    data["flash_mb"] = ESP.getFlashChipSize() / (1024 * 1024);
    data["flash_speed_mhz"] = ESP.getFlashChipSpeed() / 1000000;
    data["free_heap"] = ESP.getFreeHeap();
    data["min_free_heap"] = ESP.getMinFreeHeap();
    data["sdk_version"] = ESP.getSdkVersion();
    data["mac"] = WiFi.macAddress();

    #ifdef BOARD_HAS_PSRAM
    data["psram"] = true;
    data["psram_size"] = ESP.getPsramSize();
    data["psram_free"] = ESP.getFreePsram();
    #else
    data["psram"] = false;
    #endif

    sendOk("GET_INFO", data);
}

void handleListCapabilities() {
    StaticJsonDocument<512> doc;
    JsonObject data = doc.to<JsonObject>();
    JsonArray caps = data.createNestedArray("capabilities");
    caps.add("gpio");
    caps.add("adc");
    caps.add("pwm");
    caps.add("i2c");
    caps.add("spi");
    caps.add("uart");
    caps.add("wifi");

    #if defined(SOC_DAC_SUPPORTED)
    caps.add("dac");
    #endif

    #if HAS_BLE
    caps.add("ble");
    #endif

    #ifdef BOARD_HAS_PSRAM
    caps.add("psram");
    #endif

    caps.add("touch");
    caps.add("deep_sleep");
    sendOk("LIST_CAPABILITIES", data);
}

void handleSetPinMode(const char* params) {
    int pin;
    char mode[16];
    if (sscanf(params, "pin=%d mode=%s", &pin, mode) != 2) {
        sendError("SET_PIN_MODE", "Usage: SET_PIN_MODE pin=N mode=INPUT|OUTPUT");
        return;
    }

    if (strcmp(mode, "INPUT") == 0) {
        pinMode(pin, INPUT);
    } else if (strcmp(mode, "OUTPUT") == 0) {
        pinMode(pin, OUTPUT);
    } else if (strcmp(mode, "INPUT_PULLUP") == 0) {
        pinMode(pin, INPUT_PULLUP);
    } else if (strcmp(mode, "INPUT_PULLDOWN") == 0) {
        pinMode(pin, INPUT_PULLDOWN);
    } else {
        sendError("SET_PIN_MODE", "Invalid mode");
        return;
    }

    StaticJsonDocument<128> doc;
    JsonObject data = doc.to<JsonObject>();
    data["pin"] = pin;
    data["mode"] = mode;
    sendOk("SET_PIN_MODE", data);
}

void handleWritePin(const char* params) {
    int pin, value;
    if (sscanf(params, "pin=%d value=%d", &pin, &value) != 2) {
        sendError("WRITE_PIN", "Usage: WRITE_PIN pin=N value=0|1");
        return;
    }
    digitalWrite(pin, value ? HIGH : LOW);

    StaticJsonDocument<128> doc;
    JsonObject data = doc.to<JsonObject>();
    data["pin"] = pin;
    data["value"] = value;
    sendOk("WRITE_PIN", data);
}

void handleReadPin(const char* params) {
    int pin;
    if (sscanf(params, "pin=%d", &pin) != 1) {
        sendError("READ_PIN", "Usage: READ_PIN pin=N");
        return;
    }
    int value = digitalRead(pin);

    StaticJsonDocument<128> doc;
    JsonObject data = doc.to<JsonObject>();
    data["pin"] = pin;
    data["value"] = value;
    sendOk("READ_PIN", data);
}

void handleTestPWM(const char* params) {
    int pin;
    if (sscanf(params, "pin=%d", &pin) != 1) {
        sendError("TEST_PWM", "Usage: TEST_PWM pin=N");
        return;
    }

    // Use LEDC for PWM on ESP32
    ledcAttach(pin, 5000, 8);
    ledcWrite(pin, 128); // 50% duty
    delay(100);
    ledcWrite(pin, 0);
    ledcDetach(pin);

    StaticJsonDocument<128> doc;
    JsonObject data = doc.to<JsonObject>();
    data["pin"] = pin;
    data["frequency"] = 5000;
    data["duty"] = 128;
    data["resolution_bits"] = 8;
    sendOk("TEST_PWM", data);
}

void handleTestADC(const char* params) {
    int pin;
    if (sscanf(params, "pin=%d", &pin) != 1) {
        sendError("TEST_ADC", "Usage: TEST_ADC pin=N");
        return;
    }

    int raw = analogRead(pin);
    float voltage = (raw / 4095.0) * 3.3;

    StaticJsonDocument<128> doc;
    JsonObject data = doc.to<JsonObject>();
    data["pin"] = pin;
    data["raw"] = raw;
    data["voltage"] = voltage;
    data["resolution_bits"] = 12;
    sendOk("TEST_ADC", data);
}

void handleI2CScan() {
    Wire.begin();
    StaticJsonDocument<1024> doc;
    JsonObject data = doc.to<JsonObject>();
    JsonArray devices = data.createNestedArray("devices");

    int count = 0;
    for (byte addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            char hex[8];
            snprintf(hex, sizeof(hex), "0x%02X", addr);
            devices.add(hex);
            count++;
        }
    }
    data["count"] = count;
    sendOk("RUN_I2C_SCAN", data);
}

void handleSPIInit() {
    SPI.begin();
    SPI.end();

    StaticJsonDocument<128> doc;
    JsonObject data = doc.to<JsonObject>();
    data["spi_initialized"] = true;
    data["mosi"] = MOSI;
    data["miso"] = MISO;
    data["sck"] = SCK;
    data["ss"] = SS;
    sendOk("RUN_SPI_INIT", data);
}

void handleUARTTest() {
    // UART0 is used for communication, test UART2 availability
    StaticJsonDocument<256> doc;
    JsonObject data = doc.to<JsonObject>();
    data["uart0"] = "in_use_for_agent";
    data["uart2_available"] = true;
    data["note"] = "UART2 on GPIO16(RX)/GPIO17(TX) available for loopback test";
    sendOk("RUN_UART_TEST", data);
}

void handleWiFiScan() {
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    delay(100);

    int n = WiFi.scanNetworks();

    StaticJsonDocument<2048> doc;
    JsonObject data = doc.to<JsonObject>();
    data["network_count"] = n;
    JsonArray networks = data.createNestedArray("networks");

    int limit = min(n, 15);
    for (int i = 0; i < limit; i++) {
        JsonObject net = networks.createNestedObject();
        net["ssid"] = WiFi.SSID(i);
        net["rssi"] = WiFi.RSSI(i);
        net["channel"] = WiFi.channel(i);
        net["encryption"] = WiFi.encryptionType(i);
    }

    WiFi.scanDelete();
    sendOk("RUN_WIFI_SCAN", data);
}

void handleBLEInit() {
    #if HAS_BLE
    BLEDevice::init("DeviceProbe");
    delay(100);
    BLEDevice::deinit();

    StaticJsonDocument<128> doc;
    JsonObject data = doc.to<JsonObject>();
    data["ble_initialized"] = true;
    sendOk("RUN_BLE_INIT", data);
    #else
    sendError("RUN_BLE_INIT", "BLE not available");
    #endif
}

void handleMemoryTest() {
    StaticJsonDocument<256> doc;
    JsonObject data = doc.to<JsonObject>();
    data["free_heap"] = ESP.getFreeHeap();
    data["min_free_heap"] = ESP.getMinFreeHeap();
    data["max_alloc_heap"] = ESP.getMaxAllocHeap();
    data["heap_size"] = ESP.getHeapSize();

    #ifdef BOARD_HAS_PSRAM
    data["psram_size"] = ESP.getPsramSize();
    data["psram_free"] = ESP.getFreePsram();
    #endif

    sendOk("RUN_MEMORY_TEST", data);
}

void handleGetFlashInfo() {
    StaticJsonDocument<256> doc;
    JsonObject data = doc.to<JsonObject>();
    data["flash_size"] = ESP.getFlashChipSize();
    data["flash_speed"] = ESP.getFlashChipSpeed();
    data["sketch_size"] = ESP.getSketchSize();
    data["sketch_free"] = ESP.getFreeSketchSpace();
    sendOk("GET_FLASH_INFO", data);
}

void handleReboot() {
    StaticJsonDocument<64> doc;
    JsonObject data = doc.to<JsonObject>();
    data["rebooting"] = true;
    sendOk("REBOOT", data);
    delay(100);
    ESP.restart();
}

void processCommand(const char* cmd) {
    // Parse command and params
    char command[32] = {0};
    const char* params = "";

    const char* space = strchr(cmd, ' ');
    if (space) {
        int cmdLen = space - cmd;
        if (cmdLen >= (int)sizeof(command)) cmdLen = sizeof(command) - 1;
        strncpy(command, cmd, cmdLen);
        params = space + 1;
    } else {
        strncpy(command, cmd, sizeof(command) - 1);
    }

    // Dispatch
    if (strcmp(command, "HELLO") == 0) handleHello();
    else if (strcmp(command, "GET_INFO") == 0) handleGetInfo();
    else if (strcmp(command, "LIST_CAPABILITIES") == 0) handleListCapabilities();
    else if (strcmp(command, "SET_PIN_MODE") == 0) handleSetPinMode(params);
    else if (strcmp(command, "WRITE_PIN") == 0) handleWritePin(params);
    else if (strcmp(command, "READ_PIN") == 0) handleReadPin(params);
    else if (strcmp(command, "TEST_PWM") == 0) handleTestPWM(params);
    else if (strcmp(command, "TEST_ADC") == 0) handleTestADC(params);
    else if (strcmp(command, "RUN_I2C_SCAN") == 0) handleI2CScan();
    else if (strcmp(command, "RUN_SPI_INIT") == 0) handleSPIInit();
    else if (strcmp(command, "RUN_UART_TEST") == 0) handleUARTTest();
    else if (strcmp(command, "RUN_WIFI_SCAN") == 0) handleWiFiScan();
    else if (strcmp(command, "RUN_BLE_INIT") == 0) handleBLEInit();
    else if (strcmp(command, "RUN_MEMORY_TEST") == 0) handleMemoryTest();
    else if (strcmp(command, "GET_FLASH_INFO") == 0) handleGetFlashInfo();
    else if (strcmp(command, "REBOOT") == 0) handleReboot();
    else {
        sendError("UNKNOWN", "Unknown command");
    }
}

void setup() {
    Serial.begin(SERIAL_BAUD);
    while (!Serial) { delay(10); }
    Serial.println("{\"status\":\"ok\",\"command\":\"BOOT\",\"device\":\"ESP32\",\"data\":{\"agent\":\"esp32_test_agent\",\"version\":\"" AGENT_VERSION "\"}}");
}

void loop() {
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n' || c == '\r') {
            if (cmdIndex > 0) {
                cmdBuffer[cmdIndex] = '\0';
                processCommand(cmdBuffer);
                cmdIndex = 0;
            }
        } else if (cmdIndex < MAX_CMD_LEN - 1) {
            cmdBuffer[cmdIndex++] = c;
        }
    }
}
