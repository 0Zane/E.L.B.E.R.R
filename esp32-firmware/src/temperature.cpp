#include <Arduino.h>
#include "Adafruit_BME280.h"
#include <Wire.h>
#include "temperature.h"

Adafruit_BME280 bme;

bool initBME280() {
    if (!bme.begin(0x76, &Wire)) {
        Serial.println("Could not find a valid BME280 sensor, check wiring and I2C address.");
        return false;
    }

    bme.setSampling(
        Adafruit_BME280::MODE_FORCED,
        Adafruit_BME280::SAMPLING_X2,
        Adafruit_BME280::SAMPLING_X16,
        Adafruit_BME280::SAMPLING_X16,
        Adafruit_BME280::FILTER_X16,
        Adafruit_BME280::STANDBY_MS_1000);

    return true;
}

float readTemperature(){
    bme.takeForcedMeasurement();
    return bme.readTemperature();
}


float readHumidity(){
    bme.takeForcedMeasurement();
    return bme.readHumidity();
}