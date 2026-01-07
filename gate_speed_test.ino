// SPEED TEST - Upload this to test if PWM works on your motor driver
#include <Arduino.h>

const int IN1 = 26;
const int IN2 = 27;
const int ENA = 25;

void setup() {
  Serial.begin(115200);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  
  ledcAttach(ENA, 1000, 12);
  
  Serial.println("\n=== MOTOR SPEED TEST ===");
  Serial.println("Testing if PWM speed control works...\n");
}

void loop() {
  // Test 1: FULL SPEED
  Serial.println("Test 1: FULL SPEED (4095/4095)");
  Serial.println("  → CLOCKWISE");
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  ledcWrite(ENA, 4095);
  delay(3000);
  
  ledcWrite(ENA, 0);
  delay(1000);
  
  Serial.println("  → COUNTER-CLOCKWISE");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  ledcWrite(ENA, 4095);
  delay(3000);
  
  // Stop
  ledcWrite(ENA, 0);
  delay(2000);
  
  // Test 2: HALF SPEED
  Serial.println("Test 2: HALF SPEED (2000/4095)");
  Serial.println("  → CLOCKWISE");
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  ledcWrite(ENA, 2000);
  delay(3000);
  
  ledcWrite(ENA, 0);
  delay(1000);
  
  Serial.println("  → COUNTER-CLOCKWISE");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  ledcWrite(ENA, 2000);
  delay(3000);
  
  // Stop
  ledcWrite(ENA, 0);
  delay(2000);
  
  // Test 3: LOW SPEED
  Serial.println("Test 3: LOW SPEED (800/4095)");
  Serial.println("  → CLOCKWISE");
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  ledcWrite(ENA, 800);
  delay(3000);
  
  ledcWrite(ENA, 0);
  delay(1000);
  
  Serial.println("  → COUNTER-CLOCKWISE");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  ledcWrite(ENA, 800);
  delay(3000);
  
  // Stop
  ledcWrite(ENA, 0);
  Serial.println("\nIf all 3 tests ran at SAME speed, your driver doesn't support PWM.");
  Serial.println("If speeds were DIFFERENT, PWM works! Check hardware knob.\n");
  delay(5000);
}
