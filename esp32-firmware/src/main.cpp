//Include system libraries
#include <Arduino.h>
#include <Wire.h>
#include <string>
//Include custom header files
#include "pins.h"
#include "body.h"
#include "temperature.h"
#include "nrf24.h"
#include "wififeatures.h"

string receivedMessage = "";

void setup() {


  Serial.begin(9600);
  Wire.begin(SDA, SCL);
  Wire.setClock(400000L);

  if (!initBME280()) {
    Serial.println("BME280 did not start.");
  }

  Serial.println("Starting VL53L0X...");
  if (!lox.begin()) {
    Serial.println("VL53L0X did not respond.");
  } else {
    lox.startRangeContinuous();
    delay(100);
    Serial.println("VL53L0X started.");
  }
}

void loop() {
  Serial.println(skullstate());
  Serial.println(readTemperature());
  Serial.println(readHumidity());
  Serial.println("Scanned wifis:");
  Serial.println(nScannedWifi());
  delay(1000);
}
