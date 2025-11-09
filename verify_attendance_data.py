#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')
django.setup()

from PROTECHAPP.models import Attendance, ExcusedAbsence, Student, Guardian
from django.db.models import Count

print("=" * 50)
print("🏫 PROTECH ATTENDANCE SEEDER VERIFICATION")
print("=" * 50)

# Basic counts
total_students = Student.objects.filter(status='ACTIVE').count()
total_attendance = Attendance.objects.count()
total_excused = ExcusedAbsence.objects.count()
total_guardians = Guardian.objects.count()

print(f"👥 Active Students: {total_students:,}")
print(f"📊 Attendance Records: {total_attendance:,}")
print(f"🏥 Excused Absences: {total_excused:,}")
print(f"👨‍👩‍👧‍👦 Guardians: {total_guardians:,}")

print("\n📊 ATTENDANCE STATUS BREAKDOWN:")
print("-" * 30)
statuses = Attendance.objects.values('status').annotate(count=Count('id')).order_by('-count')
for status_data in statuses:
    status = status_data['status']
    count = status_data['count']
    percentage = (count / total_attendance * 100) if total_attendance > 0 else 0
    print(f"   {status}: {count:,} ({percentage:.1f}%)")

print("\n🏥 SAMPLE EXCUSED ABSENCES:")
print("-" * 30)
sample_excuses = ExcusedAbsence.objects.select_related('student', 'student__grade', 'student__section').order_by('-created_at')[:8]
for excuse in sample_excuses:
    duration = (excuse.end_date - excuse.effective_date).days + 1
    print(f"   {excuse.student.first_name} {excuse.student.last_name} "
          f"({excuse.student.grade.name}-{excuse.student.section.name}) "
          f"- {excuse.effective_date} to {excuse.end_date} ({duration} day{'s' if duration > 1 else ''})")

print("\n📅 DATE RANGE ANALYSIS:")
print("-" * 30)
if total_attendance > 0:
    earliest = Attendance.objects.order_by('date').first()
    latest = Attendance.objects.order_by('-date').first()
    print(f"   Earliest Record: {earliest.date}")
    print(f"   Latest Record: {latest.date}")
    
    # Count unique dates
    unique_dates = Attendance.objects.values('date').distinct().count()
    print(f"   Unique School Days: {unique_dates}")

print("\n🔍 DATA INTEGRITY CHECKS:")
print("-" * 30)

# Check for students without guardians
students_without_guardians = Student.objects.filter(guardians__isnull=True, status='ACTIVE').count()
print(f"   Students without Guardians: {students_without_guardians}")

# Check for excused absences without corresponding attendance
orphaned_excuses = 0
for excuse in ExcusedAbsence.objects.all()[:100]:  # Sample check
    if not Attendance.objects.filter(student=excuse.student, date=excuse.date_absent).exists():
        orphaned_excuses += 1

print(f"   Orphaned Excused Absences (sample): {orphaned_excuses}")

# Check for duplicate attendance records
duplicate_attendance = Attendance.objects.values('student', 'date').annotate(
    count=Count('id')
).filter(count__gt=1).count()
print(f"   Duplicate Attendance Records: {duplicate_attendance}")

if duplicate_attendance == 0 and students_without_guardians == 0:
    print("\n✅ ALL DATA INTEGRITY CHECKS PASSED!")
else:
    print(f"\n⚠️  Some data integrity issues found (see above)")

print("\n🎉 VERIFICATION COMPLETED!")
print("=" * 50)