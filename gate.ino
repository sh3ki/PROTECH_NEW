#include <WiFi.h>
#include <HTTPClient.h>

// WiFi credentials
const char* ssid = "wifi";
const char* password = "123456789";

// Server URL
const char* serverUrl = "http://protech.it.com/api/gate/check-queue/";

// Motor control pins
const int IN1 = 26;   // Direction pin 1 (green wire)
const int IN2 = 27;   // Direction pin 2 (purple wire)
const int ENA = 25;   // PWM pin (brown wire)

// Ultrasonic sensor pins
const int TRIG_PIN = 5;   // Orange wire
const int ECHO_PIN = 18;  // Blue wire

// LED pins
const int GREEN_LED = 32;  // Green LED - Counter-clockwise rotation
const int RED_LED = 33;    // Red LED - Clockwise rotation / Idle

// PWM settings
const int pwmChannel = 0;
const int pwmFreq = 20000;       // 20 kHz
const int pwmResolution = 8;     // 0–255

// Distance threshold (in cm)
const int DISTANCE_THRESHOLD = 40;

// Queue checking interval (milliseconds)
unsigned long lastCheckTime = 0;
const unsigned long checkInterval = 1000;  // Check every 1 second

// Queue count
int queueCount = 0;

void setup() {
  Serial.begin(115200);
  
  // Motor pin setup
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  
  // Ultrasonic sensor pins
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  // LED pins
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);

  // Setup PWM
  ledcSetup(pwmChannel, pwmFreq, pwmResolution);
  ledcAttachPin(ENA, pwmChannel);
  
  // Initial state: Stop motor, RED LED on (idle)
  stopMotor();
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, HIGH);
  
  // Connect to WiFi
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
  }
}

void loop() {
  // Check if WiFi is connected
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Reconnecting...");
    WiFi.begin(ssid, password);
    delay(5000);
    return;
  }
  
  // Check queue at regular intervals
  unsigned long currentTime = millis();
  if (currentTime - lastCheckTime >= checkInterval) {
    lastCheckTime = currentTime;
    checkGateQueue();
  }
  
  // If there's a queue, process it
  if (queueCount > 0) {
    performGateCycle();
    queueCount--;  // Decrement queue after completing a cycle
  } else {
    // Idle state: RED LED on, motor stopped
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(RED_LED, HIGH);
  }
}

void checkGateQueue() {
  HTTPClient http;
  
  Serial.println("Checking gate queue...");
  
  http.begin(serverUrl);
  http.setTimeout(5000);  // 5 second timeout
  
  int httpCode = http.GET();
  
  if (httpCode > 0) {
    if (httpCode == HTTP_CODE_OK) {
      String payload = http.getString();
      Serial.println("Server response: " + payload);
      
      // Parse JSON to get cycles count
      int cyclesIndex = payload.indexOf("\"cycles\":");
      if (cyclesIndex != -1) {
        int numberStart = cyclesIndex + 9;  // Skip "cycles":
        int numberEnd = payload.indexOf(",", numberStart);
        if (numberEnd == -1) {
          numberEnd = payload.indexOf("}", numberStart);
        }
        
        String cyclesStr = payload.substring(numberStart, numberEnd);
        cyclesStr.trim();
        int cycles = cyclesStr.toInt();
        
        Serial.print("New cycles from server: ");
        Serial.println(cycles);
        
        // Add to queue
        if (cycles > 0) {
          queueCount += cycles;
          Serial.print("Total queue count: ");
          Serial.println(queueCount);
        }
      }
    } else {
      Serial.print("HTTP error code: ");
      Serial.println(httpCode);
    }
  } else {
    Serial.print("Connection failed: ");
    Serial.println(http.errorToString(httpCode));
  }
  
  http.end();
}

void performGateCycle() {
  Serial.println("\n=== Starting Gate Cycle ===");
  Serial.print("Remaining in queue: ");
  Serial.println(queueCount);
  
  // Step 1: Rotate COUNTER-CLOCKWISE for 3 seconds
  Serial.println("→ Rotating COUNTER-CLOCKWISE (3 seconds)");
  digitalWrite(GREEN_LED, HIGH);  // Green LED ON
  digitalWrite(RED_LED, LOW);     // Red LED OFF
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  ledcWrite(pwmChannel, 255);     // Maximum speed
  delay(3000);
  
  // Step 2: Stop and wait for ultrasonic sensor
  Serial.println("→ Stopping - Waiting for person to pass...");
  stopMotor();
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  
  waitForPersonToPass();
  
  // Step 3: Rotate CLOCKWISE
  // If there's more in queue: 1 second, else 3 seconds
  int clockwiseTime = (queueCount > 1) ? 1000 : 3000;
  
  Serial.print("→ Rotating CLOCKWISE (");
  Serial.print(clockwiseTime / 1000);
  Serial.println(" seconds)");
  
  digitalWrite(GREEN_LED, LOW);   // Green LED OFF
  digitalWrite(RED_LED, HIGH);    // Red LED ON
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  ledcWrite(pwmChannel, 255);     // Maximum speed
  delay(clockwiseTime);
  
  // Step 4: If there's more in queue, go back 2 seconds counter-clockwise
  if (queueCount > 1) {
    Serial.println("→ Queue exists - Rotating COUNTER-CLOCKWISE (2 seconds)");
    digitalWrite(GREEN_LED, HIGH);  // Green LED ON
    digitalWrite(RED_LED, LOW);     // Red LED OFF
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    ledcWrite(pwmChannel, 255);
    delay(2000);
  }
  
  // Stop motor
  stopMotor();
  Serial.println("=== Gate Cycle Complete ===\n");
}

void waitForPersonToPass() {
  Serial.println("Waiting for sensor detection...");
  
  bool personDetected = false;
  unsigned long waitStart = millis();
  const unsigned long maxWaitTime = 30000;  // 30 seconds timeout
  
  // Wait until ultrasonic sensor detects someone (distance < 40cm)
  while (!personDetected && (millis() - waitStart < maxWaitTime)) {
    float distance = getDistance();
    
    if (distance > 0 && distance < DISTANCE_THRESHOLD) {
      personDetected = true;
      Serial.print("Person detected! Distance: ");
      Serial.print(distance);
      Serial.println(" cm");
    }
    
    delay(100);  // Check every 100ms
  }
  
  if (!personDetected) {
    Serial.println("Timeout - No person detected, continuing...");
    return;
  }
  
  // Wait for person to pass (distance > 40cm again)
  Serial.println("Waiting for person to pass...");
  delay(500);  // Small delay to ensure person is in detection zone
  
  bool personPassed = false;
  waitStart = millis();
  
  while (!personPassed && (millis() - waitStart < maxWaitTime)) {
    float distance = getDistance();
    
    if (distance >= DISTANCE_THRESHOLD || distance == 0) {
      personPassed = true;
      Serial.println("Person has passed!");
    }
    
    delay(100);
  }
  
  if (!personPassed) {
    Serial.println("Timeout - Assuming person passed, continuing...");
  }
  
  delay(500);  // Small delay before continuing
}

float getDistance() {
  // Clear the trigger pin
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  
  // Send 10 microsecond pulse
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Read the echo pin
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms timeout
  
  // Calculate distance in cm
  if (duration == 0) {
    return 0;  // No echo received
  }
  
  float distance = duration * 0.034 / 2;  // Speed of sound = 340 m/s
  
  return distance;
}

void stopMotor() {
  ledcWrite(pwmChannel, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}
