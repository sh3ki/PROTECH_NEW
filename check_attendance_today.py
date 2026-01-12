"""
Debug script to check today's attendance records
Run this to see which students have attendance for today
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')
django.setup()

from PROTECHAPP.models import Attendance, Student
from django.utils import timezone

today = timezone.now().date()

print(f"\n{'='*60}")
print(f"Checking attendance records for: {today}")
print(f"{'='*60}\n")

# Get all students in Grade 7 - Mabini
students = Student.objects.filter(section__name='Mabini', section__grade__name='Grade 7').order_by('last_name', 'first_name')

print(f"Total students in Grade 7 - Mabini: {students.count()}\n")

for student in students:
    attendance = Attendance.objects.filter(
        student=student,
        date=today,
        time_in__isnull=False
    ).first()
    
    if attendance:
        print(f"✅ {student.first_name} {student.last_name} - HAS attendance (Time in: {attendance.time_in})")
    else:
        print(f"❌ {student.first_name} {student.last_name} - NO attendance today")

print(f"\n{'='*60}")
print("Summary:")
has_attendance = Attendance.objects.filter(date=today, time_in__isnull=False, student__in=students).count()
print(f"Students with attendance: {has_attendance}")
print(f"Students without attendance: {students.count() - has_attendance}")
print(f"{'='*60}\n")
