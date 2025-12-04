"""
Celery configuration for PROTECH
"""
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')

app = Celery('PROTECH')

# Load config from Django settings, using the CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


# Configure periodic tasks
app.conf.beat_schedule = {
    'daily-database-backup': {
        'task': 'PROTECHAPP.tasks.perform_daily_backup',
        'schedule': crontab(hour=16, minute=0),  # 16:00 UTC = 00:00 Manila Time
    },
}

# Set timezone for beat scheduler
app.conf.timezone = 'UTC'


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')
