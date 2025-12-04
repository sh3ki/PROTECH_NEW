# Database Backup Installation Checklist

Use this checklist to ensure everything is installed and configured correctly.

---

## ✅ Pre-Installation Checklist

### 1. System Requirements
- [ ] Ubuntu 24.04 Server
- [ ] Python 3.x with venv
- [ ] PostgreSQL database running
- [ ] Django project working
- [ ] Admin user access

---

## ✅ Installation Steps

### Step 1: Install System Dependencies
```bash
sudo apt update
sudo apt install postgresql-client-16 redis-server
```

- [ ] PostgreSQL client installed
- [ ] Redis server installed

**Verify:**
```bash
pg_dump --version  # Should show version
redis-cli ping     # Should return: PONG
```

---

### Step 2: Install Python Dependencies
```bash
cd /path/to/PROTECH_NEW
source venv/bin/activate
pip install -r requirements.txt
```

- [ ] Celery installed
- [ ] Redis Python client installed
- [ ] All dependencies installed without errors

**Verify:**
```bash
pip list | grep -i celery
pip list | grep -i redis
```

---

### Step 3: Configure Environment
Add to `.env` file:
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

- [ ] Celery broker URL configured
- [ ] Celery result backend configured

**Verify:**
```bash
grep CELERY_BROKER_URL .env
grep CELERY_RESULT_BACKEND .env
```

---

### Step 4: Start Redis
```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

- [ ] Redis started
- [ ] Redis enabled on boot

**Verify:**
```bash
sudo systemctl status redis-server  # Should show "active (running)"
```

---

### Step 5: Create Backup Directory
```bash
mkdir -p "/path/to/PROTECH_NEW/database backup"
chmod 755 "/path/to/PROTECH_NEW/database backup"
```

- [ ] Backup directory created
- [ ] Proper permissions set

**Verify:**
```bash
ls -ld "/path/to/PROTECH_NEW/database backup"
```

---

### Step 6: Test Manual Backup
```bash
python manage.py shell
```
Then in shell:
```python
from PROTECHAPP.backup_utils import create_database_backup
success, filepath, error = create_database_backup()
print(f"Success: {success}, File: {filepath}")
exit()
```

- [ ] Manual backup works
- [ ] Backup file created in folder
- [ ] No errors displayed

---

### Step 7: Configure systemd Services

#### Create log/pid directories:
```bash
sudo mkdir -p /var/log/celery
sudo mkdir -p /var/run/celery
sudo chown YOUR_USERNAME:YOUR_USERNAME /var/log/celery
sudo chown YOUR_USERNAME:YOUR_USERNAME /var/run/celery
```

- [ ] Log directory created
- [ ] PID directory created
- [ ] Correct ownership set

#### Create service files:
Use templates from `SYSTEMD_SERVICE_FILES.md`

- [ ] Worker service file created at `/etc/systemd/system/protech-celery-worker.service`
- [ ] Beat service file created at `/etc/systemd/system/protech-celery-beat.service`
- [ ] Placeholders replaced (username, paths)
- [ ] File permissions set (644)

**Verify:**
```bash
ls -l /etc/systemd/system/protech-celery-*.service
```

---

### Step 8: Enable and Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable protech-celery-worker
sudo systemctl enable protech-celery-beat
sudo systemctl start protech-celery-worker
sudo systemctl start protech-celery-beat
```

- [ ] systemd reloaded
- [ ] Services enabled
- [ ] Services started

**Verify:**
```bash
sudo systemctl status protech-celery-worker
sudo systemctl status protech-celery-beat
```
Both should show "active (running)"

---

### Step 9: Test Background Backup
```bash
python manage.py shell -c "from PROTECHAPP.tasks import perform_daily_backup; print(perform_daily_backup.delay().get())"
```

- [ ] Task executes without errors
- [ ] Shows success status
- [ ] Backup file created

**Verify:**
```bash
ls -lt "/path/to/PROTECH_NEW/database backup/" | head -5
```

---

### Step 10: Test Web Interface
1. Open browser
2. Login as admin
3. Go to System Settings
4. Scroll to "Backup & Recovery" section

- [ ] Section visible on page
- [ ] "Download Backup" button present
- [ ] "Recent Backups" list shows
- [ ] Can click and download backup

