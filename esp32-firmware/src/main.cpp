//Include system libraries
#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
//Include custom header files
#include "pins.h"
#include "body.h"
#include "temperature.h"
#include "nrf24.h"
#include "wififeatures.h"
#include "led.h"
#include "uart.h"

static bool temperatureReady = false;
static bool skullReady = false;

void setup() {
  Serial.begin(9600);

  Wire.begin(I2C_SDA, I2C_SCL);
  Wire.setClock(400000L);

  temperatureReady = initBME280();
  if (!temperatureReady) {
    Serial.println("BME280 did not start.");
  }

  Serial.println("Starting VL53L0X...");
  skullReady = lox.begin();
  if (!skullReady) {
    Serial.println("VL53L0X did not respond.");
  } else {
    lox.startRangeContinuous();
    delay(100);
    Serial.println("VL53L0X started.");
  }

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  uartBegin();

  ledOn(NRFLED);
  ledOn(OSKULLLED);
  ledOn(CSKULLLED);
  ledOn(NFSKULLLED);
  ledOn(TEMPLED);



}

void loop() {
  uartHandleMessages(temperatureReady, skullReady);
  delay(5);
}
