#include <WiFi.h>
#include <HTTPClient.h>

// =====================
// Wi-Fi Bilgileri
// =====================
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// =====================
// Flask Server Adresi
// =====================
const char* serverUrl = "http://YOUR_PC_IP:5000/panel";

// =====================
// ACS712 Pin
// =====================
#define ACS_PIN 34   // ACS712 OUT -> ESP32 IO34

// =====================
// ADC Ayarları
// =====================
const float ADC_REF = 3.3;
const float ADC_MAX = 4095.0;

// =====================
// ACS712 Ayarları
// =====================
// ACS712 modeline göre:
// 5A  model = 0.185 V/A
// 20A model = 0.100 V/A
// 30A model = 0.066 V/A
const float ACS_SENSITIVITY = 0.185;

// Son ölçümlere göre güncel sıfır akım referansı
// Gece / akım yokken ACS OUT yaklaşık 2.459 V göründü.
float ACS_ZERO_VOLTAGE = 2.459;

// Küçük gürültüleri sıfır kabul ediyoruz
const float CURRENT_NOISE_LIMIT = 0.04;

// =====================
// Ölçüm Değerleri
// =====================
int rawCurrentADC = 0;
float acsVoltage = 0.0;

// İşaretli akım: akım yönünü gösterir
float signedCurrent = 0.0;

// Pozitif akım: analiz için kolay değer
float current = 0.0;


// =====================
// Wi-Fi Bağlantısı
// =====================
void connectToWiFi() {
  Serial.print("Wi-Fi baglaniyor: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  int tryCount = 0;

  while (WiFi.status() != WL_CONNECTED && tryCount < 40) {
    delay(500);
    Serial.print(".");
    tryCount++;
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Wi-Fi baglandi.");
    Serial.print("PANEL ESP32 IP adresi: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Wi-Fi baglanamadi!");
  }
}


// =====================
// Ortalama ADC Okuma
// =====================
int readAverageRawADC(int pin, int sampleCount = 300) {
  long total = 0;

  for (int i = 0; i < sampleCount; i++) {
    total += analogRead(pin);
    delayMicroseconds(500);
  }

  return total / sampleCount;
}


// =====================
// RAW ADC -> Voltaj
// =====================
float rawToVoltage(int raw) {
  return (raw / ADC_MAX) * ADC_REF;
}


// =====================
// ACS712 Oku
// =====================
void readCurrentSensor() {
  rawCurrentADC = readAverageRawADC(ACS_PIN);

  acsVoltage = rawToVoltage(rawCurrentADC);

  // İşaretli akım hesabı
  signedCurrent = (acsVoltage - ACS_ZERO_VOLTAGE) / ACS_SENSITIVITY;

  // Gürültü aralığındaysa sıfır kabul et
  if (abs(signedCurrent) < CURRENT_NOISE_LIMIT) {
    signedCurrent = 0.0;
  }

  // Pozitif akım değeri
  current = abs(signedCurrent);
}


// =====================
// Veriyi Flask Server'a Gönder
// =====================
void sendJSONToServer() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String jsonData = "{";

    jsonData += "\"current_a\":";
    jsonData += String(current, 4);
    jsonData += ",";

    jsonData += "\"signed_current_a\":";
    jsonData += String(signedCurrent, 4);
    jsonData += ",";

    jsonData += "\"acs_voltage_v\":";
    jsonData += String(acsVoltage, 3);
    jsonData += ",";

    jsonData += "\"raw_current_adc\":";
    jsonData += String(rawCurrentADC);

    jsonData += "}";

    int httpResponseCode = http.POST(jsonData);

    Serial.print("ACS RAW: ");
    Serial.print(rawCurrentADC);

    Serial.print(" | ACS OUT: ");
    Serial.print(acsVoltage, 3);
    Serial.print(" V");

    Serial.print(" | Signed Akim: ");
    Serial.print(signedCurrent, 4);
    Serial.print(" A");

    Serial.print(" | Akim: ");
    Serial.print(current, 4);
    Serial.println(" A");

    Serial.print("HTTP Kod: ");
    Serial.println(httpResponseCode);

    Serial.print("Gonderilen JSON: ");
    Serial.println(jsonData);

    Serial.println("--------------------------------");

    http.end();
  } else {
    Serial.println("Wi-Fi bagli degil, veri gonderilemedi.");
  }
}


// =====================
// Setup
// =====================
void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println();
  Serial.println("PANEL ESP32 ACS712 kalibrasyonlu sistem baslatiliyor...");

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  connectToWiFi();

  Serial.print("Server URL: ");
  Serial.println(serverUrl);

  Serial.print("ACS ZERO VOLTAGE: ");
  Serial.println(ACS_ZERO_VOLTAGE, 3);

  Serial.print("CURRENT NOISE LIMIT: ");
  Serial.println(CURRENT_NOISE_LIMIT, 3);

  Serial.println("PANEL ESP32 hazir.");
}


// =====================
// Loop
// =====================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi koptu. Tekrar baglaniliyor...");
    connectToWiFi();
  }

  readCurrentSensor();
  sendJSONToServer();

  delay(2000);
}