---

## ✅ Post-Installation Verification

### Check Services Status
```bash
sudo systemctl status protech-celery-worker
sudo systemctl status protech-celery-beat
sudo systemctl status redis-server
```

- [ ] All services active (running)
- [ ] No error messages in status

---

### Check Logs
```bash
sudo journalctl -u protech-celery-worker -n 20
sudo journalctl -u protech-celery-beat -n 20
```

- [ ] Worker logs show activity
- [ ] Beat logs show scheduler running
- [ ] No error messages

---

### Verify Schedule
```bash
python manage.py shell
```
Then:
```python
from PROTECH.celery import app
print(app.conf.beat_schedule)
```

- [ ] Shows 'daily-database-backup' task
- [ ] Schedule is crontab(hour=16, minute=0)
- [ ] Task points to 'PROTECHAPP.tasks.perform_daily_backup'

---

### Check Backup Files
```bash
ls -lh "/path/to/PROTECH_NEW/database backup/"
```

- [ ] At least 1 backup file exists
- [ ] Files have .sql extension
- [ ] Files have reasonable size (not 0 bytes)
- [ ] Timestamps in filenames look correct

---

## ✅ Monitoring Checklist

### Daily Tasks
- [ ] Check services are running
- [ ] Verify backup was created at midnight
- [ ] Check log files for errors

### Weekly Tasks
- [ ] Review backup file sizes
- [ ] Check disk space usage
- [ ] Verify old backups are cleaned up

### Monthly Tasks
- [ ] Test backup restore procedure
- [ ] Review logs for patterns
- [ ] Update documentation if needed

---

## ✅ Security Checklist

- [ ] Backup folder has restricted permissions (700 or 755)
- [ ] .env file not in version control
- [ ] Service files have correct ownership
- [ ] Redis password configured (if networked)
- [ ] Database credentials secure
- [ ] Log files have restricted access

---

## ✅ Troubleshooting Reference

### If services won't start:
```bash
sudo journalctl -xe  # Check system logs
sudo systemctl status protech-celery-worker -l  # Detailed status
```

### If backups fail:
```bash
# Check pg_dump
which pg_dump
pg_dump --version

# Check database connection
python manage.py dbshell

# Check permissions
ls -ld "/path/to/PROTECH_NEW/database backup"
```

### If Redis issues:
```bash
redis-cli ping
sudo systemctl restart redis-server
sudo systemctl status redis-server
```

---

## ✅ Quick Test Commands

All systems working:
```bash
# Test 1: Redis
redis-cli ping

# Test 2: Celery worker
celery -A PROTECH inspect active

# Test 3: Manual backup
python manage.py shell -c "from PROTECHAPP.tasks import perform_daily_backup; print(perform_daily_backup.delay().get())"

# Test 4: Check files
ls -l "database backup/"

# Test 5: Service status
sudo systemctl is-active protech-celery-worker
sudo systemctl is-active protech-celery-beat
```

All commands should succeed without errors.

---

## ✅ Documentation Files Created

- [ ] `BACKUP_IMPLEMENTATION_SUMMARY.md` - Overview
- [ ] `DATABASE_BACKUP_DEPLOYMENT.md` - Full deployment guide
- [ ] `BACKUP_QUICK_COMMANDS.md` - Quick command reference
- [ ] `SYSTEMD_SERVICE_FILES.md` - Service configuration
- [ ] `BACKUP_UI_GUIDE.md` - UI usage guide
- [ ] `INSTALLATION_CHECKLIST.md` - This file

---

## ✅ Success Indicators

You're fully set up when:

✅ Redis is running  
✅ Both Celery services are active  
✅ Manual backup downloads from UI  
✅ Backup files appear in folder  
✅ Services restart on server reboot  
✅ No errors in logs  
✅ Schedule shows correct time (16:00 UTC)  
✅ Old backups cleaned up automatically  

---

## 🎉 Deployment Complete!

If all items are checked, your database backup system is **fully operational**.

**Next Steps:**
1. Monitor first automatic backup at 00:00 Manila time
2. Set up monitoring/alerting
3. Document backup restore procedure
4. Train team on using the system

**Need help?** Check the other documentation files or logs.
