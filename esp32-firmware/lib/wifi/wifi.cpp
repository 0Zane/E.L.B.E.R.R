#include <wifi.h>
#include "wififeatures.h"
#include <array>

using namespace std;

int nScannedWifi(){
    return WiFi.scanNetworks();
}

array<String,10> wifinames(){
    std::array<String, 10> names;
    for (int i = 0; i < 10; i ++){
        names[i] = WiFi.SSID(i);
    }
    return names;


}

void beacon_spam(int nwifi){
    //initialize a const char* const ssids[] containing elberr related SSIDs
    //Create the AP on different channels

}