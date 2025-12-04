# Database Backup System - Deployment Guide

## Overview
This system provides:
1. **Manual Backup**: Download database backup on-demand via admin settings
2. **Automatic Daily Backup**: Runs at 00:00 Manila Time (16:00 UTC) every day
3. **Local Storage**: Backups stored in "database backup" folder with timestamps

## Prerequisites

### 1. PostgreSQL Client Tools
The system requires `pg_dump` to create backups.

**Install on Ubuntu 24.04:**
```bash
sudo apt update
sudo apt install postgresql-client-16
```

**Verify installation:**
```bash
pg_dump --version
```

### 2. Redis Server
Required for Celery message broker.

**Install on Ubuntu 24.04:**
```bash
sudo apt update
sudo apt install redis-server
```

**Start Redis:**
```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

### 3. Python Dependencies
Install required packages:
```bash
cd /path/to/PROTECH_NEW
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

### 1. Environment Variables
Add to your `.env` file:
```env
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 2. Database Configuration
Ensure your `.env` has proper database credentials:
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=PROTECH
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

## Running the Background Job

### Option 1: Using systemd (Recommended for Production)

#### Create Celery Worker Service

Create file: `/etc/systemd/system/protech-celery-worker.service`
```ini
[Unit]
Description=PROTECH Celery Worker
After=network.target redis-server.service postgresql.service

[Service]
Type=forking
User=your_username
Group=your_username
WorkingDirectory=/path/to/PROTECH_NEW
Environment="PATH=/path/to/PROTECH_NEW/venv/bin"
ExecStart=/path/to/PROTECH_NEW/venv/bin/celery -A PROTECH worker \
    --detach \
    --logfile=/var/log/celery/worker.log \
    --pidfile=/var/run/celery/worker.pid \
    --loglevel=info

ExecStop=/path/to/PROTECH_NEW/venv/bin/celery -A PROTECH control shutdown
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Create Celery Beat Service (Scheduler)

Create file: `/etc/systemd/system/protech-celery-beat.service`
```ini
[Unit]
Description=PROTECH Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=your_username
Group=your_username
WorkingDirectory=/path/to/PROTECH_NEW
Environment="PATH=/path/to/PROTECH_NEW/venv/bin"
ExecStart=/path/to/PROTECH_NEW/venv/bin/celery -A PROTECH beat \
    --logfile=/var/log/celery/beat.log \
    --pidfile=/var/run/celery/beat.pid \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Setup Log and PID Directories

```bash
# Create log directory
sudo mkdir -p /var/log/celery
sudo chown your_username:your_username /var/log/celery

# Create PID directory
sudo mkdir -p /var/run/celery
sudo chown your_username:your_username /var/run/celery
```

#### Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable protech-celery-worker
sudo systemctl enable protech-celery-beat

# Start services
sudo systemctl start protech-celery-worker
sudo systemctl start protech-celery-beat

# Check status
sudo systemctl status protech-celery-worker
sudo systemctl status protech-celery-beat
```

### Option 2: Manual Start (Development/Testing)

Open two terminal windows:

**Terminal 1 - Celery Worker:**
```bash
cd /path/to/PROTECH_NEW
source venv/bin/activate
celery -A PROTECH worker --loglevel=info
```

**Terminal 2 - Celery Beat (Scheduler):**
```bash
cd /path/to/PROTECH_NEW
source venv/bin/activate
celery -A PROTECH beat --loglevel=info
```

## Management Commands

### Start Services
```bash
sudo systemctl start protech-celery-worker
sudo systemctl start protech-celery-beat
```

### Stop Services
```bash
sudo systemctl stop protech-celery-worker
sudo systemctl stop protech-celery-beat
```

### Restart Services
```bash
sudo systemctl restart protech-celery-worker
sudo systemctl restart protech-celery-beat
```

### Check Status
```bash
sudo systemctl status protech-celery-worker
sudo systemctl status protech-celery-beat
```

### View Logs
```bash
# Worker logs
sudo tail -f /var/log/celery/worker.log

# Beat scheduler logs
sudo tail -f /var/log/celery/beat.log

# Or use journalctl
sudo journalctl -u protech-celery-worker -f
sudo journalctl -u protech-celery-beat -f
```

