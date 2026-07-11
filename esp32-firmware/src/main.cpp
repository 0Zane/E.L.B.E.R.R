//Include system libraries
#include <Arduino.h>
#include <pins.h>

//Include custom header files
#include "body.h"
#include "temperature.h"

bool skullopen = false;

void setup() {
  //initialize UART communication with rp5
  //initialize communications with modules
    Serial.println("Adafruit VL53L0X test.");
  if (!lox.begin()) {
    Serial.println(F("Failed to boot VL53L0X"));
    while(1);
  }
  lox.startRangeContinuous();
}

void loop() {
  //listen to UART from rp5 and send information (maybe direct regular push)
  skullopen = isskullopen();
  //send information to RP5

}
