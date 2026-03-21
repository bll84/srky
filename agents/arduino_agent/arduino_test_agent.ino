/*
 * DeviceProbe - Arduino Test Agent
 *
 * Flash this to your Arduino board to enable full testing via DeviceProbe.
 * Compatible: Uno, Nano, Mega, Leonardo
 *
 * Protocol: Serial JSON command/response
 * Baud: 115200
 *
 * Note: Uses minimal JSON generation (no ArduinoJson to save RAM on AVR)
 */

#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <EEPROM.h>

#define AGENT_VERSION "1.0.0"
#define SERIAL_BAUD 115200
#define MAX_CMD_LEN 128

char cmdBuffer[MAX_CMD_LEN];
int cmdIndex = 0;

// Lightweight JSON helpers for AVR
void jsonStart() { Serial.print(F("{\"status\":\"ok\",\"command\":\"")); }
void jsonStartError() { Serial.print(F("{\"status\":\"error\",\"command\":\"")); }
void jsonDevice() { Serial.print(F("\",\"device\":\"Arduino\",\"data\":{")); }
void jsonEnd() { Serial.println(F("}}")); }

void sendOk(const char* cmd) {
    jsonStart();
    Serial.print(cmd);
    jsonDevice();
}

void sendError(const char* cmd, const char* error) {
    jsonStartError();
    Serial.print(cmd);
    Serial.print(F("\",\"error\":\""));
    Serial.print(error);
    Serial.println(F("\"}"));
}

void handleHello() {
    sendOk("HELLO");
    Serial.print(F("\"agent\":\"arduino_test_agent\",\"version\":\"" AGENT_VERSION "\",\"uptime_ms\":"));
    Serial.print(millis());
    jsonEnd();
}

void handleGetInfo() {
    sendOk("GET_INFO");

    // Detect board type at compile time
    #if defined(__AVR_ATmega328P__)
    Serial.print(F("\"board\":\"Arduino Uno/Nano\",\"mcu\":\"ATmega328P\",\"flash_kb\":32,\"ram_kb\":2,\"eeprom_kb\":1"));
    #elif defined(__AVR_ATmega2560__)
    Serial.print(F("\"board\":\"Arduino Mega 2560\",\"mcu\":\"ATmega2560\",\"flash_kb\":256,\"ram_kb\":8,\"eeprom_kb\":4"));
    #elif defined(__AVR_ATmega32U4__)
    Serial.print(F("\"board\":\"Arduino Leonardo/Micro\",\"mcu\":\"ATmega32U4\",\"flash_kb\":32,\"ram_kb\":2.5,\"eeprom_kb\":1"));
    #else
    Serial.print(F("\"board\":\"Unknown Arduino\",\"mcu\":\"Unknown\""));
    #endif

    Serial.print(F(",\"cpu_freq_mhz\":"));
    Serial.print(F_CPU / 1000000L);
    Serial.print(F(",\"voltage\":\"5V\""));
    jsonEnd();
}

void handleListCapabilities() {
    sendOk("LIST_CAPABILITIES");
    Serial.print(F("\"capabilities\":[\"gpio\",\"adc\",\"pwm\",\"i2c\",\"spi\",\"uart\",\"eeprom\"]"));
    jsonEnd();
}

void handleSetPinMode() {
    int pin = -1;
    char mode[16] = {0};

    char* p = strstr(cmdBuffer, "pin=");
    if (p) pin = atoi(p + 4);
    p = strstr(cmdBuffer, "mode=");
    if (p) {
        int i = 0;
        p += 5;
        while (*p && *p != ' ' && i < 15) mode[i++] = *p++;
        mode[i] = 0;
    }

    if (pin < 0) { sendError("SET_PIN_MODE", "Invalid pin"); return; }

    if (strcmp(mode, "INPUT") == 0) pinMode(pin, INPUT);
    else if (strcmp(mode, "OUTPUT") == 0) pinMode(pin, OUTPUT);
    else if (strcmp(mode, "INPUT_PULLUP") == 0) pinMode(pin, INPUT_PULLUP);
    else { sendError("SET_PIN_MODE", "Invalid mode"); return; }

    sendOk("SET_PIN_MODE");
    Serial.print(F("\"pin\":"));
    Serial.print(pin);
    Serial.print(F(",\"mode\":\""));
    Serial.print(mode);
    Serial.print('"');
    jsonEnd();
}

void handleWritePin() {
    int pin = -1, value = -1;
    char* p = strstr(cmdBuffer, "pin=");
    if (p) pin = atoi(p + 4);
    p = strstr(cmdBuffer, "value=");
    if (p) value = atoi(p + 6);

    if (pin < 0 || value < 0) { sendError("WRITE_PIN", "Invalid params"); return; }

    digitalWrite(pin, value ? HIGH : LOW);

    sendOk("WRITE_PIN");
    Serial.print(F("\"pin\":"));
    Serial.print(pin);
    Serial.print(F(",\"value\":"));
    Serial.print(value);
    jsonEnd();
}

void handleReadPin() {
    int pin = -1;
    char* p = strstr(cmdBuffer, "pin=");
    if (p) pin = atoi(p + 4);

    if (pin < 0) { sendError("READ_PIN", "Invalid pin"); return; }

    int value = digitalRead(pin);
    sendOk("READ_PIN");
    Serial.print(F("\"pin\":"));
    Serial.print(pin);
    Serial.print(F(",\"value\":"));
    Serial.print(value);
    jsonEnd();
}

