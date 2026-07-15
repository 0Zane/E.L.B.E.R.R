#include "body.h"

Adafruit_VL53L0X lox = Adafruit_VL53L0X();

int skullstate() {
  uint16_t distance = lox.readRange();

  if (lox.timeoutOccurred()) {
    return 0;
  }

  if (distance < 30) {
    return 1;
  } else if (distance < 40) {
    return 2;
  } else {
    return 3;
  }
}