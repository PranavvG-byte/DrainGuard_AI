// Pin Definitions
#define TRIG_PIN 5
#define ECHO_PIN 18
#define GAS_PIN 34   // MQ135 Analog Output

long duration;
float distance_cm;

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(GAS_PIN, INPUT);

  Serial.println("Smart Drainage Monitoring System Started...");
}

void loop() {

  // -------- Ultrasonic Sensor --------
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  duration = pulseIn(ECHO_PIN, HIGH);
  distance_cm = duration * 0.034 / 2;

  // -------- Gas Sensor --------
  int gasValue = analogRead(GAS_PIN);

  // -------- Simple Anomaly Logic --------
  String status = "NORMAL";

  if (distance_cm < 10) {
    status = "BLOCKAGE WARNING";
  }
  else if (distance_cm > 100) {
    status = "LEAKAGE DETECTED";
  }

  if (gasValue > 2500) {
    status = "GAS LEVEL HIGH";
  }

  // -------- Serial Output --------
  Serial.println("----------");
  Serial.print("Water Level (cm): ");
  Serial.println(distance_cm);

  Serial.print("Gas Level: ");
  Serial.println(gasValue);

  Serial.print("Status: ");
  Serial.println(status);

  delay(2000); // 2 seconds delay
}
