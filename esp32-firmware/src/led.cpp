#include "led.h"
#include "pins.h"
#include "Arduino.h"

void initPins(){
    pinMode(1, OUTPUT);
    pinMode(2, OUTPUT);
    pinMode(3, OUTPUT);
    pinMode(4, OUTPUT);
    pinMode(7, OUTPUT);
}

void ledOn(int PIN){
    digitalWrite(PIN, 1);
}
void ledOff(int PIN){
    digitalWrite(PIN, 0);
}
