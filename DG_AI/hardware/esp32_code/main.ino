// ============================================================
//  DrainGuard AI - ESP32 Smart Drainage Monitor (Firmware v2.0)
// ============================================================
//  Improvements over v1.0:
//  - JSON serial output for robust parsing
//  - Median filter (5 samples) for ultrasonic sensor
//  - Exponential moving average for gas sensor
//  - Hardware watchdog timer
//  - Configurable read interval
//  - WiFi-ready structure (commented out for USB prototype)
// ============================================================

#include <esp_task_wdt.h>

// ─── Pin Configuration ──────────────────────────────────────
#define TRIG_PIN       5
#define ECHO_PIN       18
#define GAS_PIN        34    // MQ135 Analog Output (ADC1)

// ─── Configuration ─────────────────────────────────────────
#define SERIAL_BAUD    115200
#define READ_INTERVAL  2000  // ms between readings
#define MEDIAN_SAMPLES 5     // Number of ultrasonic samples for median
#define EMA_ALPHA      0.2f  // Exponential moving average weight for gas
#define WDT_TIMEOUT    8     // Watchdog timeout in seconds

// ─── State Variables ────────────────────────────────────────
float gasEMA = 0.0;
bool firstReading = true;
unsigned long readingCount = 0;
unsigned long bootTime = 0;

// ─── Ultrasonic: Take N readings, return median ─────────────
float readUltrasonicMedian(int samples) {
  float readings[MEDIAN_SAMPLES];  // Fixed-size array avoids non-standard VLA
  
  for (int i = 0; i < samples; i++) {
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    
    long duration = pulseIn(ECHO_PIN, HIGH, 30000); // 30ms timeout
    
    if (duration == 0) {
      readings[i] = -1.0; // Invalid reading
    } else {
      readings[i] = duration * 0.034 / 2.0;
    }
    delay(30); // Gap between pings
  }
  
  // Sort for median (simple insertion sort for small N)
  for (int i = 1; i < samples; i++) {
    float key = readings[i];
    int j = i - 1;
    while (j >= 0 && readings[j] > key) {
      readings[j + 1] = readings[j];
      j--;
    }
    readings[j + 1] = key;
  }
  
  // Remove invalid readings (-1) and return median of valid ones
  int validStart = 0;
  while (validStart < samples && readings[validStart] < 0) validStart++;
  
  int validCount = samples - validStart;
  if (validCount == 0) return -1.0; // All invalid
  
  return readings[validStart + validCount / 2];
}

// ─── Gas Sensor: Exponential Moving Average ─────────────────
float readGasEMA() {
  int rawGas = analogRead(GAS_PIN);
  
  if (firstReading) {
    gasEMA = (float)rawGas;
    firstReading = false;
  } else {
    gasEMA = EMA_ALPHA * (float)rawGas + (1.0 - EMA_ALPHA) * gasEMA;
  }
  
  return gasEMA;
}

// ─── Setup ──────────────────────────────────────────────────
void setup() {
  Serial.begin(SERIAL_BAUD);
  
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(GAS_PIN, INPUT);
  
  // Initialize hardware watchdog
  esp_task_wdt_init(WDT_TIMEOUT, true);
  esp_task_wdt_add(NULL);
  
  bootTime = millis();
  
  // Boot message (JSON)
  Serial.println("{\"event\":\"boot\",\"firmware\":\"DrainGuard_v2.0\",\"interval_ms\":" + String(READ_INTERVAL) + "}");
  
  delay(1000); // Sensor stabilization
}

// ─── Main Loop ──────────────────────────────────────────────
void loop() {
  // Feed watchdog
  esp_task_wdt_reset();
  
  // Read sensors
  float waterLevel = readUltrasonicMedian(MEDIAN_SAMPLES);
  float gasLevel = readGasEMA();
  
  readingCount++;
  unsigned long uptimeSeconds = (millis() - bootTime) / 1000;
  
  // Build JSON output
  // Format: {"water_level":XX.XX,"gas_level":XXXX,"reading":N,"uptime":N}
  String json = "{";
  json += "\"water_level\":" + String(waterLevel, 2) + ",";
  json += "\"gas_level\":" + String((int)gasLevel) + ",";
  json += "\"reading\":" + String(readingCount) + ",";
  json += "\"uptime\":" + String(uptimeSeconds);
  json += "}";
  
  Serial.println(json);
  
  delay(READ_INTERVAL);
}

// ============================================================
//  WiFi Extension (uncomment for WiFi mode in future):
// ============================================================
// #include <WiFi.h>
// #include <HTTPClient.h>
//
// const char* ssid = "YOUR_SSID";
// const char* password = "YOUR_PASSWORD";
// const char* serverUrl = "http://YOUR_SERVER:5000/api/data";
//
// void setupWiFi() {
//   WiFi.begin(ssid, password);
//   while (WiFi.status() != WL_CONNECTED) {
//     delay(500);
//     Serial.print(".");
//   }
//   Serial.println("\nWiFi Connected: " + WiFi.localIP().toString());
// }
//
// void sendDataHTTP(String json) {
//   if (WiFi.status() == WL_CONNECTED) {
//     HTTPClient http;
//     http.begin(serverUrl);
//     http.addHeader("Content-Type", "application/json");
//     int code = http.POST(json);
//     http.end();
//   }
// }
// ============================================================
