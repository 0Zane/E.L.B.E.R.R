#include <Arduino.h>
#include <HardwareSerial.h>
#include "pins.h"
#include "temperature.h"
#include "body.h"
#include "wififeatures.h"

HardwareSerial rp5Serial(2);

void uartBegin(){
    
    rp5Serial.begin(115200, SERIAL_8N1, UART1_RX_PIN, UART1_TX_PIN);
}
void uartSendTemperature(){
    rp5Serial.print(readTemperature());
}

void uartSendHumidity(){
    rp5Serial.print(readHumidity());
}

void uartSendSkullState(){
    rp5Serial.print(skullstate());
}
void uartSendNWifi(){
    rp5Serial.print(nScannedWifi());
}
void uartSendWifiSSID(){
    rp5Serial.print("wifinames()");
}

String uartReadMessage();