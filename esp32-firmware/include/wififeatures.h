#include <Arduino.h>

using namespace std;

int nScannedWifi();

array<String,10> wifinames();

struct Wifi {
    char ssid[33];
    int channel;
    int RSSI;
    String encryption;
};


