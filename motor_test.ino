    // Simple Motor Direction Test (no relays)
    // Tests if motor can reverse directions using L298N only

    // Motor control pins
    const int IN1 = 26;   // Direction pin 1 (green wire)
    const int IN2 = 27;   // Direction pin 2 (purple wire)
    const int ENA = 25;   // PWM pin (brown wire)

    // LED pins
    const int GREEN_LED = 32;  // Green LED - Counter-clockwise
    const int RED_LED = 33;    // Red LED - Clockwise

    // PWM settings
    const int pwmFreq = 200;       // very low freq for more torque per duty at crawl speeds
    const int pwmResolution = 12;  // 12-bit resolution (0..4095) for very fine control
    const int pwmLow = 3;          // low steady duty for CW
    const int pwmLowCCW = 0;       // near-zero steady duty for CCW to slow it way down
    const int pwmKick = 96;        // stronger boost to break static friction
    const int kickMsCW = 80;       // CW kick duration (ms)
    const int kickMsCCW = 20;      // much shorter CCW kick to reduce motion

    void setup() {
    Serial.begin(115200);
    
    // Motor pin setup
    pinMode(IN1, OUTPUT);
    pinMode(IN2, OUTPUT);
    
    // LED pins
    pinMode(GREEN_LED, OUTPUT);
    pinMode(RED_LED, OUTPUT);

    // Setup PWM
    ledcAttach(ENA, pwmFreq, pwmResolution);
    
    Serial.println("\n\n=================================");
    Serial.println("MOTOR DIRECTION TEST (NO RELAYS)");
    Serial.println("=================================");
    Serial.println("Testing CW then CCW using IN1/IN2");
    Serial.println("=================================\n");
    
    delay(2000);
    }

    void loop() {
    // Test 1: Rotate CLOCKWISE - Normal polarity
    Serial.println("\n>>> TEST: Rotating CLOCKWISE for 0.3 seconds");
    Serial.println("    RED LED ON (normal polarity)");
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(RED_LED, HIGH);
    stopMotor();
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    delay(200);
    softStart(300, pwmLow, pwmKick, kickMsCW);  // exact 0.3s total
    stopMotor();                 // hard stop
    
    // Full stop before reversing
    Serial.println("\n>>> STOP for 1.5 seconds (allow controller to reset)");
    stopMotor();
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(RED_LED, LOW);
    delay(1500);
    
    // Test 2: Rotate COUNTER-CLOCKWISE - Reversed polarity
    Serial.println("\n>>> TEST: Rotating COUNTER-CLOCKWISE for 0.1 seconds");
    Serial.println("    GREEN LED ON (reverse polarity)");
    digitalWrite(GREEN_LED, HIGH);
    digitalWrite(RED_LED, LOW);
    stopMotor();
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    delay(300);                     // extra settle
    softStart(100, pwmLowCCW, pwmKick, kickMsCCW); // CCW: tiny kick then near-zero hold
    stopMotor();                    // hard stop
    
    // Stop
    Serial.println("\n>>> STOP for 2 seconds");
    stopMotor();
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(RED_LED, LOW);
    delay(2000);
    
    Serial.println("\n=================================");
    Serial.println("Test cycle complete. Repeating...");
    Serial.println("=================================");
    delay(1000);
    }

    void stopMotor() {
    ledcWrite(ENA, 0);
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    }

    // Small kick helps very low duty overcome static friction, then drop to hold value
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
