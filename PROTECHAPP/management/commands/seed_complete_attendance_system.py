from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from PROTECHAPP.models import Student, Attendance, ExcusedAbsence, Guardian
import datetime

class Command(BaseCommand):
    help = 'Complete attendance and excused absence seeding with realistic data'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=60, help='Number of school days to generate')
        parser.add_argument('--start-date', type=str, help='Start date in YYYY-MM-DD format')
        parser.add_argument('--clear-all', action='store_true', help='Clear all existing data before seeding')
        parser.add_argument('--skip-attendance', action='store_true', help='Skip attendance seeding')
        parser.add_argument('--skip-excuses', action='store_true', help='Skip excused absence seeding')
        parser.add_argument('--create-notifications', action='store_true', help='Create notifications for attendance issues')
        parser.add_argument('--create-letters', action='store_true', help='Create excuse letter references')
        parser.add_argument('--verbose', action='store_true', help='Show detailed progress')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🏫 PROTECH ATTENDANCE & EXCUSED ABSENCE COMPREHENSIVE SEEDER'))
        self.stdout.write('=' * 70)
        
        verbose = options['verbose']
        
        # Pre-seeding validation
        student_count = Student.objects.filter(status='ACTIVE').count()
        guardian_count = Guardian.objects.count()
        
        if student_count == 0:
            self.stdout.write(self.style.ERROR('❌ No active students found. Please run student seeders first.'))
            return
        
        self.stdout.write(f'👥 Found {student_count} active students')
        if guardian_count > 0:
            self.stdout.write(f'👨‍👩‍👧‍👦 Found {guardian_count} guardians')
        
        # Clear existing data if requested
        if options['clear_all']:
            self.stdout.write(self.style.WARNING('\n🧹 CLEARING EXISTING DATA...'))
            
            excused_count = ExcusedAbsence.objects.count()
            attendance_count = Attendance.objects.count()
            
            if excused_count > 0:
                ExcusedAbsence.objects.all().delete()
                self.stdout.write(f'  ✓ Cleared {excused_count} excused absence records')
            
            if attendance_count > 0:
                Attendance.objects.all().delete()
                self.stdout.write(f'  ✓ Cleared {attendance_count} attendance records')
        
        # Prepare arguments for sub-commands
        attendance_args = ['--days', str(options['days'])]
        if options['start_date']:
            attendance_args.extend(['--start-date', options['start_date']])
        if options['create_notifications']:
            attendance_args.append('--create-notifications')
        if verbose:
            attendance_args.append('--verbose')
        
        excuse_args = []
        if options['create_letters']:
            excuse_args.append('--create-letters')
        if verbose:
            excuse_args.append('--verbose')
        excuse_args.append('--generate-additional')  # Always generate additional for comprehensive data
        
        # Step 1: Generate Attendance Records
        if not options['skip_attendance']:
            self.stdout.write(f'\n📊 STEP 1: GENERATING ATTENDANCE RECORDS')
            self.stdout.write('-' * 50)
            
            try:
                call_command('seed_realistic_attendance', *attendance_args)
                attendance_created = Attendance.objects.count()
                self.stdout.write(self.style.SUCCESS(f'✅ Attendance seeding completed: {attendance_created} records'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Attendance seeding failed: {str(e)}'))
                return
        else:
            self.stdout.write(f'\n⏭️  STEP 1: SKIPPED - Attendance seeding')
        
        # Step 2: Generate Excused Absence Records
        if not options['skip_excuses']:
            self.stdout.write(f'\n🏥 STEP 2: GENERATING EXCUSED ABSENCE RECORDS')
            self.stdout.write('-' * 50)
            
            try:
                call_command('seed_realistic_excused_absences', *excuse_args)
                excused_created = ExcusedAbsence.objects.count()
                self.stdout.write(self.style.SUCCESS(f'✅ Excused absence seeding completed: {excused_created} records'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Excused absence seeding failed: {str(e)}'))
                return
        else:
            self.stdout.write(f'\n⏭️  STEP 2: SKIPPED - Excused absence seeding')
        
        # Final Summary and Verification
        self.stdout.write(f'\n📈 FINAL SUMMARY & VERIFICATION')
        self.stdout.write('=' * 50)
        
        # Get final counts
        final_students = Student.objects.filter(status='ACTIVE').count()
        final_attendance = Attendance.objects.count()
        final_excused = ExcusedAbsence.objects.count()
        final_guardians = Guardian.objects.count()
        
        self.stdout.write(f'👥 Active Students: {final_students:,}')
        self.stdout.write(f'📊 Attendance Records: {final_attendance:,}')
        self.stdout.write(f'🏥 Excused Absences: {final_excused:,}')
        self.stdout.write(f'👨‍👩‍👧‍👦 Guardians: {final_guardians:,}')
        
        # Attendance status breakdown
        if final_attendance > 0:
            on_time = Attendance.objects.filter(status='ON TIME').count()
            late = Attendance.objects.filter(status='LATE').count()
            absent = Attendance.objects.filter(status='ABSENT').count()
            excused = Attendance.objects.filter(status='EXCUSED').count()
            
            self.stdout.write(f'\n📊 Attendance Breakdown:')
            self.stdout.write(f'   ✅ On Time: {on_time:,} ({on_time/final_attendance*100:.1f}%)')
            self.stdout.write(f'   ⏰ Late: {late:,} ({late/final_attendance*100:.1f}%)')
            self.stdout.write(f'   ❌ Absent: {absent:,} ({absent/final_attendance*100:.1f}%)')
            self.stdout.write(f'   🏥 Excused: {excused:,} ({excused/final_attendance*100:.1f}%)')
        
        # Date range information
        if final_attendance > 0:
            earliest_date = Attendance.objects.order_by('date').first().date
            latest_date = Attendance.objects.order_by('-date').first().date
            self.stdout.write(f'\n📅 Date Range: {earliest_date} to {latest_date}')
            
            # Count school days
            total_days = (latest_date - earliest_date).days + 1
            school_days = sum(1 for i in range(total_days) 
                            if (earliest_date + datetime.timedelta(days=i)).weekday() < 5)
            self.stdout.write(f'🏫 School Days: {school_days} (excluding weekends)')
        
        # Data integrity checks
        self.stdout.write(f'\n🔍 DATA INTEGRITY CHECKS:')
        
        # Check for excused absences without attendance records
        orphaned_excuses = ExcusedAbsence.objects.exclude(
            student__attendance_records__date=ExcusedAbsence.objects.values('date_absent')[0]['date_absent']
        ).count() if final_excused > 0 else 0
        
        # Check for duplicate attendance records
        from django.db.models import Count
        duplicate_attendance = Attendance.objects.values('student', 'date').annotate(
            count=Count('id')
        ).filter(count__gt=1).count()
        
        if duplicate_attendance == 0:
            self.stdout.write('   ✅ No duplicate attendance records')
        else:
            self.stdout.write(f'   ⚠️  Found {duplicate_attendance} duplicate attendance records')
        
        # Check student-guardian relationships
        students_with_guardians = Student.objects.filter(guardians__isnull=False).distinct().count()
        self.stdout.write(f'   👨‍👩‍👧‍👦 Students with Guardians: {students_with_guardians}/{final_students} ({students_with_guardians/final_students*100:.1f}%)')
        
        # Sample data preview
        if verbose and final_attendance > 0:
            self.stdout.write(f'\n📋 SAMPLE RECENT ATTENDANCE RECORDS:')
            recent_records = Attendance.objects.select_related('student', 'student__grade', 'student__section').order_by('-date', '-created_at')[:10]
            
            for record in recent_records:
                time_display = f"{record.time_in.strftime('%I:%M %p')}" if record.time_in else "N/A"
                self.stdout.write(
                    f'   {record.date} | {record.student.first_name} {record.student.last_name} '
                    f'({record.student.grade.name}-{record.student.section.name}) | '
                    f'{record.get_status_display()} | Time In: {time_display}'
                )
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 COMPREHENSIVE SEEDING COMPLETED SUCCESSFULLY!'))
        self.stdout.write('=' * 70)
        self.stdout.write('💡 Usage Tips:')
        self.stdout.write('   • Use Django Admin to explore the generated data')
        self.stdout.write('   • Check attendance reports in the PROTECH system')
        self.stdout.write('   • Verify guardian notifications are working')
        self.stdout.write('   • Review excused absence letters in media/private_excuse_letters/')
        self.stdout.write('')