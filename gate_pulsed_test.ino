// PULSED SPEED TEST - Test ON/OFF pulsing for slow speed control
#include <Arduino.h>

const int IN1 = 26;
const int IN2 = 27;
const int ENA = 25;

void setup() {
  Serial.begin(115200);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENA, OUTPUT);
  
  Serial.println("\n=== PULSED SPEED TEST ===");
  Serial.println("Testing ON/OFF pulsing for slow speed control\n");
}

void loop() {
  Serial.println("\n=== GATE CYCLE TEST ===\n");
  
  // Step 1: CLOCKWISE - FULL SPEED (1.5 seconds)
  Serial.println("→ CLOCKWISE at FULL SPEED (1500ms)");
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(ENA, HIGH);
  delay(1500);
  stopMotor();
  
  // Step 2: Wait 3 seconds
  Serial.println("→ Waiting 3 seconds...");
  delay(3000);
  
  // Step 3: COUNTER-CLOCKWISE - PULSED SLOW (5 seconds)
  Serial.println("→ COUNTER-CLOCKWISE at PULSED SLOW SPEED (5000ms)");
  Serial.println("   Pulse: 100ms ON, 200ms OFF (33% duty)");
  pulsedRotate(LOW, HIGH, 5000, 100, 200);
  
  Serial.println("\n=== Cycle Complete ===");
  Serial.println("If CCW is too fast: Increase offTime (try 30, 40, 50)");
  Serial.println("If CCW is too slow: Increase onTime (try 50, 60, 70)");
  Serial.println("If jerky: Try smaller values (30ms ON, 15ms OFF)\n");
  delay(5000);
}

void pulsedRotate(int in1State, int in2State, int totalDurationMs, int onTime, int offTime) {
  digitalWrite(IN1, in1State);
  digitalWrite(IN2, in2State);
  
  unsigned long startTime = millis();
  while (millis() - startTime < totalDurationMs) {
    digitalWrite(ENA, HIGH);
    delay(onTime);
    digitalWrite(ENA, LOW);
    delay(offTime);
  }
  
  stopMotor();
}

void stopMotor() {
  digitalWrite(ENA, LOW);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}
