#include <Arduino.h>
#include <ESP32WiFi.h>
#include <ArduinoJson.h>

#define TRIG_PIN 5
#define ECHO_PIN 18
#define GAS_SENSOR_PIN 34

const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

WiFiServer server(80);

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(GAS_SENSOR_PIN, INPUT);
  
  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  server.begin();
  Serial.println("Connected to WiFi");
}

void loop() {
  // Measure distance
  long duration, distance;
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  duration = pulseIn(ECHO_PIN, HIGH);
  distance = (duration * 0.034) / 2;

  // Read gas concentration
  int gasValue = analogRead(GAS_SENSOR_PIN);

  // Simple anomaly detection logic
  bool anomalyDetected = (gasValue > 400); // threshold; modify as necessary

  // Create JSON output
  StaticJsonDocument<200> doc;
  doc["distance"] = distance;
  doc["gasValue"] = gasValue;
  doc["anomalyDetected"] = anomalyDetected;
  
  // Serialize JSON to string
  String output;
  serializeJson(doc, output);

  // Send data to serial
  Serial.println(output);
  delay(2000); // Delay between iterations
}