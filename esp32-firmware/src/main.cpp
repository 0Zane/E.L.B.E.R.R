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
#include "led.h"

string receivedMessage = "";

void setup() {


  Serial.begin(9600);

  /*
  Wire.begin(I2C_SDA, I2C_SCL);
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
    */

  ledOn(NRFLED);
  ledOn(OSKULLLED);
  ledOn(CSKULLLED);
  ledOn(NFSKULLLED);
  ledOn(TEMPLED);



}

void loop() {
  Serial.print("Hello");
  delay(1000);
}
