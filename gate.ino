#include <WiFi.h>
#include <HTTPClient.h>

// WiFi credentials
const char* ssid = "wifi";
const char* password = "123456789";

// Server URL - Using your domain
const char* serverUrl = "http://protech.it.com/api/gate/check-queue/";

// Motor control pins
int IN1 = 26;   // Direction pin 1
int IN2 = 27;   // Direction pin 2
int ENA = 25;   // PWM pin (ENA)

// PWM settings
int pwmChannel = 0;
int pwmFreq = 20000;       // 20 kHz (silent for motors)
int pwmResolution = 8;     // 0–255

// Queue checking interval (milliseconds)
unsigned long lastCheckTime = 0;
const unsigned long checkInterval = 2000;  // Check every 2 seconds

void setup() {
  Serial.begin(115200);
  
  // Motor pin setup
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  // Setup PWM
  ledcSetup(pwmChannel, pwmFreq, pwmResolution);
  ledcAttachPin(ENA, pwmChannel);
  
  // Stop motor initially
  stopMotor();
  
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
      // Looking for "cycles": number in the response
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
        
        Serial.print("Cycles to perform: ");
        Serial.println(cycles);
        
        // Perform gate cycles
        if (cycles > 0) {
          for (int i = 0; i < cycles; i++) {
            Serial.print("Performing cycle ");
            Serial.print(i + 1);
            Serial.print(" of ");
            Serial.println(cycles);
            performGateCycle();
          }
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
  Serial.println("Starting gate cycle...");
  
  // CLOCKWISE – MAX SPEED for 3 seconds
  Serial.println("Rotating clockwise (3s)");
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  ledcWrite(pwmChannel, 255);   // MAX SPEED
  delay(3000);

  // STOP for 5 seconds
  Serial.println("Stopping (5s)");
  stopMotor();
  delay(5000);

  // COUNTER-CLOCKWISE – MAX SPEED for 3 seconds
  Serial.println("Rotating counter-clockwise (3s)");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  ledcWrite(pwmChannel, 255);   // MAX SPEED
  delay(3000);

  // STOP
  Serial.println("Cycle complete");
  stopMotor();
}

void stopMotor() {
  ledcWrite(pwmChannel, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}
