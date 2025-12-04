# Database Backup - Quick Command Reference

## 🚀 Start Background Jobs

### On Ubuntu Server (Production)
```bash
# Start both services
sudo systemctl start protech-celery-worker protech-celery-beat

# Or start individually
sudo systemctl start protech-celery-worker
sudo systemctl start protech-celery-beat
```

### Development (Manual)
```bash
# Terminal 1 - Worker
cd /path/to/PROTECH_NEW
source venv/bin/activate
celery -A PROTECH worker --loglevel=info

# Terminal 2 - Beat Scheduler
cd /path/to/PROTECH_NEW
source venv/bin/activate
celery -A PROTECH beat --loglevel=info
```

---

## 🛑 Stop Background Jobs

### On Ubuntu Server (Production)
```bash
# Stop both services
sudo systemctl stop protech-celery-worker protech-celery-beat

# Or stop individually
sudo systemctl stop protech-celery-worker
sudo systemctl stop protech-celery-beat
```

### Development (Manual)
Press `Ctrl+C` in each terminal, or:
```bash
pkill -f "celery.*PROTECH worker"
pkill -f "celery.*PROTECH beat"
```

---

## 🔄 Restart Background Jobs

```bash
sudo systemctl restart protech-celery-worker
sudo systemctl restart protech-celery-beat
```

---

## ✅ Check Status

```bash
# Check service status
sudo systemctl status protech-celery-worker
sudo systemctl status protech-celery-beat

# Check if processes are running
ps aux | grep celery

# Check Redis connection
redis-cli ping  # Should return: PONG
```

---

## 📋 View Logs

```bash
# Live tail logs
sudo journalctl -u protech-celery-worker -f
sudo journalctl -u protech-celery-beat -f

# Last 50 lines
sudo journalctl -u protech-celery-worker -n 50
sudo journalctl -u protech-celery-beat -n 50

# Log files (if configured)
sudo tail -f /var/log/celery/worker.log
sudo tail -f /var/log/celery/beat.log
```

---

## 🧪 Test Backup Manually

```bash
# From Django shell
python manage.py shell

# Run this in shell:
from PROTECHAPP.tasks import perform_daily_backup
result = perform_daily_backup.delay()
print(result.get())
```

Or one-liner:
```bash
python manage.py shell -c "from PROTECHAPP.tasks import perform_daily_backup; print(perform_daily_backup.delay().get())"
```

---

## 📁 Check Backup Files

```bash
# List backups
ls -lh "/path/to/PROTECH_NEW/database backup/"

# Count backups
ls "/path/to/PROTECH_NEW/database backup/" | wc -l

# Check disk space
du -sh "/path/to/PROTECH_NEW/database backup/"
```

---

## ⚙️ Service Management

```bash
# Enable services to start on boot
sudo systemctl enable protech-celery-worker
sudo systemctl enable protech-celery-beat

# Disable services from starting on boot
sudo systemctl disable protech-celery-worker
sudo systemctl disable protech-celery-beat

# Reload systemd after config changes
sudo systemctl daemon-reload
```

---

## 🔍 Monitor Celery

```bash
# Check active tasks
celery -A PROTECH inspect active

# Check scheduled tasks
celery -A PROTECH inspect scheduled

# Check worker statistics
celery -A PROTECH inspect stats

# List registered tasks
celery -A PROTECH inspect registered
```

---

## 📅 Backup Schedule

- **Time**: 00:00 Asia/Manila (16:00 UTC)
- **Frequency**: Daily
- **Retention**: Last 30 backups
- **Location**: `database backup/` folder
- **Format**: `protech_backup_YYYYMMDD_HHMMSS.sql`

---

## 🆘 Emergency Commands

```bash
# Force stop all Celery processes
sudo pkill -9 -f celery

# Restart Redis
sudo systemctl restart redis-server

# Clear Redis (WARNING: clears all tasks)
redis-cli FLUSHALL

# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
python manage.py dbshell
```

---

## 📝 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "pg_dump not found" | `sudo apt install postgresql-client-16` |
| "Redis connection refused" | `sudo systemctl start redis-server` |
| "Permission denied" | `chmod 755 "database backup"` |
| Worker not processing | Restart: `sudo systemctl restart protech-celery-worker` |
| Schedule not running | Restart beat: `sudo systemctl restart protech-celery-beat` |

---

## 🎯 Installation Quick Start

```bash
# 1. Install dependencies
sudo apt update
sudo apt install postgresql-client-16 redis-server

# 2. Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 3. Install Python packages
cd /path/to/PROTECH_NEW
source venv/bin/activate
pip install -r requirements.txt

# 4. Create systemd services (see DATABASE_BACKUP_DEPLOYMENT.md)

# 5. Start services
sudo systemctl start protech-celery-worker protech-celery-beat

# 6. Enable on boot
sudo systemctl enable protech-celery-worker protech-celery-beat
```

---

## 💡 Remember

- Always check logs if something doesn't work
- Redis must be running for Celery to work
- Worker processes tasks, Beat schedules them
- Both must run for automatic backups
- Manual backups work without Celery (direct download)

---

**Need detailed setup?** See `DATABASE_BACKUP_DEPLOYMENT.md`
