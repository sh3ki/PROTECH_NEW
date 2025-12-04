# 🗄️ PROTECH Database Backup & Recovery System

## 📖 Overview

A complete, production-ready database backup solution for the PROTECH Attendance System with both manual and automatic backup capabilities.

### Key Features

✅ **One-Click Manual Backup** - Download PostgreSQL database instantly  
✅ **Automatic Daily Backups** - Runs at midnight Manila time  
✅ **Smart Retention** - Keeps last 30 backups automatically  
✅ **Production Ready** - systemd integration for Ubuntu servers  
✅ **Beautiful UI** - Integrated into admin settings page  
✅ **Comprehensive Logging** - Track all backup operations  
✅ **Error Handling** - Robust failure detection and reporting  

---

## 🚀 Quick Start

### For Server Administrators

```bash
# 1. Install dependencies
sudo apt install postgresql-client-16 redis-server

# 2. Start Redis
sudo systemctl start redis-server

# 3. Install Python packages
pip install -r requirements.txt

# 4. Setup services (see SYSTEMD_SERVICE_FILES.md)

# 5. Start background jobs
sudo systemctl start protech-celery-worker protech-celery-beat
```

### For Admin Users

1. Login to admin panel
2. Go to **System Settings**
3. Scroll to **Backup & Recovery**
4. Click **Download Backup** button

---

## 📋 Documentation Index

| Document | Purpose | Audience |
|----------|---------|----------|
| **[BACKUP_IMPLEMENTATION_SUMMARY.md](BACKUP_IMPLEMENTATION_SUMMARY.md)** | Complete feature summary | Everyone |
| **[DATABASE_BACKUP_DEPLOYMENT.md](DATABASE_BACKUP_DEPLOYMENT.md)** | Full deployment guide | Sys Admins |
| **[BACKUP_QUICK_COMMANDS.md](BACKUP_QUICK_COMMANDS.md)** | Command reference | Sys Admins |
| **[SYSTEMD_SERVICE_FILES.md](SYSTEMD_SERVICE_FILES.md)** | Service configuration | Sys Admins |
| **[INSTALLATION_CHECKLIST.md](INSTALLATION_CHECKLIST.md)** | Step-by-step checklist | Sys Admins |
| **[BACKUP_UI_GUIDE.md](BACKUP_UI_GUIDE.md)** | User interface guide | Admin Users |
| **[BACKUP_SYSTEM_ARCHITECTURE.md](BACKUP_SYSTEM_ARCHITECTURE.md)** | System architecture | Developers |

---

## 🎯 Use Cases

### Manual Backup
**When to use:**
- Before major system updates
- Before data migrations
- For immediate backup needs
- To download backup locally

**How:**
1. Click "Download Backup" button
2. File downloads automatically
3. Save to secure location

### Automatic Backup
**When to use:**
- Daily disaster recovery protection
- Compliance requirements
- Hands-off backup strategy

**How:**
- Runs automatically at 00:00 Manila Time
- No manual intervention needed
- Backups stored on server

---

## 🏗️ System Architecture

```
┌──────────────┐
│  Admin User  │ ──► Manual Backup
└──────────────┘      (Download Button)
                              │
                              ▼
                    ┌─────────────────┐
                    │  Django Views   │
                    └─────────────────┘
                              │
┌──────────────┐              │
│ Celery Beat  │ ──► Automatic Backup
│  (Schedule)  │     (00:00 Manila)
└──────────────┘              │
        │                     │
        ▼                     ▼
┌──────────────┐    ┌─────────────────┐
│Celery Worker │ ───│ Backup Utils    │
└──────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   (pg_dump)     │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │database backup/ │
                    │  *.sql files    │
                    └─────────────────┘
```

---

## ⚙️ Configuration

### Environment Variables (.env)
```env
# Database
DB_NAME=PROTECH
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Backup Schedule
- **Time**: 00:00 Asia/Manila (16:00 UTC)
- **Frequency**: Daily
- **Retention**: Last 30 backups
- **Location**: `database backup/` folder

---

## 🔧 Management

### Start Services
```bash
sudo systemctl start protech-celery-worker protech-celery-beat
```

### Stop Services
```bash
sudo systemctl stop protech-celery-worker protech-celery-beat
```

### Check Status
```bash
sudo systemctl status protech-celery-worker
sudo systemctl status protech-celery-beat
```

### View Logs
```bash
sudo journalctl -u protech-celery-worker -f
sudo journalctl -u protech-celery-beat -f
```

---

## 🧪 Testing

### Test Manual Backup
```bash
# Via web interface
Login → Settings → Click "Download Backup"

# Via command line
python manage.py shell -c "from PROTECHAPP.backup_utils import create_database_backup; print(create_database_backup())"
```

### Test Automatic Backup
```bash
python manage.py shell -c "from PROTECHAPP.tasks import perform_daily_backup; print(perform_daily_backup.delay().get())"
```

### Check Backup Files
```bash
ls -lh "database backup/"
```

---

## 📊 Monitoring

### What to Monitor
- ✅ Services running (worker, beat, redis)
- ✅ Daily backup created successfully
- ✅ Backup file sizes reasonable
- ✅ Disk space availability
- ✅ Error logs empty

### Monitoring Commands
```bash
# Service health
sudo systemctl is-active protech-celery-worker
sudo systemctl is-active protech-celery-beat
redis-cli ping

# Backup files
ls -lt "database backup/" | head -5
du -sh "database backup/"

