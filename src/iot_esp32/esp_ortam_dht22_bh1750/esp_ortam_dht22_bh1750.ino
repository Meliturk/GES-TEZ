#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <BH1750.h>
#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT22

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

const char* serverUrl = "http://YOUR_PC_IP:5000/env";

BH1750 lightMeter;
DHT dht(DHTPIN, DHTTYPE);

void connectToWiFi() {
  Serial.print("Wi-Fi baglaniyor: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  int tryCount = 0;

  while (WiFi.status() != WL_CONNECTED && tryCount < 30) {
    delay(500);
    Serial.print(".");
    tryCount++;
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Wi-Fi baglandi.");
    Serial.print("ESP32 IP adresi: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Wi-Fi baglanamadi!");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(21, 22);

  dht.begin();

  if (!lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("BH1750 bulunamadi!");
  } else {
    Serial.println("BH1750 baslatildi.");
  }

  connectToWiFi();

  Serial.println("ESP32-1 Wi-Fi ortam veri gonderimi basladi.");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi koptu. Tekrar baglaniliyor...");
    connectToWiFi();
  }

  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  float lux = lightMeter.readLightLevel();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("DHT22 okuma hatasi!");
    delay(5000);
    return;
  }

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String jsonData = "{";
    jsonData += "\"temperature_c\":";
    jsonData += String(temperature, 2);
    jsonData += ",";
    jsonData += "\"humidity_percent\":";
    jsonData += String(humidity, 2);
    jsonData += ",";
    jsonData += "\"lux\":";
    jsonData += String(lux, 2);
    jsonData += "}";

    int httpResponseCode = http.POST(jsonData);

    Serial.print("Gonderilen veri: ");
    Serial.println(jsonData);

    Serial.print("HTTP cevap kodu: ");
    Serial.println(httpResponseCode);

    http.end();
  } else {
    Serial.println("Wi-Fi bagli degil, veri gonderilemedi.");
  }

  delay(5000);
}