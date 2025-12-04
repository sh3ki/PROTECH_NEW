# Database Backup System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PROTECH BACKUP SYSTEM                        │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐        ┌──────────────────────┐
│   ADMIN USER (WEB)   │        │   BACKGROUND JOBS    │
└──────────────────────┘        └──────────────────────┘
          │                               │
          │                               │
          ▼                               ▼
┌─────────────────────┐         ┌──────────────────────┐
│  Manual Backup      │         │  Celery Beat         │
│  Button Click       │         │  (Scheduler)         │
└─────────────────────┘         └──────────────────────┘
          │                               │
          │                               │ Schedule:
          │ Direct Call                   │ 16:00 UTC Daily
          │                               │ (00:00 Manila)
          ▼                               ▼
┌──────────────────────────────────────────────────────┐
│           backup_utils.py Functions                  │
│  • create_database_backup()                          │
│  • cleanup_old_backups()                             │
│  • get_backup_list()                                 │
└──────────────────────────────────────────────────────┘
                      │
                      │ Calls pg_dump
                      ▼
         ┌───────────────────────┐
         │   PostgreSQL Server   │
         │   (Database)          │
         └───────────────────────┘
                      │
                      │ Exports data
                      ▼
         ┌───────────────────────┐
         │  database backup/     │
         │  • protech_backup_    │
         │    20251201_000012.sql│
         │  • protech_backup_    │
         │    20251130_235945.sql│
         │  • ... (30 files max) │
         └───────────────────────┘
```

---

## Component Breakdown

### 1. User Interface Layer
```
┌────────────────────────────────────────┐
│        Admin Settings Page             │
│  ┌──────────────────────────────────┐ │
│  │   Backup & Recovery Section      │ │
│  │                                  │ │
│  │  [Download Backup Button]        │ │
│  │                                  │ │
│  │  Automatic Backup Info Box       │ │
│  │  (00:00 Manila Time)             │ │
│  │                                  │ │
│  │  Recent Backups List             │ │
│  │  • protech_backup_...sql         │ │
│  │  • protech_backup_...sql         │ │
│  └──────────────────────────────────┘ │
└────────────────────────────────────────┘
           │
           │ HTTP Request
           ▼
┌────────────────────────────────────────┐
│        Django Views                    │
│  • download_database_backup()          │
│  • get_backup_status()                 │
└────────────────────────────────────────┘
```

### 2. Background Task Layer
```
┌─────────────────────────────────────────┐
│           Celery Workers                │
│                                         │
│  ┌────────────────────────────────┐   │
│  │  Celery Beat (Scheduler)       │   │
│  │  • Checks schedule every minute│   │
│  │  • Triggers at 16:00 UTC       │   │
│  └────────────────────────────────┘   │
│                │                        │
│                │ Sends Task             │
│                ▼                        │
│  ┌────────────────────────────────┐   │
│  │  Celery Worker (Executor)      │   │
│  │  • Receives tasks from queue   │   │
│  │  • Runs perform_daily_backup() │   │
│  └────────────────────────────────┘   │
└─────────────────────────────────────────┘
                │
                │ via Redis
                ▼
┌─────────────────────────────────────────┐
│           Redis Server                  │
│  • Message Broker (queue)               │
│  • Result Backend (task results)        │
└─────────────────────────────────────────┘
```

### 3. Database Backup Layer
```
┌─────────────────────────────────────────┐
│       Backup Utilities Module           │
│       (PROTECHAPP/backup_utils.py)      │
│                                         │
│  create_database_backup()               │
│    ├─ Get DB credentials                │
│    ├─ Generate filename with timestamp  │
│    ├─ Call pg_dump command              │
│    └─ Return success/error              │
│                                         │
│  cleanup_old_backups()                  │
│    ├─ List all backup files             │
│    ├─ Sort by date (oldest first)       │
│    └─ Delete files beyond 30            │
│                                         │
│  get_backup_list()                      │
│    ├─ Scan backup directory             │
│    ├─ Get file metadata                 │
│    └─ Return list with details          │
└─────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### Manual Backup Flow
```
User clicks        Django View         Backup Utils       PostgreSQL
"Download"          receives           creates backup      dumps data
  │                 request            │                   │
  ├────────────────►│                  │                   │
  │                 ├─────────────────►│                   │
  │                 │                  ├──────────────────►│
  │                 │                  │◄──────────────────┤
  │                 │                  │  (SQL file)        │
  │                 │◄─────────────────┤                   │
  │◄────────────────┤                  │                   │
  │  (File download)                   │                   │
  │                                    │                   │
  ▼                                    ▼                   ▼
Browser           HTTP Response      Temp file         Data exported
Downloads         with file          created           as SQL
```

