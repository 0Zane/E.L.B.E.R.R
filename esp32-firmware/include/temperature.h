#include "Adafruit_BME280.h"

extern Adafruit_BME280 bme;

bool initBME280();
float readTemperature();
float readPressure();
float readHumidity();
