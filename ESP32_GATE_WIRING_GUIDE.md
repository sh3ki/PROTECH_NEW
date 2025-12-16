# ESP32 Gate Control - Complete Wiring Guide

## ✅ Hardware Components
- ESP32 Development Board
- HC-SR04 Ultrasonic Sensor
- L298N Motor Driver
- DC Motor with PWM Speed Controller
- 2x LEDs (1 Green, 1 Red)
- 2x 220Ω Resistors (for LEDs)
- Jumper wires
- Power supply (for motor driver)

---

## 📋 Complete Wiring Connections

### **Ultrasonic Sensor (HC-SR04) → ESP32**
| HC-SR04 Pin | Wire Color | ESP32 Pin | Description |
|-------------|------------|-----------|-------------|
| GND         | White      | GND       | Ground      |
| ECHO        | Blue       | GPIO 18   | Echo signal |
| TRIG        | Orange     | GPIO 5    | Trigger signal |
| VCC         | Blue       | 5V        | Power (5V)  |

### **Motor Driver (L298N) → ESP32**
| L298N Pin   | Wire Color | ESP32 Pin | Description |
|-------------|------------|-----------|-------------|
| GND         | Gray       | GND       | Ground      |
| IN1         | Green      | GPIO 26   | Direction control 1 |
| IN2         | Purple     | GPIO 27   | Direction control 2 |
| ENA         | Brown      | GPIO 25   | PWM Speed control |

### **Motor Driver → PWM Speed Controller**
| L298N Pin   | Wire Color | Speed Controller | Description |
|-------------|------------|------------------|-------------|
| OUT1        | Orange     | V+               | Motor output positive |
| OUT2        | Black      | V-               | Motor output negative |

### **PWM Speed Controller → DC Motor**
| Speed Controller | Wire Color | Motor Pin | Description |
|------------------|------------|-----------|-------------|
| M+               | Blue       | Motor +   | Motor positive |
| M-               | Red        | Motor -   | Motor negative |

### **LED Indicators → ESP32**

#### **Green LED (Counter-Clockwise Rotation)**
```
ESP32 GPIO 32 → 220Ω Resistor → Green LED Anode (+)
Green LED Cathode (-) → ESP32 GND
```

| Component       | Connection    |
|-----------------|---------------|
| ESP32 GPIO 32   | → 220Ω Resistor |
| 220Ω Resistor   | → LED Anode (+) (longer leg) |
| LED Cathode (-) | → ESP32 GND (shorter leg) |

#### **Red LED (Clockwise Rotation / Idle)**
```
ESP32 GPIO 33 → 220Ω Resistor → Red LED Anode (+)
Red LED Cathode (-) → ESP32 GND
```

| Component       | Connection    |
|-----------------|---------------|
| ESP32 GPIO 33   | → 220Ω Resistor |
| 220Ω Resistor   | → LED Anode (+) (longer leg) |
| LED Cathode (-) | → ESP32 GND (shorter leg) |

---

## 🔌 Power Connections

### ESP32 Power
- Connect ESP32 to USB or 5V power supply via VIN and GND

### Motor Driver Power
- **+12V**: Connect to external power supply (depends on your motor voltage)
- **GND**: Connect to power supply ground AND ESP32 GND (common ground)
- **+5V**: Can power ESP32 if needed (L298N has 5V regulator)

⚠️ **IMPORTANT**: Make sure ESP32 GND and Motor Driver GND share a common ground!

---

## 📊 Pin Summary Table

