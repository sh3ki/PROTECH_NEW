from django.core.management.base import BaseCommand
from django.utils import timezone
from PROTECHAPP.models import (
    Student, Attendance, ExcusedAbsence, Guardian, Notification, CustomUser, 
    AttendanceStatus, StudentStatus, NotificationType, NotificationStatus, NotificationCategory
)
import random
import datetime
from faker import Faker

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds realistic attendance data with 8AM-5PM schedule and proper relationships'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=60, help='Number of school days to generate')
        parser.add_argument('--start-date', type=str, help='Start date in YYYY-MM-DD format')
        parser.add_argument('--clear', action='store_true', help='Clear existing attendance records')
        parser.add_argument('--create-notifications', action='store_true', help='Create realistic notifications')
        parser.add_argument('--verbose', action='store_true', help='Show detailed progress')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing attendance records...'))
            Attendance.objects.all().delete()
            if options['verbose']:
                self.stdout.write('✓ Attendance records cleared')
        
        days = options['days']
        verbose = options['verbose']
        
        # Determine start date
        if options['start_date']:
            try:
                start_date = datetime.datetime.strptime(options['start_date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD'))
                return
        else:
            # Start from 2 months ago to have historical data
            start_date = (timezone.now() - datetime.timedelta(days=60)).date()
        
        # Ensure we don't go into the future
        today = timezone.now().date()
        if start_date > today:
            start_date = today - datetime.timedelta(days=days-1)
        
        self.stdout.write(f'🏫 Generating realistic attendance for {days} school days starting from {start_date}')
        
        # Get active students
        students = Student.objects.filter(status=StudentStatus.ACTIVE).select_related('grade', 'section')
        total_students = students.count()
        
        if total_students == 0:
            self.stdout.write(self.style.ERROR('❌ No active students found'))
            return
            
        self.stdout.write(f'👥 Found {total_students} active students')
        
        # Get users for notifications
        notification_users = []
        if options['create_notifications']:
            notification_users = list(CustomUser.objects.filter(is_active=True))
            if verbose and notification_users:
                self.stdout.write(f'📢 Found {len(notification_users)} users for notifications')
        
        # School time settings (8AM - 5PM as requested)
        SCHOOL_TIME_IN = datetime.time(8, 0)  # 8:00 AM
        SCHOOL_TIME_OUT = datetime.time(17, 0)  # 5:00 PM
        
        # Realistic attendance patterns
        ATTENDANCE_PATTERNS = {
            'excellent_student': {  # 5% of students - almost never absent
                'on_time': 0.85,
                'late': 0.12,
                'absent': 0.02,
                'excused': 0.01
            },
            'good_student': {  # 60% of students - normal attendance
                'on_time': 0.75,
                'late': 0.20,
                'absent': 0.04,
                'excused': 0.01
            },
            'average_student': {  # 30% of students - some issues
                'on_time': 0.65,
                'late': 0.25,
                'absent': 0.08,
                'excused': 0.02
            },
            'problem_student': {  # 5% of students - frequent issues
                'on_time': 0.50,
                'late': 0.30,
                'absent': 0.15,
                'excused': 0.05
            }
        }
        
        # Assign patterns to students
        student_patterns = {}
        student_list = list(students)
        random.shuffle(student_list)
        
        pattern_counts = {
            'excellent_student': int(total_students * 0.05),
            'good_student': int(total_students * 0.60),
            'average_student': int(total_students * 0.30),
            'problem_student': int(total_students * 0.05)
        }
        
        idx = 0
        for pattern, count in pattern_counts.items():
            for _ in range(count):
                if idx < len(student_list):
                    student_patterns[student_list[idx].id] = pattern
                    idx += 1
        
        # Fill remaining students with good_student pattern
        while idx < len(student_list):
            student_patterns[student_list[idx].id] = 'good_student'
            idx += 1
        
        if verbose:
            self.stdout.write(f'📊 Assigned attendance patterns: {pattern_counts}')
        
        # Generate school days (skip weekends)
        school_days = []
        current_date = start_date
        days_added = 0
        
        while days_added < days and current_date <= today:
            # Skip weekends (Monday=0, Sunday=6)
            if current_date.weekday() < 5:  # Monday to Friday
                school_days.append(current_date)
                days_added += 1
            current_date += datetime.timedelta(days=1)
        
        if verbose:
            self.stdout.write(f'📅 Generated {len(school_days)} school days (excluding weekends)')
        
        # Track statistics
        stats = {
            'total_records': 0,
            'on_time': 0,
            'late': 0,
            'absent': 0,
            'excused': 0,
            'notifications_sent': 0
        }
        
        # Generate attendance records
        for day_num, school_date in enumerate(school_days):
            if verbose and day_num % 10 == 0:
                self.stdout.write(f'  📝 Processing day {day_num + 1}/{len(school_days)}: {school_date}')
            
            # Seasonal factors (more absences during flu season, etc.)
            seasonal_factor = self._get_seasonal_factor(school_date)
            
            for student in students:
                # Skip if record exists
                if Attendance.objects.filter(student=student, date=school_date).exists():
                    continue
                
                # Get student's attendance pattern
                pattern = student_patterns.get(student.id, 'good_student')
                probabilities = ATTENDANCE_PATTERNS[pattern].copy()
                
                # Apply seasonal adjustments
                probabilities['absent'] *= seasonal_factor
                probabilities['excused'] *= seasonal_factor
                
                # Normalize probabilities
                total_prob = sum(probabilities.values())
                for key in probabilities:
                    probabilities[key] /= total_prob
                
                # Determine attendance status
                rand = random.random()
                cumulative = 0
                status = AttendanceStatus.ONTIME
                
                for att_status, prob in probabilities.items():
                    cumulative += prob
                    if rand <= cumulative:
                        if att_status == 'on_time':
                            status = AttendanceStatus.ONTIME
                        elif att_status == 'late':
                            status = AttendanceStatus.LATE
                        elif att_status == 'absent':
                            status = AttendanceStatus.ABSENT
                        elif att_status == 'excused':
                            status = AttendanceStatus.EXCUSED
                        break
                
                # Generate realistic times based on status
                time_in = None
                time_out = None
                sent_email = False
                sent_sms = False
                
                if status == AttendanceStatus.ONTIME:
                    # Arrive 0-10 minutes early to 5 minutes late
                    minutes_variance = random.randint(-10, 5)
                    time_in = (datetime.datetime.combine(datetime.date.today(), SCHOOL_TIME_IN) + 
                              datetime.timedelta(minutes=minutes_variance)).time()
                    time_out = SCHOOL_TIME_OUT
                    stats['on_time'] += 1
                    
                elif status == AttendanceStatus.LATE:
                    # Arrive 6-45 minutes late
                    minutes_late = random.randint(6, 45)
                    time_in = (datetime.datetime.combine(datetime.date.today(), SCHOOL_TIME_IN) + 
                              datetime.timedelta(minutes=minutes_late)).time()
                    time_out = SCHOOL_TIME_OUT
                    # Late students often get notifications
                    sent_email = random.random() < 0.7
                    sent_sms = random.random() < 0.4
                    stats['late'] += 1
                    
                elif status == AttendanceStatus.ABSENT:
                    # No times for absent students
                    time_in = None
                    time_out = None
                    # Absent students usually get notifications
                    sent_email = random.random() < 0.9
                    sent_sms = random.random() < 0.6
                    stats['absent'] += 1
                    
                elif status == AttendanceStatus.EXCUSED:
                    # No times for excused students
                    time_in = None
                    time_out = None
                    # Excused students get confirmation notifications
                    sent_email = random.random() < 0.8
                    sent_sms = random.random() < 0.3
                    stats['excused'] += 1
                
                # Create attendance record
                attendance = Attendance.objects.create(
                    student=student,
                    date=school_date,
                    time_in=time_in,
                    time_out=time_out,
                    status=status,
                    sent_email=sent_email,
                    sent_sms=sent_sms
                )
                stats['total_records'] += 1
                
                # Create notifications for problematic attendance
                if (options['create_notifications'] and notification_users and 
                    (status in [AttendanceStatus.LATE, AttendanceStatus.ABSENT])):
                    
                    # Don't create notifications for every instance
                    if random.random() < 0.3:  # 30% chance of notification
                        user = random.choice(notification_users)
                        
                        if status == AttendanceStatus.LATE:
                            message = f"Student {student.first_name} {student.last_name} ({student.grade.name} - {student.section.name}) arrived late at {time_in.strftime('%I:%M %p')} on {school_date.strftime('%B %d, %Y')}"
                        else:  # ABSENT
                            message = f"Student {student.first_name} {student.last_name} ({student.grade.name} - {student.section.name}) was absent on {school_date.strftime('%B %d, %Y')}"
                        
                        # Create notification with realistic timestamp
                        notification_time = timezone.make_aware(
                            datetime.datetime.combine(school_date, SCHOOL_TIME_IN) + 
                            datetime.timedelta(hours=random.randint(1, 3))
                        )
                        
                        Notification.objects.create(
                            user=user,
                            message=message,
                            type=NotificationType.SYSTEM,
                            status=NotificationStatus.SENT,
                            category=NotificationCategory.ATTENDANCE,
                            sent_at=notification_time
                        )
                        stats['notifications_sent'] += 1
        
        # Display results
        self.stdout.write(self.style.SUCCESS('\n✅ ATTENDANCE SEEDING COMPLETED'))
        self.stdout.write(f'📊 Statistics:')
        self.stdout.write(f'   Total Records: {stats["total_records"]:,}')
        self.stdout.write(f'   On Time: {stats["on_time"]:,} ({stats["on_time"]/stats["total_records"]*100:.1f}%)')
        self.stdout.write(f'   Late: {stats["late"]:,} ({stats["late"]/stats["total_records"]*100:.1f}%)')
        self.stdout.write(f'   Absent: {stats["absent"]:,} ({stats["absent"]/stats["total_records"]*100:.1f}%)')
        self.stdout.write(f'   Excused: {stats["excused"]:,} ({stats["excused"]/stats["total_records"]*100:.1f}%)')
        
        if options['create_notifications']:
            self.stdout.write(f'   Notifications Created: {stats["notifications_sent"]:,}')
        
        self.stdout.write(f'\n🏫 School Schedule: {SCHOOL_TIME_IN.strftime("%I:%M %p")} - {SCHOOL_TIME_OUT.strftime("%I:%M %p")}')
        self.stdout.write(f'📅 Date Range: {school_days[0]} to {school_days[-1]} ({len(school_days)} school days)')

    def _get_seasonal_factor(self, date):
        """Apply seasonal factors to attendance (flu season, etc.)"""
        month = date.month
        
        # Higher absence rates during flu season (Nov-Feb) and start of school year
        if month in [11, 12, 1, 2]:  # Flu season
            return 1.4
        elif month in [6, 7]:  # Start of school year adjustments
            return 1.2
        elif month in [3, 4]:  # End of school year fatigue
            return 1.1
        else:
            return 1.0