#include <Arduino.h>

using namespace std;

int nScannedWifi();

struct Wifi {
    char ssid[33];
    int channel;
    int RSSI;
    String encryption;
}


