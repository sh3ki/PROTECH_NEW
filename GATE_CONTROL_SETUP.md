# Gate Control System Setup Guide

## Overview
This system integrates automatic gate control with the PROTECH attendance system. When a student records attendance (time in or time out), the gate automatically opens using a queue-based system.

## System Architecture

### Components
1. **Django Server** - Manages gate queue and provides API endpoints
2. **Arduino ESP32** - Controls physical gate motor via WiFi
3. **Attendance System** - Triggers gate when attendance is recorded

## How It Works

### Gate Operation Cycle
When attendance is recorded:
1. Server adds a trigger to the gate queue
2. Arduino checks the queue every 2 seconds
3. For each queued trigger, the gate performs one full cycle:
   - **Rotate clockwise** for 3 seconds (gate opens)
   - **Stop** for 5 seconds (people pass through)
   - **Rotate counter-clockwise** for 3 seconds (gate closes)
   - Total cycle time: **11 seconds**

### Queue System
- Multiple attendance records create multiple queue entries
- Arduino processes all queued cycles in sequence
- Queue is cleared after Arduino retrieves it

## Configuration

### 1. Arduino Setup (gate.ino)

#### WiFi Credentials
```cpp
const char* ssid = "wifi";
const char* password = "123456789";
```

#### Server URL Configuration
**IMPORTANT**: Update this line with your deployed server IP/domain:
```cpp
const char* serverUrl = "http://YOUR_SERVER_IP/api/gate/check-queue/";
```

**Examples:**
- Local testing: `http://192.168.1.100:8000/api/gate/check-queue/`
- Production: `http://212.85.27.241/api/gate/check-queue/`
- Domain: `http://yourschool.com/api/gate/check-queue/`

#### Hardware Connections
```
ESP32 Pin 26 -> Motor Driver IN1 (Direction 1)
ESP32 Pin 27 -> Motor Driver IN2 (Direction 2)
ESP32 Pin 25 -> Motor Driver ENA (PWM Speed Control)
```

### 2. Server API Endpoints

#### Check Gate Queue (Arduino polls this)
- **URL**: `/api/gate/check-queue/`
- **Method**: GET
- **Response**:
```json
{
  "success": true,
  "cycles": 2,
  "message": "2 gate cycle(s) to perform"
}
```

#### Trigger Gate (Internal use)
- **URL**: `/api/gate/trigger/`
- **Method**: POST
- **Response**:
```json
{
  "success": true,
  "queue_length": 1,
  "message": "Gate trigger added to queue"
}
```

## Installation Steps

### Arduino Side

1. **Install Arduino IDE**
   - Download from https://www.arduino.cc/en/software

2. **Install ESP32 Board Support**
   - File -> Preferences -> Additional Board Manager URLs
   - Add: `https://dl.espressif.com/dl/package_esp32_index.json`
   - Tools -> Board -> Boards Manager -> Search "ESP32" -> Install

3. **Configure Board**
   - Tools -> Board -> ESP32 Arduino -> ESP32 Dev Module
   - Tools -> Upload Speed -> 115200
   - Tools -> Port -> Select your ESP32 COM port

4. **Update Configuration**
   - Open `gate.ino`
   - Update WiFi credentials (if different)
   - **Update `serverUrl` with your actual server address**

5. **Upload Code**
   - Click Upload button
   - Wait for "Done uploading"
   - Open Serial Monitor (115200 baud) to see connection status

### Server Side

1. **Django Server** (Already configured)
   - Gate endpoints are in `PROTECHAPP/views/face_recognition_views.py`
   - URLs are in `PROTECHAPP/urls.py`
   - No additional configuration needed

2. **Allow Arduino IP in Firewall** (if needed)
   - Ensure port 8000 (or your production port) is accessible
   - Add Arduino IP to allowed hosts if using IP filtering

## Testing

### 1. Test WiFi Connection
Open Arduino Serial Monitor and verify:
```
Connecting to WiFi: wifi
.....
WiFi connected!
IP address: 192.168.1.XXX
```

### 2. Test Server Connectivity
Monitor Serial output - should show:
```
Checking gate queue...
Server response: {"success":true,"cycles":0,"message":"No gate cycles in queue"}
```

### 3. Test Attendance Integration
1. Record a time in or time out via face recognition
2. Check Arduino Serial Monitor - should show:
```
Checking gate queue...
Server response: {"success":true,"cycles":1,"message":"1 gate cycle(s) to perform"}
Cycles to perform: 1
Performing cycle 1 of 1
Starting gate cycle...
Rotating clockwise (3s)
Stopping (5s)
Rotating counter-clockwise (3s)
Cycle complete
```

### 4. Test Multiple Queue Entries
1. Record multiple attendances quickly
2. Arduino should process all cycles in sequence

## Troubleshooting

### WiFi Connection Issues
- **Problem**: "WiFi connection failed!"
- **Solutions**:
  - Verify SSID and password are correct
  - Check if WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
  - Ensure WiFi is in range
  - Try rebooting the router

### Server Connection Issues
- **Problem**: "Connection failed" or "HTTP error code"
- **Solutions**:
  - Verify `serverUrl` is correct
  - Test URL in browser: should return JSON response
  - Check firewall settings
  - Ensure Django server is running
  - Verify server is accessible from Arduino's network

### Gate Doesn't Move
- **Problem**: Queue processed but motor doesn't rotate
- **Solutions**:
  - Check motor power supply (separate from ESP32)
  - Verify motor driver connections (IN1, IN2, ENA)
  - Test motor manually by uploading simple test code
  - Check motor driver enable pin
  - Verify motor direction pins are working

### Gate Moves Wrong Direction
- **Problem**: Gate opens when it should close
- **Solutions**:
  - Swap IN1 and IN2 connections
  - Or modify code: swap HIGH/LOW in `performGateCycle()`

### Queue Not Processing
- **Problem**: Attendance recorded but gate doesn't open
- **Solutions**:
  - Check Django server logs for errors
  - Verify attendance recording is successful
  - Check if `trigger_gate_opening()` is being called
  - Monitor Arduino Serial to see if queue is retrieved

## Advanced Configuration

### Adjust Gate Timing
Edit in `gate.ino`:
```cpp
delay(3000);  // Clockwise time (milliseconds)
delay(5000);  // Stop time (milliseconds)
delay(3000);  // Counter-clockwise time (milliseconds)
```

### Adjust Queue Check Interval
Edit in `gate.ino`:
```cpp
const unsigned long checkInterval = 2000;  // Check every 2 seconds
```

### Adjust Motor Speed
Edit in `gate.ino`:
```cpp
ledcWrite(pwmChannel, 255);   // 255 = MAX, 128 = HALF, adjust as needed
```

## Security Considerations

1. **Network Security**
   - Use HTTPS in production (requires SSL certificate)
   - Implement API authentication if needed
   - Restrict API access to Arduino IP only

2. **Physical Security**
   - Secure Arduino and motor driver in locked enclosure
   - Use tamper-proof connections
   - Add emergency stop button

## Maintenance

### Regular Checks
- Monitor Arduino connection status daily
- Check motor operation weekly
- Verify queue is being processed correctly
- Check server logs for errors

### Common Maintenance Tasks
- Clean motor and gate mechanism monthly
- Check wire connections quarterly
- Update firmware as needed
- Monitor power supply stability

## Support

For issues or questions:
1. Check Serial Monitor output for diagnostic messages
2. Review server logs: `/var/log/django/` (production)
3. Test individual components separately
4. Document any error messages for troubleshooting

---

**Last Updated**: December 10, 2025