### Stop Services Manually (if running in terminal)
Press `Ctrl+C` in each terminal window, or:
```bash
# Find and kill processes
pkill -f "celery.*PROTECH worker"
pkill -f "celery.*PROTECH beat"
```

## Backup Schedule

- **Daily Automatic Backup**: 00:00 Asia/Manila Time (16:00 UTC)
- **Retention**: Last 30 backups are kept automatically
- **Storage Location**: `PROTECH_NEW/database backup/`
- **Filename Format**: `protech_backup_YYYYMMDD_HHMMSS.sql`

## Testing the System

### 1. Test Manual Backup
1. Open admin panel
2. Go to System Settings
3. Click "Download Backup" button
4. Verify file downloads successfully

### 2. Test Background Worker
```bash
# In Django shell
python manage.py shell

# Run this:
from PROTECHAPP.tasks import perform_daily_backup
result = perform_daily_backup.delay()
print(result.get())
```

### 3. Check Backup Files
```bash
ls -lh "/path/to/PROTECH_NEW/database backup/"
```

## Troubleshooting

### Issue: pg_dump not found
**Solution:** Install PostgreSQL client tools
```bash
sudo apt install postgresql-client-16
```

### Issue: Redis connection refused
**Solution:** Start Redis server
```bash
sudo systemctl start redis-server
sudo systemctl status redis-server
```

### Issue: Permission denied for backup directory
**Solution:** Create directory with proper permissions
```bash
mkdir -p "/path/to/PROTECH_NEW/database backup"
chmod 755 "/path/to/PROTECH_NEW/database backup"
```

### Issue: Celery workers not processing tasks
**Solution:** 
1. Check if Redis is running: `redis-cli ping`
2. Check if worker is running: `sudo systemctl status protech-celery-worker`
3. Check logs: `sudo journalctl -u protech-celery-worker -n 50`

### Issue: Scheduled tasks not running
**Solution:**
1. Verify beat is running: `sudo systemctl status protech-celery-beat`
2. Check beat logs: `sudo journalctl -u protech-celery-beat -n 50`
3. Verify schedule in Django shell:
```python
from PROTECH.celery import app
print(app.conf.beat_schedule)
```

## Security Considerations

1. **Database Credentials**: Never commit `.env` file
2. **Backup Files**: Contain sensitive data - restrict access
3. **File Permissions**: 
   ```bash
   chmod 700 "/path/to/PROTECH_NEW/database backup"
   ```
4. **Redis**: Configure password if exposed to network
5. **Celery Logs**: Contain operational data - restrict access

## Monitoring

### Check Last Backup
Via admin settings page - shows last 10 backups with timestamps and sizes.

### Monitor Celery
```bash
# Monitor in real-time
celery -A PROTECH inspect active
celery -A PROTECH inspect scheduled
celery -A PROTECH inspect stats
```

### Check Disk Space
```bash
df -h "/path/to/PROTECH_NEW/database backup"
```

## Quick Reference Commands

```bash
# START SERVICES
sudo systemctl start protech-celery-worker protech-celery-beat

# STOP SERVICES  
sudo systemctl stop protech-celery-worker protech-celery-beat

# RESTART SERVICES
sudo systemctl restart protech-celery-worker protech-celery-beat

# CHECK STATUS
sudo systemctl status protech-celery-worker
sudo systemctl status protech-celery-beat

# VIEW LOGS
sudo journalctl -u protech-celery-worker -f
sudo journalctl -u protech-celery-beat -f

# TEST BACKUP MANUALLY
python manage.py shell -c "from PROTECHAPP.tasks import perform_daily_backup; print(perform_daily_backup.delay().get())"
```

## Production Deployment Checklist

- [ ] PostgreSQL client tools installed
- [ ] Redis server installed and running
- [ ] Python dependencies installed
- [ ] Environment variables configured
- [ ] Backup directory created with proper permissions
- [ ] systemd service files created
- [ ] Services enabled and started
- [ ] Manual backup tested successfully
- [ ] Automatic backup scheduled and verified
- [ ] Monitoring and alerts configured
- [ ] Log rotation configured
- [ ] Disk space monitoring enabled

## Support

For issues or questions:
1. Check logs: `/var/log/celery/`
2. Verify Redis: `redis-cli ping`
3. Test database connection: `python manage.py dbshell`
4. Check Celery status: `celery -A PROTECH inspect stats`