### Automatic Backup Flow
```
Time: 16:00 UTC    Celery Beat       Celery Worker     Backup Utils
(00:00 Manila)     checks schedule   executes task     creates backup
  │                │                 │                 │
  ├───────────────►│                 │                 │
  │                ├────────────────►│                 │
  │                │   Send task     │                 │
  │                │   to queue      ├────────────────►│
  │                │                 │                 │
  │                │                 │◄────────────────┤
  │                │                 │  Success/Error   │
  │                │◄────────────────┤                 │
  │                │   Task complete │                 │
  ▼                ▼                 ▼                 ▼
Next day          Schedule           Result stored    File saved in
same time         advances           in Redis         "database backup/"
```

---

## File Structure

```
PROTECH_NEW/
│
├── PROTECH/
│   ├── __init__.py           ← Loads Celery app
│   ├── settings.py           ← Celery config
│   ├── celery.py             ← Celery app & schedule
│   └── wsgi.py
│
├── PROTECHAPP/
│   ├── backup_utils.py       ← NEW: Backup functions
│   ├── tasks.py              ← NEW: Celery tasks
│   ├── views/
│   │   └── admin_views.py    ← Modified: Added backup views
│   └── urls.py               ← Modified: Added backup routes
│
├── templates/
│   └── admin/
│       └── settings.html     ← Modified: Added backup UI
│
├── database backup/          ← NEW: Backup storage folder
│   ├── protech_backup_20251201_000012.sql
│   ├── protech_backup_20251130_235945.sql
│   └── ... (up to 30 files)
│
├── requirements.txt          ← Modified: Added Celery/Redis
├── .env                      ← Modified: Added Celery config
│
└── Documentation/
    ├── BACKUP_IMPLEMENTATION_SUMMARY.md
    ├── DATABASE_BACKUP_DEPLOYMENT.md
    ├── BACKUP_QUICK_COMMANDS.md
    ├── SYSTEMD_SERVICE_FILES.md
    ├── BACKUP_UI_GUIDE.md
    └── INSTALLATION_CHECKLIST.md
```

---

## Process Architecture

### Services Running on Server
```
┌─────────────────────────────────────────────────────┐
│                   Ubuntu Server                      │
│                                                      │
│  ┌────────────────────┐  ┌────────────────────┐   │
│  │   PostgreSQL       │  │   Redis Server     │   │
│  │   Port: 5432       │  │   Port: 6379       │   │
│  └────────────────────┘  └────────────────────┘   │
│                                                      │
│  ┌────────────────────┐  ┌────────────────────┐   │
│  │   Django/Gunicorn  │  │   Celery Worker    │   │
│  │   Port: 8000       │  │   Background       │   │
│  └────────────────────┘  └────────────────────┘   │
│                                                      │
│  ┌────────────────────┐                            │
│  │   Celery Beat      │                            │
│  │   Scheduler        │                            │
│  └────────────────────┘                            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Timing Diagram

### Daily Backup Execution Timeline
```
Time (UTC)       15:30   15:45   16:00   16:05   16:10
Time (Manila)    23:30   23:45   00:00   00:05   00:10
                   │       │       │       │       │
                   │       │       │       │       │
Celery Beat      Check   Check  TRIGGER Check   Check
                 (no)    (no)    (YES!)  (no)    (no)
                                   │
                                   ├─► Task sent to queue
                                   │
