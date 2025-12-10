# 🚪 Gate Control Quick Setup

## ⚡ Quick Start Checklist

### 1️⃣ Arduino Configuration (gate.ino)
```cpp
// WiFi Credentials
const char* ssid = "wifi";
const char* password = "123456789";

// 🔴 IMPORTANT: Update this with your server IP!
const char* serverUrl = "http://YOUR_SERVER_IP/api/gate/check-queue/";
```

**Replace `YOUR_SERVER_IP` with:**
- Production: `212.85.27.241`
- Local test: Your computer's local IP (e.g., `192.168.1.100:8000`)

### 2️⃣ Hardware Wiring
```
ESP32 Pin 25 -> Motor Driver ENA (Speed)
ESP32 Pin 26 -> Motor Driver IN1 (Direction 1)  
ESP32 Pin 27 -> Motor Driver IN2 (Direction 2)
```

### 3️⃣ Upload & Test
1. Connect ESP32 via USB
2. Select Board: ESP32 Dev Module
3. Upload `gate.ino`
4. Open Serial Monitor (115200 baud)
5. Verify WiFi connection and server communication

## 🔄 How Gate Works

**When attendance is recorded:**
1. ↻ Clockwise rotation for **3 seconds** (gate opens)
2. ⏸ Stop for **5 seconds** (people pass)
3. ↺ Counter-clockwise for **3 seconds** (gate closes)

**Total cycle time:** 11 seconds

## 🌐 API Endpoints

### Arduino Polls This
```
GET /api/gate/check-queue/
Response: {"success": true, "cycles": 1, "message": "1 gate cycle(s) to perform"}
```

### Server Triggers This (Automatic)
```
POST /api/gate/trigger/
Response: {"success": true, "queue_length": 1}
```

## 🧪 Testing

### Test Server from Browser
```
http://YOUR_SERVER_IP/api/gate/check-queue/
```
Should return JSON response.

### Test Gate Operation
1. Record attendance (time in or time out)
2. Watch Serial Monitor - should show gate cycle execution
3. Gate should rotate → stop → reverse → stop

## ⚙️ Adjustments

### Change Gate Speed
```cpp
ledcWrite(pwmChannel, 255);   // 255=MAX, 128=HALF
```

### Change Timings
```cpp
delay(3000);  // Clockwise time (ms)
delay(5000);  // Stop time (ms)
delay(3000);  // Counter-clockwise time (ms)
```

### Change Check Interval
```cpp
const unsigned long checkInterval = 2000;  // Check queue every 2 seconds
```

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| WiFi won't connect | Check SSID/password, use 2.4GHz WiFi |
| Can't reach server | Verify serverUrl, check firewall |
| Gate doesn't move | Check power supply & wiring |
| Wrong rotation | Swap IN1 & IN2 pins |

## 📋 Server Files Modified

- `PROTECHAPP/views/face_recognition_views.py` - Gate API & attendance integration
- `PROTECHAPP/urls.py` - API endpoints  
- `PROTECH/settings.py` - ALLOWED_HOSTS updated
- `gate.ino` - Arduino control code

## ✅ Success Indicators

**Arduino Serial Monitor should show:**
```
WiFi connected!
IP address: 192.168.1.XXX
Checking gate queue...
Server response: {"success":true,"cycles":0,...}
```

**When attendance recorded:**
```
Cycles to perform: 1
Performing cycle 1 of 1
Starting gate cycle...
Rotating clockwise (3s)
Stopping (5s)
Rotating counter-clockwise (3s)
Cycle complete
```

---

📖 **Full documentation:** See `GATE_CONTROL_SETUP.md`
