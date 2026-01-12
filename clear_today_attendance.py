"""
Clear today's attendance records for testing
WARNING: This will delete today's attendance records!
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')
django.setup()

from PROTECHAPP.models import Attendance
from django.utils import timezone

today = timezone.now().date()

print(f"\n{'='*60}")
print(f"Deleting attendance records for: {today}")
print(f"{'='*60}\n")

records = Attendance.objects.filter(date=today)
count = records.count()

if count > 0:
    confirm = input(f"Found {count} attendance records for today. Delete them? (yes/no): ")
    if confirm.lower() == 'yes':
        records.delete()
        print(f"\n✅ Deleted {count} attendance records for {today}")
        print("Now all students should show with red outline!\n")
    else:
        print("\n❌ Cancelled. No records deleted.\n")
else:
    print(f"No attendance records found for {today}\n")

print(f"{'='*60}\n")
