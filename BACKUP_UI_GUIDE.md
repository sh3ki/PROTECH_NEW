# Database Backup System - User Interface Guide

## 📍 Location
**Admin Panel → System Settings → Backup & Recovery Section**

---

## 🖥️ What You'll See

### Backup & Recovery Section
Located on the System Settings page, below the "Late Time Cutoff" section.

---

## 🎯 Features

### 1. Manual Backup
```
┌─────────────────────────────────────────────────────────┐
│ Manual Backup                                           │
│ Create and download a database backup now               │
│                                    [Download Backup] ← Click here
└─────────────────────────────────────────────────────────┘
```
- **Purpose**: Create and download a backup immediately
- **Action**: Click button → File downloads to your computer
- **File Format**: `protech_backup_YYYYMMDD_HHMMSS.sql`
- **No Setup Required**: Works without background services

### 2. Automatic Backups Info
```
┌─────────────────────────────────────────────────────────┐
│ 🕐 Automatic Backups                                    │
│                                                          │
│ Daily backups run automatically at 00:00                │
│ (midnight) Asia/Manila Time                             │
│                                                          │
│ Backups are stored in the "database backup" folder      │
│ on the server. The system keeps the last 30 backups     │
│ automatically.                                           │
└─────────────────────────────────────────────────────────┘
```
- **Schedule**: Midnight Manila Time daily
- **Location**: Server's "database backup" folder
- **Retention**: Last 30 backups kept automatically

### 3. Recent Backups List
```
┌─────────────────────────────────────────────────────────┐
│ Recent Backups                              [🔄 Refresh] │
│                                                          │
│ 📄 protech_backup_20251201_000012.sql                  │
│    2025-12-01 00:00:12 • 45.3 MB                       │
│                                                          │
│ 📄 protech_backup_20251130_000009.sql                  │
│    2025-11-30 00:00:09 • 44.8 MB                       │
│                                                          │
│ 📄 protech_backup_20251129_000015.sql                  │
│    2025-11-29 00:00:15 • 44.2 MB                       │
│                                                          │
│ Showing last 10 backups. Total: 25 backup(s) available. │
└─────────────────────────────────────────────────────────┘
```
- **Shows**: Last 10 backups
- **Info**: Filename, timestamp, file size
- **Refresh**: Click refresh button to update list

---

## 📱 Step-by-Step Usage

### How to Download a Manual Backup

1. **Login** as Administrator

2. **Navigate** to System Settings
   ```
   Sidebar → Settings
   ```

3. **Scroll** to "Backup & Recovery" section

4. **Click** the green "Download Backup" button
   ```
   [Download Backup]
   ```

5. **Wait** for file generation (usually 5-30 seconds)

6. **Save** the downloaded file
   - File will appear in your Downloads folder
   - Format: `protech_backup_20251201_143055.sql`

---

## 🔍 What Each Section Shows

### Section 1: Attendance Device Mode
- Configure how attendance devices work
- Choose between Separate or Hybrid mode

### Section 2: Late Time Cutoff
- Set cutoff time for marking students late
- Uses Asia/Manila timezone

### Section 3: Backup & Recovery ⭐ NEW
- **Manual Backup**: Download database on-demand
- **Automatic Info**: When automatic backups run
- **Recent Backups**: List of existing backups

---

## 💡 Tips & Notes

### ✅ Good to Know
- Manual backups work anytime, no configuration needed
- Downloaded files are in PostgreSQL SQL format
- Files can be opened in text editor (they're SQL commands)
- Automatic backups require background services running

### ⚠️ Important
- Backup files contain **sensitive data**
- Store backups securely
- Don't share backup files publicly
- Keep downloads in a secure location

### 🎯 Best Practices
1. Download manual backup before major updates
2. Keep copies of important backups offline
3. Test restore procedure periodically
4. Monitor disk space for backup folder
5. Verify automatic backups are running

---

## 🆘 Troubleshooting UI

### Button says "Downloading..."
- **Normal**: Backup is being created
- **Wait**: Usually takes 5-30 seconds
- **If stuck**: Refresh page and try again

### No backups listed
- **Possible**: No automatic backups yet
- **Check**: Are background services running?
- **Solution**: Download manual backup first

### Error message appears
- **Read**: Error message shows what went wrong
- **Common**: "pg_dump not found" means PostgreSQL tools not installed
- **Check**: Server logs for details

### Refresh doesn't update list
- **Try**: Hard refresh (Ctrl+F5)
- **Check**: Browser console for errors
- **Wait**: Give it a few seconds

---

## 🎨 UI Features

### Visual Design
- Clean, modern interface
- Dark mode support
- Responsive design (works on mobile)
- Clear visual hierarchy

### Interactive Elements
- Hover effects on buttons
- Loading states during download
- Real-time refresh capability
- Toast notifications for success/error

### Accessibility
- Clear labels and descriptions
- Keyboard navigation support
- Screen reader friendly
- Color-blind friendly

---

## 📊 Status Indicators

### Download Button States
```
[Download Backup]     → Ready to download
[Downloading...]      → Creating backup
```

### Refresh Icon
```
🔄 Refresh           → Click to reload list
⟳ (spinning)        → Loading backups
```

---

## 🎓 Quick Reference

| Action | Location | Result |
|--------|----------|--------|
| Manual Backup | Click green button | File downloads |
| View Backups | Scroll to list | See recent backups |
| Refresh List | Click refresh icon | Update backup list |
| Check Schedule | Read info box | See automatic schedule |

---

## 📸 What It Looks Like

### Color Scheme
- **Green Button**: Manual backup (safe action)
- **Blue Info Box**: Automatic backup information
- **Gray Cards**: Individual backup items
- **White/Dark Background**: Based on system theme

### Layout
```
System Settings Page
├── Attendance Mode Section
├── Late Time Cutoff Section
└── Backup & Recovery Section (NEW!)
    ├── Manual Backup Button
    ├── Automatic Backup Info
    └── Recent Backups List
```

---

## ✨ Advanced Features

### Auto-refresh
- Backups list updates when clicking refresh
- Shows up to 10 most recent backups
- Displays total count at bottom

### File Information
- Filename shows exact timestamp
- Size displayed in MB for easy reading
- Created date in readable format

### Smart Design
- Works with existing dark mode
- Responsive on all screen sizes
- Fast loading with Alpine.js
- AJAX refresh without page reload

---

**Need technical details?** See other documentation files:
- `DATABASE_BACKUP_DEPLOYMENT.md` - Full setup guide
- `BACKUP_QUICK_COMMANDS.md` - Command reference
- `SYSTEMD_SERVICE_FILES.md` - Service configuration
