#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>

// WiFi credentials
const char* ssid = "wifi";
const char* password = "123456789";

// Server URL (use HTTPS; server redirects HTTP to HTTPS)
const char* serverUrl = "https://protech.it.com/api/gate/check-queue/";

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

// PWM settings (match motor_test.ino behavior)
const int pwmFreq = 200;          // very low freq for more torque at crawl speeds
const int pwmResolution = 12;     // 0–4095
const int pwmLowCW = 3;           // low steady duty for CW
const int pwmLowCCW = 0;          // near-zero steady duty for CCW to slow it way down
const int pwmKick = 96;           // strong kick to break static friction
const int kickMsCW = 80;          // CW kick duration (ms)
const int kickMsCCW = 20;         // shorter CCW kick to reduce motion
const int cwDurationMs = 1000;    // CW runtime (ms) per cycle
const int ccwDurationMs = 500;    // CCW runtime (ms) per cycle

// Queue checking interval (milliseconds)
unsigned long lastCheckTime = 0;
const unsigned long checkInterval = 1000;  // Check every 1 second

// Queue count
int queueCount = 0;
bool isProcessing = false;

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

  // Setup PWM (New ESP32 Arduino Core 3.x API)
  ledcAttach(ENA, pwmFreq, pwmResolution);
  
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
  if (!isProcessing && queueCount > 0) {
    isProcessing = true;
    performGateCycle();
    isProcessing = false;
  } else {
    // Idle state: RED LED on, motor stopped
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(RED_LED, HIGH);
  }
}

void checkGateQueue() {
  WiFiClientSecure client;
  client.setInsecure();  // Allow self-signed/any cert
  HTTPClient http;
  
  Serial.println("Checking gate queue...");
  
  http.begin(client, serverUrl);
  http.setTimeout(5000);  // 5 second timeout
  http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);  // Follow 301/302 redirects
  
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
  
  // Step 1: Rotate CLOCKWISE for configured duration
  Serial.print("→ Rotating CLOCKWISE (ms): ");
  Serial.println(cwDurationMs);
  digitalWrite(GREEN_LED, LOW);   // Green LED OFF
  digitalWrite(RED_LED, HIGH);    // Red LED ON
  stopMotor();
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  delay(150);                     // Allow direction to latch
  softStart(cwDurationMs, pwmLowCW, pwmKick, kickMsCW);
  stopMotor();
  
  // Step 2: Fixed wait before reversing (no sensor)
  Serial.println("→ Stopping - Fixed delay before reverse (6000 ms)");
  stopMotor();
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  delay(6000);
  // Brief settle before reversing direction
  stopMotor();
  delay(150);
  
  // Step 3: Rotate COUNTER-CLOCKWISE for configured duration
  Serial.print("→ Rotating COUNTER-CLOCKWISE (ms): ");
  Serial.println(ccwDurationMs);
  digitalWrite(GREEN_LED, HIGH);  // Green LED ON
  digitalWrite(RED_LED, LOW);     // Red LED OFF
  stopMotor();
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  delay(200);                     // Allow direction to latch
  softStart(ccwDurationMs, pwmLowCCW, pwmKick, kickMsCCW);
  stopMotor();
  
  // Stop motor
  stopMotor();
  Serial.println("=== Gate Cycle Complete ===\n");

  // Decrement queue after full cycle completes
  if (queueCount > 0) {
    queueCount--;
  }
}

void waitForPersonToPass() {
  // Sensor disabled per latest requirements
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
  ledcWrite(ENA, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}

// Kick then hold at low duty for a precise total duration
void softStart(int totalMs, int holdDuty, int kickDuty, int kickMs) {
  int kick = (totalMs < kickMs) ? totalMs : kickMs;
  int hold = totalMs - kick;
  if (kick > 0) {
    ledcWrite(ENA, kickDuty);
    delay(kick);
  }
  if (hold > 0) {
    ledcWrite(ENA, holdDuty);
    delay(hold);
  }
}