void handleTestPWM() {
    int pin = -1;
    char* p = strstr(cmdBuffer, "pin=");
    if (p) pin = atoi(p + 4);

    if (pin < 0) { sendError("TEST_PWM", "Invalid pin"); return; }

    analogWrite(pin, 128); // 50% duty
    delay(100);
    analogWrite(pin, 0);

    sendOk("TEST_PWM");
    Serial.print(F("\"pin\":"));
    Serial.print(pin);
    Serial.print(F(",\"duty\":128,\"resolution_bits\":8"));
    jsonEnd();
}

void handleTestADC() {
    int pin = -1;
    char* p = strstr(cmdBuffer, "pin=");
    if (p) pin = atoi(p + 4);

    if (pin < 0) { sendError("TEST_ADC", "Invalid pin"); return; }

    int raw = analogRead(pin);
    float voltage = (raw / 1023.0) * 5.0;

    sendOk("TEST_ADC");
    Serial.print(F("\"pin\":"));
    Serial.print(pin);
    Serial.print(F(",\"raw\":"));
    Serial.print(raw);
    Serial.print(F(",\"voltage\":"));
    Serial.print(voltage, 2);
    Serial.print(F(",\"resolution_bits\":10"));
    jsonEnd();
}

void handleI2CScan() {
    Wire.begin();
    sendOk("RUN_I2C_SCAN");
    Serial.print(F("\"devices\":["));

    int count = 0;
    for (byte addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            if (count > 0) Serial.print(',');
            Serial.print(F("\"0x"));
            if (addr < 16) Serial.print('0');
            Serial.print(addr, HEX);
            Serial.print('"');
            count++;
        }
    }

    Serial.print(F("],\"count\":"));
    Serial.print(count);
    jsonEnd();
}

void handleSPIInit() {
    SPI.begin();
    SPI.end();

    sendOk("RUN_SPI_INIT");
    Serial.print(F("\"spi_initialized\":true"));
    jsonEnd();
}

void handleUARTTest() {
    sendOk("RUN_UART_TEST");
    #if defined(__AVR_ATmega2560__)
    Serial.print(F("\"uart0\":\"in_use\",\"uart1_available\":true,\"uart2_available\":true,\"uart3_available\":true"));
    #else
    Serial.print(F("\"uart0\":\"in_use\",\"note\":\"Only UART0 on this board, used by agent\""));
    #endif
    jsonEnd();
}

void handleEEPROMTest() {
    // Read-write test at address 0 (safe, non-destructive: read, write, restore)
    byte original = EEPROM.read(0);
    byte testVal = (original == 0xAA) ? 0x55 : 0xAA;

    EEPROM.write(0, testVal);
    byte readBack = EEPROM.read(0);
    EEPROM.write(0, original); // Restore original

    bool pass = (readBack == testVal);

    sendOk("TEST_EEPROM");
    Serial.print(F("\"test_passed\":"));
    Serial.print(pass ? "true" : "false");
    Serial.print(F(",\"eeprom_size\":"));
    Serial.print(EEPROM.length());
    jsonEnd();
}

void handleReboot() {
    sendOk("REBOOT");
    Serial.print(F("\"rebooting\":true"));
    jsonEnd();
    delay(100);
    // Software reset via watchdog
    void (*resetFunc)(void) = 0;
    resetFunc();
}

void processCommand() {
    char* cmd = cmdBuffer;
    // Trim leading spaces
    while (*cmd == ' ') cmd++;

    if (strncmp(cmd, "HELLO", 5) == 0) handleHello();
    else if (strncmp(cmd, "GET_INFO", 8) == 0) handleGetInfo();
    else if (strncmp(cmd, "LIST_CAPABILITIES", 17) == 0) handleListCapabilities();
    else if (strncmp(cmd, "SET_PIN_MODE", 12) == 0) handleSetPinMode();
    else if (strncmp(cmd, "WRITE_PIN", 9) == 0) handleWritePin();
    else if (strncmp(cmd, "READ_PIN", 8) == 0) handleReadPin();
    else if (strncmp(cmd, "TEST_PWM", 8) == 0) handleTestPWM();
    else if (strncmp(cmd, "TEST_ADC", 8) == 0) handleTestADC();
    else if (strncmp(cmd, "RUN_I2C_SCAN", 12) == 0) handleI2CScan();
    else if (strncmp(cmd, "RUN_SPI_INIT", 12) == 0) handleSPIInit();
    else if (strncmp(cmd, "RUN_UART_TEST", 13) == 0) handleUARTTest();
    else if (strncmp(cmd, "TEST_EEPROM", 11) == 0) handleEEPROMTest();
    else if (strncmp(cmd, "REBOOT", 6) == 0) handleReboot();
    else sendError("UNKNOWN", "Unknown command");
}

void setup() {
    Serial.begin(SERIAL_BAUD);
    while (!Serial) { delay(10); }
    Serial.println(F("{\"status\":\"ok\",\"command\":\"BOOT\",\"device\":\"Arduino\",\"data\":{\"agent\":\"arduino_test_agent\",\"version\":\"" AGENT_VERSION "\"}}"));
}

void loop() {
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n' || c == '\r') {
            if (cmdIndex > 0) {
                cmdBuffer[cmdIndex] = '\0';
                processCommand();
                cmdIndex = 0;
            }
        } else if (cmdIndex < MAX_CMD_LEN - 1) {
            cmdBuffer[cmdIndex++] = c;
        }
    }
}
