// Arduino code for Smart Urban Drainage Monitoring System using ESP32

#include <WiFi.h>
#include <ArduinoJson.h>
#include <NewPing.h>

// Define your WiFi credentials
const char* ssid = "your_ssid";
const char* password = "your_password";

// Ultrasonic sensor pins
const int trigPin = 23;  
const int echoPin = 22;  
NewPing sonar(trigPin, echoPin);

// Gas sensor pin
const int gasSensorPin = 34; // Example pin

// Thresholds
const int distanceThreshold = 30; // in cm
const int gasThreshold = 400; // change as per gas sensor specs

void setup() {
    Serial.begin(115200);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("Connected to WiFi");
}

void loop() {
    delay(1000); // Delay between each reading
    checkSensors();
}

void checkSensors() {
    float distance = sonar.ping_cm();
    int gasValue = analogRead(gasSensorPin);
    bool anomalyDetected = false;

    // Anomaly detection logic
    if (distance < distanceThreshold) {
        anomalyDetected = true;
        Serial.println("Anomaly Detected: Flood risk");
    }
    if (gasValue > gasThreshold) {
        anomalyDetected = true;
        Serial.println("Anomaly Detected: Gas leakage");
    }

    // Outputting data as JSON
    DynamicJsonDocument doc(1024);
    doc["distance"] = distance;
    doc["gasValue"] = gasValue;
    doc["anomalyDetected"] = anomalyDetected;

    String jsonOutput;
    serializeJson(doc, jsonOutput);
    Serial.println(jsonOutput);

    // Add your code to send this JSON output to a server or cloud
}