| ESP32 GPIO | Connected To              | Purpose                    |
|------------|---------------------------|----------------------------|
| GPIO 5     | Ultrasonic TRIG (Orange)  | Trigger ultrasonic sensor  |
| GPIO 18    | Ultrasonic ECHO (Blue)    | Receive ultrasonic echo    |
| GPIO 25    | Motor Driver ENA (Brown)  | PWM speed control          |
| GPIO 26    | Motor Driver IN1 (Green)  | Direction control 1        |
| GPIO 27    | Motor Driver IN2 (Purple) | Direction control 2        |
| GPIO 32    | Green LED (via resistor)  | Counter-clockwise indicator|
| GPIO 33    | Red LED (via resistor)    | Clockwise/idle indicator   |
| 5V         | Ultrasonic VCC            | Power ultrasonic sensor    |
| GND        | All component grounds     | Common ground              |

---

## 🎨 LED Behavior Guide

| LED State       | Meaning                                    |
|-----------------|------------------------------------------- |
| 🟢 Green ON     | Motor rotating COUNTER-CLOCKWISE (opening) |
| 🔴 Red ON       | Motor rotating CLOCKWISE (closing)         |
| 🔴 Red ON       | Idle state (no queue, motor stopped)       |
| Both OFF        | Waiting for ultrasonic sensor detection    |

---

## ⚙️ System Operation Flow

1. **Fetch Queue** (Every 1 second)
   - ESP32 checks server for new gate cycles
   - Adds to internal queue count

2. **Process Queue** (When count > 0)
   
   **Step 1**: Rotate COUNTER-CLOCKWISE for 3 seconds
   - 🟢 Green LED ON
   - Gate opens
   
   **Step 2**: Wait for person detection
   - Both LEDs OFF
   - Ultrasonic sensor waits for distance < 40cm
   - Then waits for person to pass (distance > 40cm)
   
   **Step 3**: Rotate CLOCKWISE
   - 🔴 Red LED ON
   - If queue > 1: Rotate 1 second
   - If queue = 1: Rotate 3 seconds (full close)
   
   **Step 4**: Prepare for next cycle (if queue exists)
   - 🟢 Green LED ON
   - Rotate COUNTER-CLOCKWISE for 2 seconds
   - Ready for next person

3. **Idle State** (Queue = 0)
   - 🔴 Red LED ON
   - Motor stopped
   - Waiting for new queue items

---

## 🔧 Testing Checklist

- [ ] WiFi connection established
- [ ] Server communication working (check Serial Monitor)
- [ ] Motor rotates counter-clockwise (Green LED ON)
- [ ] Motor rotates clockwise (Red LED ON)
- [ ] Ultrasonic sensor detects objects < 40cm
- [ ] Gate cycle completes properly
- [ ] Queue management working
- [ ] LEDs indicate correct states

---

## 📱 WiFi Configuration

```cpp
SSID: "wifi"
Password: "123456789"
Server: "http://protech.it.com/api/gate/check-queue/"
```

---

## 🐛 Troubleshooting

### Motor not rotating
- Check ENA connection (GPIO 25)
- Check IN1/IN2 connections (GPIO 26/27)
- Verify motor driver power supply
- Check common ground connection

### Ultrasonic not working
- Verify TRIG (GPIO 5) and ECHO (GPIO 18) connections
- Check 5V power to sensor
- Test with Serial Monitor distance readings

### LEDs not lighting
- Check resistor connections (220Ω)
- Verify LED polarity (longer leg = anode/+)
- Check GPIO 32 (Green) and GPIO 33 (Red) connections

### WiFi not connecting
- Verify SSID and password in code
- Check router settings
- Monitor Serial output for connection status

---

## 📝 Notes

- The PWM speed controller allows manual speed adjustment - no need to modify code
- Motor speed is set to maximum (255) in code - adjust using hardware controller
- Ultrasonic sensor timeout is 30 seconds
- Gate cycle timeout prevents infinite waiting
- Server is checked every 1 second for new queue items
- Queue accumulates - multiple people can queue up

---

## 🚀 Upload Instructions

1. Open [gate.ino](gate.ino) in Arduino IDE
2. Select board: **ESP32 Dev Module**
3. Select correct COM port
4. Click Upload
5. Open Serial Monitor (115200 baud) to view logs

---

*Last Updated: December 17, 2025*
