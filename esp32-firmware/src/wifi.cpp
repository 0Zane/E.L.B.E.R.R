#include <wifi.h>
#include "wififeatures.h"

using namespace std;

byte nScannedWifi(){
    return WiFi.scanNetworks();
}