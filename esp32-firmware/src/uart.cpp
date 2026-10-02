#include <Arduino.h>
#include <HardwareSerial.h>
#include <math.h>
#include <WiFi.h>

#include "pins.h"
#include "temperature.h"
#include "body.h"
#include "wififeatures.h"

HardwareSerial rp5Serial(2);

void uartBegin() {
    rp5Serial.begin(115200, SERIAL_8N1, UART1_RX_PIN, UART1_TX_PIN);
    rp5Serial.setTimeout(50);
}

static void sendResponse(int command, bool ok, const String& fields = "") {
    rp5Serial.printf(
        "{\"cmd\":%d,\"ok\":%s%s}\n",
        command,
        ok ? "true" : "false",
        fields.c_str());
}

static String readSkullState(bool skullReady) {
    if (!skullReady) {
        return "unavailable";
    }

    switch (skullstate()) {
        case 1:
            return "closed";
        case 2:
            return "nonfixed";
        case 3:
            return "open";
        default:
            return "unknown";
    }
}

static String readTemperatureField(bool temperatureReady) {
    if (!temperatureReady) {
        return "null";
    }

    const float temperature = readTemperature();
    if (!isfinite(temperature)) {
        return "null";
    }
    return String(temperature, 1);
}

static void sendDiagnosis(bool temperatureReady, bool skullReady) {
    const int wifiCount = nScannedWifi();
    const String temperature = readTemperatureField(temperatureReady);
    const String skull = readSkullState(skullReady);
    String fields = ",\"connected\":true,\"skull_state\":\"" + skull +
                    "\",\"temperature_c\":" + temperature +
                    ",\"wifi_count\":";
    fields += wifiCount >= 0 ? String(wifiCount) : "null";
    sendResponse(1, true, fields);
}

void uartHandleMessages(bool temperatureReady, bool skullReady) {
    while (rp5Serial.available() > 0) {
        String message = rp5Serial.readStringUntil('\n');
        message.trim();
        if (message.length() != 1 || message[0] < '0' || message[0] > '4') {
            continue;
        }

        const int command = message[0] - '0';
        switch (command) {
            case 0:
                sendResponse(0, true, ",\"connected\":true");
                break;
            case 1:
                sendDiagnosis(temperatureReady, skullReady);
                break;
            case 2:
                if (skullReady) {
                    sendResponse(
                        2,
                        true,
                        ",\"skull_state\":\"" + readSkullState(skullReady) + "\"");
                } else {
                    sendResponse(2, false, ",\"error\":\"sensor_unavailable\"");
                }
                break;
            case 3:
                if (temperatureReady) {
                    const String temperature = readTemperatureField(temperatureReady);
                    if (temperature != "null") {
                        sendResponse(3, true, ",\"temperature_c\":" + temperature);
                        break;
                    }
                }
                sendResponse(3, false, ",\"error\":\"sensor_unavailable\"");
                break;
            case 4: {
                const int wifiCount = nScannedWifi();
                if (wifiCount >= 0) {
                    sendResponse(4, true, ",\"wifi_count\":" + String(wifiCount));
                } else {
                    sendResponse(4, false, ",\"error\":\"wifi_scan_failed\"");
                }
                break;
            }
        }
    }
}