# Logs
sudo journalctl -u protech-celery-worker -n 20 --no-pager
sudo journalctl -u protech-celery-beat -n 20 --no-pager
```

---

## 🔐 Security

### Best Practices
1. **Restrict backup folder permissions**: `chmod 700 "database backup"`
2. **Secure .env file**: Never commit to git
3. **Redis security**: Configure password if networked
4. **Regular testing**: Test restore procedure monthly
5. **Offsite backups**: Store critical backups externally

### File Permissions
```bash
# Backup directory
chmod 755 "database backup"  # or 700 for stricter

# Service files
chmod 644 /etc/systemd/system/protech-celery-*.service

# Log directories
chmod 755 /var/log/celery
chmod 755 /var/run/celery
```

---

## 🆘 Troubleshooting

### Common Issues

#### Services won't start
```bash
# Check logs
sudo journalctl -xe
sudo systemctl status protech-celery-worker -l

# Verify paths in service files
cat /etc/systemd/system/protech-celery-worker.service
```

#### Backups fail
```bash
# Check pg_dump installed
which pg_dump
pg_dump --version

# Test database connection
python manage.py dbshell

# Check permissions
ls -ld "database backup"
```

#### Redis connection error
```bash
# Start Redis
sudo systemctl start redis-server

# Test connection
redis-cli ping

# Check status
sudo systemctl status redis-server
```

---

## 📦 Requirements

### System Requirements
- Ubuntu 24.04 (or similar Linux)
- Python 3.8+
- PostgreSQL 12+
- Redis 5+

### Python Packages
```
celery==5.4.0
redis==5.2.1
Django==5.2.6
psycopg2-binary==2.9.10
```

---

## 🔄 Restore Procedure

### Basic Restore
```bash
# 1. Stop Django
sudo systemctl stop gunicorn

# 2. Restore database
psql -U postgres -d PROTECH < "database backup/protech_backup_YYYYMMDD_HHMMSS.sql"

# 3. Verify
python manage.py check

# 4. Start Django
sudo systemctl start gunicorn
```

**⚠️ Warning**: Restoring will overwrite current data. Always test in staging first.

---

## 📈 Performance

### Backup Times
- Small database (<100MB): 5-10 seconds
- Medium database (100-500MB): 10-30 seconds
- Large database (>500MB): 30-60+ seconds

### Disk Space
- Each backup ≈ current database size
- 30 backups ≈ 30x database size
- Monitor with: `du -sh "database backup"`

---

## 🎓 Training Resources

### For Administrators
1. Read **DATABASE_BACKUP_DEPLOYMENT.md**
2. Follow **INSTALLATION_CHECKLIST.md**
3. Practice restore procedure
4. Set up monitoring

### For Users
1. Read **BACKUP_UI_GUIDE.md**
2. Practice manual backup
3. Know when to escalate issues

---

## 🚧 Maintenance

### Daily
- Verify backup created
- Check service status
- Review error logs

### Weekly
- Check disk space
- Verify old backups cleaned
- Review backup sizes

### Monthly
- Test restore procedure
- Review performance metrics
- Update documentation

---

## 🤝 Support

### Getting Help

1. **Check logs first**
   ```bash
   sudo journalctl -u protech-celery-worker -n 50
   sudo journalctl -u protech-celery-beat -n 50
   ```

2. **Verify services**
   ```bash
   sudo systemctl status protech-celery-worker
   sudo systemctl status protech-celery-beat
   redis-cli ping
   ```

3. **Test components**
   ```bash
   python manage.py shell
   ```

4. **Review documentation**
   - Check relevant .md files
   - Follow troubleshooting guides

---

## 📝 Change Log

### Version 1.0.0 (December 2025)
- ✅ Initial implementation
- ✅ Manual backup via UI
- ✅ Automatic daily backups
- ✅ systemd integration
- ✅ Comprehensive documentation

---

## 🎉 Success Criteria

Your system is working correctly when:

✅ Manual backup downloads successfully  
✅ Automatic backup runs at midnight  
✅ New backups appear daily  
✅ Old backups are cleaned up  
✅ Services auto-start on reboot  
✅ No errors in logs  
✅ UI shows backup list  
✅ Disk space is sufficient  

---

## 📞 Quick Reference

```bash
# START
sudo systemctl start protech-celery-worker protech-celery-beat

# STOP
sudo systemctl stop protech-celery-worker protech-celery-beat

# STATUS
sudo systemctl status protech-celery-worker
sudo systemctl status protech-celery-beat

# LOGS
sudo journalctl -u protech-celery-worker -f
sudo journalctl -u protech-celery-beat -f

# TEST
python manage.py shell -c "from PROTECHAPP.tasks import perform_daily_backup; print(perform_daily_backup.delay().get())"

# FILES
ls -lh "database backup/"
```

---

## 🌟 Features at a Glance

| Feature | Status | Notes |
|---------|--------|-------|
| Manual Backup | ✅ Ready | One-click download |
| Auto Backup | ✅ Ready | 00:00 Manila daily |
| Retention | ✅ Ready | Keep last 30 |
| UI Integration | ✅ Ready | Admin settings page |
| systemd Services | ✅ Ready | Production grade |
| Error Handling | ✅ Ready | Comprehensive |
| Logging | ✅ Ready | Full audit trail |
| Documentation | ✅ Ready | 7 detailed guides |

---

**🎯 Ready to Deploy!**

This system is fully functional and production-ready. Follow the documentation to get started.

**Questions?** Check the documentation files listed at the top of this README.
