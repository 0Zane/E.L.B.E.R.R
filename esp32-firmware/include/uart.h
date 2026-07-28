#include <Arduino.h>

void uartBegin();
void uartSendTemperature();
void uartSendHumidity();
void uartSendSkullState();
void uartSendNWifi()
void uartSendWifiSSID();

String uartReadMessage();