# Quick Start Guide: Hybrid Attendance Mode

## How to Use the New Feature

### For Administrators

#### Step 1: Access Settings
1. Login to PROTECH as an **Administrator**
2. Navigate to **Settings** from the sidebar menu
3. You'll see the "Attendance Device Mode" section

#### Step 2: Choose Your Mode

**Option A: Separate Mode (Default)**
- Time In and Time Out on different screens
- Use when you have two separate devices
- Traditional setup - one device at entrance, one at exit

**Option B: Hybrid Mode (NEW)**
- Both Time In and Time Out on the same screen
- Use when you have one device with two cameras
- Space-efficient setup - single device handles both

#### Step 3: Save Settings
1. Select your preferred mode by clicking the radio button
2. Click the **"Save Settings"** button
3. You'll see a success message confirming the change
4. Changes take effect immediately!

### For Device Users

#### When Mode is SEPARATE:
1. Go to: `http://127.0.0.1:8000/select-device/`
2. You'll see **TWO buttons**:
   - 🔵 **TIME IN** (Blue) - Click for morning attendance
   - 🟣 **TIME OUT** (Purple) - Click for afternoon attendance
3. Choose the appropriate button for your device

#### When Mode is HYBRID:
1. Go to: `http://127.0.0.1:8000/select-device/`
2. You'll see **ONE button**:
   - 🟣 **HYBRID MODE** (Purple) - Click to access dual camera interface
3. This opens a split-screen with:
   - **Left side**: TIME IN camera (Blue theme)
   - **Right side**: TIME OUT camera (Indigo theme)
4. Select different cameras for each side from the dropdowns

## URLs Reference

| Page | URL |
|------|-----|
| Landing Page | `http://127.0.0.1:8000/` |
| Select Device | `http://127.0.0.1:8000/select-device/` |
| Time In (Separate) | `http://127.0.0.1:8000/time-in/` |
| Time Out (Separate) | `http://127.0.0.1:8000/time-out/` |
| Hybrid Attendance | `http://127.0.0.1:8000/hybrid-attendance/` |
| Admin Settings | `http://127.0.0.1:8000/admin/settings/` |

## Visual Guide

### Settings Page Layout
```
┌─────────────────────────────────────────────┐
│  Attendance Device Mode                     │
├─────────────────────────────────────────────┤
│                                             │
│  ○ Separate Screens                        │
│    Time In and Time Out on different pages │
│                                             │
│  ● Hybrid Mode (Dual Camera)               │
│    Time In and Time Out on same page       │
│                                             │
│            [Save Settings]                  │
└─────────────────────────────────────────────┘
```

### Select Device - Separate Mode
```
┌──────────────────────────────────────────┐
│  Select Attendance Device Option         │
├──────────────────────────────────────────┤
│                                          │
│  ┌───────────┐     ┌──────────────┐    │
│  │ TIME IN   │     │  TIME OUT    │    │
│  │   🔵      │     │     🟣       │    │
│  └───────────┘     └──────────────┘    │
│                                          │
│         [Back to Home]                   │
└──────────────────────────────────────────┘
```

### Select Device - Hybrid Mode
```
┌──────────────────────────────────────────┐
│  Select Attendance Device Option         │
├──────────────────────────────────────────┤
│                                          │
│       ┌─────────────────────┐           │
│       │   HYBRID MODE       │           │
│       │       🟣🟣          │           │
│       │  (Dual Camera)      │           │
│       └─────────────────────┘           │
│                                          │
│         [Back to Home]                   │
└──────────────────────────────────────────┘
```

### Hybrid Attendance Page Layout
```
┌─────────────────────────────────────────────────────────┐
│                    PROTECH: HYBRID ATTENDANCE            │
├───────────────────────────┬─────────────────────────────┤
│      TIME IN (Blue)       │    TIME OUT (Indigo)        │
├───────────────────────────┼─────────────────────────────┤
│ Camera: [Select ▼]        │ Camera: [Select ▼]          │
├───────────────────────────┼─────────────────────────────┤
│                           │                             │
│    📹 Camera Feed 1       │    📹 Camera Feed 2         │
│                           │                             │
│      [FPS: 30]            │      [FPS: 30]              │
│                           │                             │
├───────────────────────────┼─────────────────────────────┤
│ Students Timed In: 0      │ Students Timed Out: 0       │
└───────────────────────────┴─────────────────────────────┘
```

## Camera Setup Tips

### For Hybrid Mode:
1. **Use Two Different Cameras**:
   - If you have a laptop, use built-in webcam for one feed
   - Use external USB camera for the second feed
   - OR use two external USB cameras

2. **Camera Positioning**:
   - Position one camera at entrance (Time In)
   - Position other camera at exit (Time Out)
   - Or use both cameras at same location but different angles

3. **Browser Permissions**:
   - First time: Browser will ask for camera permission
   - Click "Allow" when prompted
   - Permission needed for each camera

### Troubleshooting:

**Problem**: Cameras not showing in dropdown
- **Solution**: Grant camera permissions in browser
- Refresh the page after granting permissions

**Problem**: Same camera appears in both feeds
- **Solution**: You need at least 2 cameras for hybrid mode
- Or select different camera for each side

**Problem**: Camera feed is black
- **Solution**: Check if another app is using the camera
- Close other apps and refresh page

## Best Practices

### When to Use SEPARATE Mode:
✅ Multiple physical locations (entrance/exit)  
✅ Two separate devices available  
✅ Simple setup with dedicated devices  

### When to Use HYBRID Mode:
✅ Single physical location  
✅ Limited devices available  
✅ Want to monitor both in/out from one screen  
✅ Have device with multiple cameras  

## Testing the Feature

1. **Start the server** (if not running):
   ```bash
   python manage.py runserver
   ```

2. **Login as Admin**:
   - Go to: `http://127.0.0.1:8000/login/`
   - Use admin credentials

3. **Change Mode**:
   - Visit: `http://127.0.0.1:8000/admin/settings/`
   - Try both modes

4. **Test Device Selection**:
   - Visit: `http://127.0.0.1:8000/select-device/`
   - Verify correct UI appears

5. **Test Hybrid Page**:
   - Select hybrid mode in settings
   - Click "HYBRID MODE" button
   - Try selecting cameras

## Notes

- Default mode is **SEPARATE** (backward compatible)
- Changes are instant - no need to restart server
- Settings persist in database
- Each mode has its own color scheme for easy identification
- Dark mode support on all pages

## Need Help?

Check the main documentation: `HYBRID_ATTENDANCE_IMPLEMENTATION.md`

---
Enjoy the new hybrid attendance feature! 🎉
