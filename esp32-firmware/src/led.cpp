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

void nrfLED(bool state){
    digitalWrite(NRFLED, state);
}
 
void bmeHotLED(bool state){
    digitalWrite(TEMPLED, state);
}

void skullOpenLED(bool state){
    digitalWrite(OSKULLLED, state);
}

void skullClosedLED(bool state){
    digitalWrite(CSKULLLED, state);
}

void skullFloatingLED(bool state){
    digitalWrite(NFSKULLLED, state);
}
