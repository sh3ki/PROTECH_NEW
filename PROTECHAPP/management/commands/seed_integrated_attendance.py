from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from PROTECHAPP.models import (
    Student, Attendance, ExcusedAbsence, Guardian, CustomUser,
    AttendanceStatus, StudentStatus, NotificationType, NotificationStatus, 
    NotificationCategory, Notification
)
import random
import datetime
from faker import Faker

fake = Faker()

class Command(BaseCommand):
    help = 'Integrated attendance and excused absence seeder with realistic 8AM-5PM schedule (2 weeks ago to now)'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')
        parser.add_argument('--create-notifications', action='store_true', help='Create notifications for issues')
        parser.add_argument('--verbose', action='store_true', help='Show detailed progress')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('🧹 Clearing existing data...'))
            Attendance.objects.all().delete()
            ExcusedAbsence.objects.all().delete()
            self.stdout.write('✅ Data cleared')
        
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('🏫 PROTECH INTEGRATED ATTENDANCE & EXCUSED ABSENCE SEEDER'))
        self.stdout.write('=' * 80)
        
        # Date range: 2 weeks ago to now
        today = timezone.now().date()
        start_date = today - datetime.timedelta(days=14)
        
        self.stdout.write(f'📅 Generating data from {start_date} to {today} (2 weeks)')
        
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
        
        # School schedule settings
        SCHOOL_TIME_IN = datetime.time(8, 0)  # 8:00 AM sharp
        SCHOOL_TIME_OUT_BASE = datetime.time(17, 0)  # 5:00 PM base
        
        # Realistic attendance patterns with behavioral consistency
        STUDENT_BEHAVIOR_PATTERNS = {
            'excellent': {  # 15% of students - almost perfect
                'on_time': 0.85,
                'late': 0.10,
                'absent': 0.03,
                'excused': 0.02,
                'late_minutes_range': (1, 15),
                'absence_probability_multiplier': 0.3
            },
            'good': {  # 60% of students - normal good behavior
                'on_time': 0.75,
                'late': 0.18,
                'absent': 0.05,
                'excused': 0.02,
                'late_minutes_range': (1, 25),
                'absence_probability_multiplier': 1.0
            },
            'average': {  # 20% of students - some issues
                'on_time': 0.65,
                'late': 0.25,
                'absent': 0.08,
                'excused': 0.02,
                'late_minutes_range': (1, 40),
                'absence_probability_multiplier': 1.5
            },
            'problematic': {  # 5% of students - frequent issues
                'on_time': 0.45,
                'late': 0.35,
                'absent': 0.15,
                'excused': 0.05,
                'late_minutes_range': (5, 60),
                'absence_probability_multiplier': 2.5
            }
        }
        
        # Excuse reasons with realistic patterns
        EXCUSE_REASONS = {
            'medical_checkup': {
                'duration_days': [1],
                'letter_file': 'medical_certificate.pdf',
                'weight': 25,
                'common_days': [1, 2, 3, 4]  # Monday to Thursday
            },
            'illness_fever': {
                'duration_days': [1, 2, 3],
                'letter_file': 'parent_excuse_letter.pdf',
                'weight': 30,
                'common_days': [0, 1, 2, 3, 4]  # Any day
            },
            'family_emergency': {
                'duration_days': [1, 2],
                'letter_file': 'emergency_excuse.pdf',
                'weight': 15,
                'common_days': [0, 1, 2, 3, 4]  # Any day
            },
            'dental_appointment': {
                'duration_days': [1],
                'letter_file': 'dental_certificate.pdf',
                'weight': 12,
                'common_days': [1, 2, 3, 4]  # Tuesday to Friday
            },
            'illness_stomach': {
                'duration_days': [1, 2],
                'letter_file': 'parent_excuse_letter.pdf',
                'weight': 10,
                'common_days': [0, 1, 2, 3, 4]  # Any day
            },
            'family_event': {
                'duration_days': [1, 2, 3],
                'letter_file': 'family_event_excuse.pdf',
                'weight': 8,
                'common_days': [0, 4]  # Monday or Friday
            }
        }
        
        # Assign behavior patterns to students
        student_patterns = {}
        student_list = list(students)
        random.shuffle(student_list)
        
        pattern_distribution = {
            'excellent': int(total_students * 0.15),
            'good': int(total_students * 0.60),
            'average': int(total_students * 0.20),
            'problematic': int(total_students * 0.05)
        }
        
        idx = 0
        for pattern, count in pattern_distribution.items():
            for _ in range(count):
                if idx < len(student_list):
                    student_patterns[student_list[idx].id] = pattern
                    idx += 1
        
        # Fill remaining with 'good' pattern
        while idx < len(student_list):
            student_patterns[student_list[idx].id] = 'good'
            idx += 1
        
        if verbose:
            self.stdout.write(f'📊 Assigned behavior patterns: {pattern_distribution}')
        
        # Generate school days (Monday to Friday only)
        school_days = []
        current_date = start_date
        
        while current_date <= today:
            # Only weekdays (Monday=0, Sunday=6)
            if current_date.weekday() < 5:
                school_days.append(current_date)
            current_date += datetime.timedelta(days=1)
        
        school_days.sort()  # Ensure chronological order
        
        if verbose:
            self.stdout.write(f'📅 Generated {len(school_days)} school days (Monday-Friday only)')
        
        # Statistics tracking
        stats = {
            'total_attendance': 0,
            'on_time': 0,
            'late': 0,
            'absent': 0,
            'excused': 0,
            'total_excused_absences': 0,
            'notifications_created': 0,
            'excuse_reasons': {}
        }
        
        # Main generation loop - integrated attendance and excused absences
        with transaction.atomic():
            for day_idx, school_date in enumerate(school_days):
                if verbose and day_idx % 3 == 0:
                    self.stdout.write(f'  📝 Processing day {day_idx + 1}/{len(school_days)}: {school_date.strftime("%A, %B %d")}')
                
                # Day-specific factors
                day_of_week = school_date.weekday()  # 0=Monday, 4=Friday
                is_monday = day_of_week == 0
                is_friday = day_of_week == 4
                
                # Monday factor (slightly more absences/lateness after weekend)
                monday_factor = 1.3 if is_monday else 1.0
                # Friday factor (slightly more absences for long weekends)
                friday_factor = 1.2 if is_friday else 1.0
                
                for student in students:
                    # Get student's behavior pattern
                    pattern_name = student_patterns.get(student.id, 'good')
                    pattern = STUDENT_BEHAVIOR_PATTERNS[pattern_name]
                    
                    # Apply day factors
                    adjusted_probabilities = pattern.copy()
                    adjusted_probabilities['absent'] *= monday_factor * friday_factor
                    adjusted_probabilities['late'] *= monday_factor
                    
                    # Normalize probabilities
                    total_prob = sum(adjusted_probabilities[k] for k in ['on_time', 'late', 'absent', 'excused'])
                    for key in ['on_time', 'late', 'absent', 'excused']:
                        adjusted_probabilities[key] /= total_prob
                    
                    # Determine attendance status
                    rand = random.random()
                    cumulative = 0
                    attendance_status = AttendanceStatus.ONTIME
                    
                    for status_key, prob in adjusted_probabilities.items():
                        cumulative += prob
                        if rand <= cumulative:
                            if status_key == 'on_time':
                                attendance_status = AttendanceStatus.ONTIME
                            elif status_key == 'late':
                                attendance_status = AttendanceStatus.LATE
                            elif status_key == 'absent':
                                attendance_status = AttendanceStatus.ABSENT
                            elif status_key == 'excused':
                                attendance_status = AttendanceStatus.EXCUSED
                            break
                    
                    # Generate realistic times and notifications
                    time_in = None
                    time_out = None
                    sent_email = False
                    sent_sms = False
                    
                    if attendance_status == AttendanceStatus.ONTIME:
                        # On time: arrive exactly at 8:00 AM or up to 5 minutes early
                        early_minutes = random.randint(0, 5)
                        time_in = (datetime.datetime.combine(datetime.date.today(), SCHOOL_TIME_IN) - 
                                  datetime.timedelta(minutes=early_minutes)).time()
                        
                        # Time out varies around 5 PM
                        time_out_variance = random.randint(-15, 30)  # 4:45 PM to 5:30 PM
                        time_out = (datetime.datetime.combine(datetime.date.today(), SCHOOL_TIME_OUT_BASE) + 
                                   datetime.timedelta(minutes=time_out_variance)).time()
                        
                        stats['on_time'] += 1
                        
                    elif attendance_status == AttendanceStatus.LATE:
                        # Late: 8:01 AM or later based on student pattern
                        late_min, late_max = pattern['late_minutes_range']
                        late_minutes = random.randint(late_min, late_max)
                        time_in = (datetime.datetime.combine(datetime.date.today(), SCHOOL_TIME_IN) + 
                                  datetime.timedelta(minutes=late_minutes)).time()
                        
                        # Time out still around 5 PM but might stay later to catch up
                        time_out_variance = random.randint(-5, 45)  # 4:55 PM to 5:45 PM
                        time_out = (datetime.datetime.combine(datetime.date.today(), SCHOOL_TIME_OUT_BASE) + 
                                   datetime.timedelta(minutes=time_out_variance)).time()
                        
                        # Late students often get notifications
                        sent_email = random.random() < 0.6
                        sent_sms = random.random() < 0.3
                        
                        stats['late'] += 1
                        
                    elif attendance_status == AttendanceStatus.ABSENT:
                        # Absent: no times
                        time_in = None
                        time_out = None
                        
                        # Absent students usually get notifications
                        sent_email = random.random() < 0.85
                        sent_sms = random.random() < 0.5
                        
                        stats['absent'] += 1
                        
                    elif attendance_status == AttendanceStatus.EXCUSED:
                        # Excused: no times, but we'll create an ExcusedAbsence record
                        time_in = None
                        time_out = None
                        
                        # Excused students get confirmation notifications
                        sent_email = random.random() < 0.7
                        sent_sms = random.random() < 0.2
                        
                        stats['excused'] += 1
                        
                        # Create integrated ExcusedAbsence record
                        excuse_reason = self._choose_excuse_reason(EXCUSE_REASONS, day_of_week)
                        reason_data = EXCUSE_REASONS[excuse_reason]
                        duration = random.choice(reason_data['duration_days'])
                        
                        # Calculate end date (considering only school days)
                        end_date = self._calculate_school_end_date(school_date, duration, school_days)
                        
                        # Create excuse letter path
                        letter_filename = f"student_{student.id}_{school_date}_{reason_data['letter_file']}"
                        excuse_letter_path = f"private_excuse_letters/{letter_filename}"
                        
                        # Create ExcusedAbsence record
                        ExcusedAbsence.objects.create(
                            student=student,
                            date_absent=school_date,
                            excuse_letter=excuse_letter_path,
                            effective_date=school_date,
                            end_date=end_date
                        )
                        
                        stats['total_excused_absences'] += 1
                        stats['excuse_reasons'][excuse_reason] = stats['excuse_reasons'].get(excuse_reason, 0) + 1
                    
                    # Create Attendance record
                    Attendance.objects.create(
                        student=student,
                        date=school_date,
                        time_in=time_in,
                        time_out=time_out,
                        status=attendance_status,
                        sent_email=sent_email,
                        sent_sms=sent_sms
                    )
                    
                    stats['total_attendance'] += 1
                    
                    # Create notifications for problematic attendance
                    if (options['create_notifications'] and notification_users and 
                        attendance_status in [AttendanceStatus.LATE, AttendanceStatus.ABSENT] and 
                        random.random() < 0.25):  # 25% chance of notification
                        
                        user = random.choice(notification_users)
                        
                        if attendance_status == AttendanceStatus.LATE:
                            message = (f"🕐 LATE ARRIVAL: {student.first_name} {student.last_name} "
                                     f"({student.grade.name}-{student.section.name}) arrived late at "
                                     f"{time_in.strftime('%I:%M %p')} on {school_date.strftime('%B %d, %Y')}")
                        else:  # ABSENT
                            message = (f"❌ ABSENT: {student.first_name} {student.last_name} "
                                     f"({student.grade.name}-{student.section.name}) was absent on "
                                     f"{school_date.strftime('%B %d, %Y')}")
                        
                        # Create notification with realistic timing
                        notification_time = timezone.make_aware(
                            datetime.datetime.combine(school_date, SCHOOL_TIME_IN) + 
                            datetime.timedelta(hours=random.randint(1, 4))
                        )
                        
                        Notification.objects.create(
                            user=user,
                            message=message,
                            type=NotificationType.SYSTEM,
                            status=NotificationStatus.SENT,
                            category=NotificationCategory.ATTENDANCE,
                            sent_at=notification_time
                        )
                        
                        stats['notifications_created'] += 1
        
        # Final summary
        self.stdout.write(self.style.SUCCESS('\n✅ INTEGRATED SEEDING COMPLETED'))
        self.stdout.write('=' * 80)
        
        self.stdout.write(f'📊 ATTENDANCE STATISTICS:')
        self.stdout.write(f'   Total Records: {stats["total_attendance"]:,}')
        self.stdout.write(f'   ✅ On Time: {stats["on_time"]:,} ({stats["on_time"]/stats["total_attendance"]*100:.1f}%)')
        self.stdout.write(f'   ⏰ Late (8:01AM+): {stats["late"]:,} ({stats["late"]/stats["total_attendance"]*100:.1f}%)')
        self.stdout.write(f'   ❌ Absent: {stats["absent"]:,} ({stats["absent"]/stats["total_attendance"]*100:.1f}%)')
        self.stdout.write(f'   🏥 Excused: {stats["excused"]:,} ({stats["excused"]/stats["total_attendance"]*100:.1f}%)')
        
        self.stdout.write(f'\n🏥 EXCUSED ABSENCE STATISTICS:')
        self.stdout.write(f'   Total Excused Absence Records: {stats["total_excused_absences"]:,}')
        if stats['excuse_reasons']:
            self.stdout.write(f'   📋 Excuse Reasons:')
            for reason, count in sorted(stats['excuse_reasons'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / stats["total_excused_absences"]) * 100
                formatted_reason = reason.replace('_', ' ').title()
                self.stdout.write(f'      {formatted_reason}: {count} ({percentage:.1f}%)')
        
        if options['create_notifications']:
            self.stdout.write(f'\n📢 NOTIFICATIONS: {stats["notifications_created"]:,} created')
        
        self.stdout.write(f'\n🕐 SCHEDULE DETAILS:')
        self.stdout.write(f'   School Hours: 8:00 AM - 5:00 PM (time-out varies ±30 min)')
        self.stdout.write(f'   On Time: Exactly 8:00 AM or up to 5 minutes early')
        self.stdout.write(f'   Late: 8:01 AM or later')
        self.stdout.write(f'   School Days: Monday to Friday only')
        
        self.stdout.write(f'\n📅 DATE RANGE:')
        self.stdout.write(f'   From: {school_days[0]} ({school_days[0].strftime("%A")})')
        self.stdout.write(f'   To: {school_days[-1]} ({school_days[-1].strftime("%A")})')
        self.stdout.write(f'   Total School Days: {len(school_days)}')
        
        self.stdout.write(f'\n💡 DATA INTEGRATION:')
        self.stdout.write(f'   ✅ Attendance and ExcusedAbsence records are fully integrated')
        self.stdout.write(f'   ✅ All records ordered by date for chronological viewing')
        self.stdout.write(f'   ✅ Realistic student behavior patterns applied')
        self.stdout.write(f'   ✅ School schedule strictly enforced (8AM on-time, 8:01AM+ late)')
        
        self.stdout.write('\n🎉 Ready to view in PROTECH system!')

    def _choose_excuse_reason(self, reasons, day_of_week):
        """Choose excuse reason based on weights and day preferences"""
        # Filter reasons based on day preferences
        valid_reasons = {}
        for reason, data in reasons.items():
            if day_of_week in data['common_days']:
                valid_reasons[reason] = data['weight']
            else:
                # Reduce weight for less common days
                valid_reasons[reason] = data['weight'] * 0.3
        
        # Choose based on weighted probability
        total_weight = sum(valid_reasons.values())
        rand_weight = random.uniform(0, total_weight)
        
        current_weight = 0
        for reason, weight in valid_reasons.items():
            current_weight += weight
            if rand_weight <= current_weight:
                return reason
        
        return list(reasons.keys())[0]  # Fallback

    def _calculate_school_end_date(self, start_date, duration_days, school_days):
        """Calculate end date considering only school days"""
        if duration_days == 1:
            return start_date
        
        # Find start date in school_days list
        try:
            start_idx = school_days.index(start_date)
        except ValueError:
            return start_date
        
        # Calculate end date
        end_idx = min(start_idx + duration_days - 1, len(school_days) - 1)
        return school_days[end_idx]