Celery Worker                      │
                                   ├─► Pick up task
                                   ├─► Run backup
                                   ├─► Cleanup old files
                                   └─► Report success
                                   
Backup File                        │
                                   └─► protech_backup_
                                       20251201_000012.sql
                                       created
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Security Layers                   │
│                                                      │
│  1. Web Interface                                   │
│     ├─ Login Required (Admin only)                  │
│     ├─ CSRF Protection                              │
│     └─ User Permission Check                        │
│                                                      │
│  2. File System                                     │
│     ├─ Backup folder permissions (755/700)          │
│     ├─ Files outside web root                       │
│     └─ No direct web access                         │
│                                                      │
│  3. Database                                        │
│     ├─ Credentials in .env (not in git)             │
│     ├─ PostgreSQL authentication                    │
│     └─ Network security                             │
│                                                      │
│  4. Background Services                             │
│     ├─ Run as specific user (not root)              │
│     ├─ systemd security features                    │
│     └─ Log file permissions                         │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Scalability Considerations

```
Current Setup (Single Server)
┌─────────────────────┐
│   Server            │
│  ├─ Django          │
│  ├─ PostgreSQL      │
│  ├─ Redis           │
│  ├─ Celery Worker   │
│  └─ Celery Beat     │
└─────────────────────┘

Future Scaling Options
┌─────────────────────┐  ┌─────────────────────┐
│   Web Server        │  │   Database Server   │
│  ├─ Django          │  │  └─ PostgreSQL      │
│  └─ Nginx           │  └─────────────────────┘
└─────────────────────┘           │
        │                          │
        │                          │
┌─────────────────────┐  ┌─────────────────────┐
│   Redis Server      │  │   Worker Servers    │
│  └─ Message Queue   │  │  ├─ Celery Worker 1 │
└─────────────────────┘  │  ├─ Celery Worker 2 │
        │                │  └─ Celery Beat     │
        └────────────────┴─────────────────────┘
```

---

## Monitoring Points

```
┌────────────────────────────────────────────┐
│           What to Monitor                  │
├────────────────────────────────────────────┤
│  1. Services Status                        │
│     • Redis running?                       │
│     • Celery worker active?                │
│     • Celery beat scheduling?              │
│                                            │
│  2. Backup Operations                      │
│     • Daily backup completed?              │
│     • Backup file size reasonable?         │
│     • Old files cleaned up?                │
│                                            │
│  3. System Resources                       │
│     • Disk space for backups               │
│     • Memory usage                         │
│     • CPU usage during backup              │
│                                            │
│  4. Errors & Logs                          │
│     • Celery worker errors                 │
│     • Beat scheduler errors                │
│     • Backup operation failures            │
│                                            │
│  5. Performance                            │
│     • Backup creation time                 │
│     • Download speed                       │
│     • Queue processing time                │
└────────────────────────────────────────────┘
```

---

## Disaster Recovery Workflow

```
┌─────────────────────────────────────────────────────┐
│              Disaster Recovery Steps                 │
│                                                      │
│  1. Identify Issue                                  │
│     └─ Data loss, corruption, or system failure     │
│                                                      │
│  2. Select Backup                                   │
│     ├─ List backups in "database backup" folder     │
│     └─ Choose appropriate timestamp                 │
│                                                      │
│  3. Prepare System                                  │
│     ├─ Stop Django application                      │
│     └─ Ensure PostgreSQL is running                 │
│                                                      │
│  4. Restore Database                                │
│     ├─ Drop existing database (if needed)           │
│     ├─ Create new database                          │
│     └─ psql -U user -d db < backup_file.sql         │
│                                                      │
│  5. Verify Restoration                              │
│     ├─ Check tables exist                           │
│     ├─ Verify data integrity                        │
│     └─ Test application functionality               │
│                                                      │
│  6. Resume Operations                               │
│     └─ Restart Django application                   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

This architecture provides a robust, scalable, and maintainable solution for automated database backups with manual override capabilities.
