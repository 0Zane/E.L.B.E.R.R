#include <wifi.h>
#include "wififeatures.h"
#include <array>

using namespace std;

int nScannedWifi(){
    return WiFi.scanNetworks();
}

array<String,10> wifinames(int nWifi){
    String names[nWifi];
    for (int i = 0; i < nWifi; i ++){
        names[i] = WiFi.ssid(i);
    }
    return names;


}
