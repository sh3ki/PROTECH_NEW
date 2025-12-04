# Systemd Service Files for PROTECH Database Backup

## Copy these files to `/etc/systemd/system/` on your Ubuntu server

---

## File 1: `/etc/systemd/system/protech-celery-worker.service`

```ini
[Unit]
Description=PROTECH Celery Worker
After=network.target redis-server.service postgresql.service

[Service]
Type=forking
User=YOUR_USERNAME
Group=YOUR_USERNAME
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

---

## File 2: `/etc/systemd/system/protech-celery-beat.service`

```ini
[Unit]
Description=PROTECH Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/path/to/PROTECH_NEW
Environment="PATH=/path/to/PROTECH_NEW/venv/bin"
ExecStart=/path/to/PROTECH_NEW/venv/bin/celery -A PROTECH beat \
    --logfile=/var/log/celery/beat.log \
    --pidfile=/var/run/celery/beat.pid \
    --loglevel=info

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Installation Steps

### 1. Replace Placeholders
Replace these in both files:
- `YOUR_USERNAME` → Your Ubuntu username
- `/path/to/PROTECH_NEW` → Full path to your project

Example:
```ini
User=protech_admin
Group=protech_admin
WorkingDirectory=/home/protech_admin/PROTECH_NEW
Environment="PATH=/home/protech_admin/PROTECH_NEW/venv/bin"
ExecStart=/home/protech_admin/PROTECH_NEW/venv/bin/celery ...
```

### 2. Create Directories

```bash
# Create log directory
sudo mkdir -p /var/log/celery
sudo chown YOUR_USERNAME:YOUR_USERNAME /var/log/celery

# Create PID directory
sudo mkdir -p /var/run/celery
sudo chown YOUR_USERNAME:YOUR_USERNAME /var/run/celery
```

### 3. Copy Service Files

```bash
# Copy worker service
sudo nano /etc/systemd/system/protech-celery-worker.service
# Paste the worker service content (with your paths)

# Copy beat service
sudo nano /etc/systemd/system/protech-celery-beat.service
# Paste the beat service content (with your paths)
```

### 4. Set Permissions

```bash
sudo chmod 644 /etc/systemd/system/protech-celery-worker.service
sudo chmod 644 /etc/systemd/system/protech-celery-beat.service
```

### 5. Reload and Enable

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable protech-celery-worker
sudo systemctl enable protech-celery-beat

# Start services
sudo systemctl start protech-celery-worker
sudo systemctl start protech-celery-beat
```

### 6. Verify

```bash
# Check status
sudo systemctl status protech-celery-worker
sudo systemctl status protech-celery-beat

# Check logs
sudo journalctl -u protech-celery-worker -n 20
sudo journalctl -u protech-celery-beat -n 20
```

---

## Alternative: Simple Script Installation

Create a file `install_services.sh`:

```bash
#!/bin/bash

# Configuration - CHANGE THESE
USERNAME="your_username"
PROJECT_PATH="/path/to/PROTECH_NEW"
VENV_PATH="$PROJECT_PATH/venv"

# Create directories
echo "Creating directories..."
sudo mkdir -p /var/log/celery
sudo mkdir -p /var/run/celery
sudo chown $USERNAME:$USERNAME /var/log/celery
sudo chown $USERNAME:$USERNAME /var/run/celery

# Create worker service
echo "Creating worker service..."
sudo tee /etc/systemd/system/protech-celery-worker.service > /dev/null <<EOF
[Unit]
Description=PROTECH Celery Worker
After=network.target redis-server.service postgresql.service

[Service]
Type=forking
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$PROJECT_PATH
Environment="PATH=$VENV_PATH/bin"
ExecStart=$VENV_PATH/bin/celery -A PROTECH worker \\
    --detach \\
    --logfile=/var/log/celery/worker.log \\
    --pidfile=/var/run/celery/worker.pid \\
    --loglevel=info

ExecStop=$VENV_PATH/bin/celery -A PROTECH control shutdown
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create beat service
echo "Creating beat service..."
sudo tee /etc/systemd/system/protech-celery-beat.service > /dev/null <<EOF
[Unit]
Description=PROTECH Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$PROJECT_PATH
Environment="PATH=$VENV_PATH/bin"
ExecStart=$VENV_PATH/bin/celery -A PROTECH beat \\
    --logfile=/var/log/celery/beat.log \\
    --pidfile=/var/run/celery/beat.pid \\
    --loglevel=info

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload and enable
echo "Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable protech-celery-worker
sudo systemctl enable protech-celery-beat

# Start services
echo "Starting services..."
sudo systemctl start protech-celery-worker
sudo systemctl start protech-celery-beat

# Show status
echo "Services status:"
sudo systemctl status protech-celery-worker --no-pager
sudo systemctl status protech-celery-beat --no-pager

echo "Done! Services are running."
```

Make it executable and run:
```bash
chmod +x install_services.sh
./install_services.sh
```

---

## Uninstall Services

If you need to remove the services:

```bash
# Stop services
sudo systemctl stop protech-celery-worker
sudo systemctl stop protech-celery-beat

# Disable services
sudo systemctl disable protech-celery-worker
sudo systemctl disable protech-celery-beat

# Remove service files
sudo rm /etc/systemd/system/protech-celery-worker.service
sudo rm /etc/systemd/system/protech-celery-beat.service

# Reload systemd
sudo systemctl daemon-reload
```

---

## Quick Commands After Installation

```bash
# Start
sudo systemctl start protech-celery-worker protech-celery-beat

# Stop
sudo systemctl stop protech-celery-worker protech-celery-beat

# Restart
sudo systemctl restart protech-celery-worker protech-celery-beat

# Status
sudo systemctl status protech-celery-worker
sudo systemctl status protech-celery-beat

# Logs
sudo journalctl -u protech-celery-worker -f
sudo journalctl -u protech-celery-beat -f
```
