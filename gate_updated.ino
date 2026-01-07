#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>

// WiFi credentials
const char* ssid = "wifi";
const char* password = "123456789";

// Server URL
const char* serverUrl = "https://protech.it.com/api/gate/check-queue/";

// Motor control pins
const int IN1 = 26;
const int IN2 = 27;
const int ENA = 25;

// Ultrasonic sensor pins
const int TRIG_PIN = 5;
const int ECHO_PIN = 18;

// LED pins
const int GREEN_LED = 32;
const int RED_LED = 33;

// PWM settings - SPEED CONTROL
const int pwmFreq = 1000;           // Higher frequency for smoother control
const int pwmResolution = 12;       // 0-4095 range

// Speed and timing for EQUAL ROTATIONS
const int cwSpeed = 2500;           // Clockwise: HIGH SPEED (duty cycle)
const int ccwSpeed = 1500;          // Counter-clockwise: LOW SPEED (ratio 1.67:1)
const int cwDurationMs = 1500;      // CW duration: 1.5 seconds
const int ccwDurationMs = 2500;     // CCW duration: 2.5 seconds

// Queue checking
unsigned long lastCheckTime = 0;
const unsigned long checkInterval = 200;
int queueCount = 0;
bool isProcessing = false;

void setup() {
  Serial.begin(115200);
  
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);

  ledcAttach(ENA, pwmFreq, pwmResolution);
  
  stopMotor();
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, HIGH);
  
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
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi connection failed!");
  }
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Reconnecting...");
    WiFi.begin(ssid, password);
    delay(5000);
    return;
  }
  
  unsigned long currentTime = millis();
  if (currentTime - lastCheckTime >= checkInterval) {
    lastCheckTime = currentTime;
    checkGateQueue();
  }
  
  if (!isProcessing && queueCount > 0) {
    isProcessing = true;
    performGateCycle();
    isProcessing = false;
  } else {
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(RED_LED, HIGH);
  }
}

void checkGateQueue() {
  WiFiClientSecure client;
  client.setInsecure();
  HTTPClient http;
  
  Serial.println("Checking gate queue...");
  
  http.begin(client, serverUrl);
  http.setTimeout(5000);
  http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
  
  int httpCode = http.GET();
  
  if (httpCode > 0) {
    if (httpCode == HTTP_CODE_OK) {
      String payload = http.getString();
      Serial.println("Server response: " + payload);
      
      int cyclesIndex = payload.indexOf("\"cycles\":");
      if (cyclesIndex != -1) {
        int numberStart = cyclesIndex + 9;
        int numberEnd = payload.indexOf(",", numberStart);
        if (numberEnd == -1) {
          numberEnd = payload.indexOf("}", numberStart);
        }
        
        String cyclesStr = payload.substring(numberStart, numberEnd);
        cyclesStr.trim();
        int cycles = cyclesStr.toInt();
        
        Serial.print("New cycles from server: ");
        Serial.println(cycles);
        
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
  
  // CLOCKWISE - HIGH SPEED (1.5 seconds)
  Serial.println("→ Rotating CLOCKWISE at HIGH SPEED");
  Serial.print("   Speed: "); Serial.print(cwSpeed); 
  Serial.print(" | Duration: "); Serial.print(cwDurationMs); Serial.println(" ms");
  
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, HIGH);
  stopMotor();
  delay(100);
  
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  ledcWrite(ENA, cwSpeed);
  delay(cwDurationMs);
  stopMotor();
  
  // WAIT 3 SECONDS
  Serial.println("→ Waiting 3 seconds...");
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  delay(3000);
  
  // COUNTER-CLOCKWISE - LOW SPEED (2.5 seconds)
  Serial.println("→ Rotating COUNTER-CLOCKWISE at LOW SPEED");
  Serial.print("   Speed: "); Serial.print(ccwSpeed); 
  Serial.print(" | Duration: "); Serial.print(ccwDurationMs); Serial.println(" ms");
  
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(RED_LED, LOW);
  stopMotor();
  delay(100);
  
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  ledcWrite(ENA, ccwSpeed);
  delay(ccwDurationMs);
  stopMotor();
  
  Serial.println("=== Gate Cycle Complete ===\n");

  if (queueCount > 0) {
    queueCount--;
  }
}

float getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return 0;
  
  return duration * 0.034 / 2;
}

void stopMotor() {
  ledcWrite(ENA, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}
