from django.core.management.base import BaseCommand
from django.utils import timezone
from PROTECHAPP.models import Student, Attendance, AttendanceStatus, StudentStatus, ExcusedAbsence, Notification, CustomUser, NotificationType, NotificationStatus, NotificationCategory
import random
import datetime

class Command(BaseCommand):
    help = 'Seeds the attendance table with realistic data'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30, help='Number of days to generate attendance for')
        parser.add_argument('--start-date', type=str, help='Start date in YYYY-MM-DD format')
        parser.add_argument('--clear', action='store_true', help='Clear existing attendance records')
        parser.add_argument('--create-excuses', action='store_true', help='Create excused absence records for excused students')
        parser.add_argument('--create-notifications', action='store_true', help='Create notification records for absences and late arrivals')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing attendance records...')
            Attendance.objects.all().delete()
        
        days = options['days']
        
        if options['start_date']:
            start_date = datetime.datetime.strptime(options['start_date'], '%Y-%m-%d').date()
        else:
            # Default to 'days' days ago
            start_date = (timezone.now() - datetime.timedelta(days=days-1)).date()
        
        # Make sure we don't generate future dates
        now = timezone.now().date()
        if start_date > now:
            self.stdout.write(self.style.WARNING(f'Start date {start_date} is in the future. Using current date instead.'))
            start_date = now
        
        self.stdout.write(f'Generating attendance records starting from {start_date}')
        
        # Get all active students
        students = Student.objects.filter(status=StudentStatus.ACTIVE)
        total_students = students.count()
        
        if total_students == 0:
            self.stdout.write(self.style.ERROR('No active students found. Nothing to do.'))
            return
            
        self.stdout.write(f'Found {total_students} active students')
        
        # Get admin users for notifications
        admins = None
        if options['create_notifications']:
            admins = list(CustomUser.objects.filter(is_active=True))
            if not admins:
                self.stdout.write(self.style.WARNING('No active users found for notifications.'))
        
        # Get system settings for default attendance times
        from PROTECHAPP.models import SystemSettings
        try:
            settings = SystemSettings.objects.first()
            default_time_in = settings.attendance_time_in
            default_time_out = settings.attendance_time_out
        except (SystemSettings.DoesNotExist, AttributeError):
            # Default times if settings aren't available
            default_time_in = datetime.time(7, 0)
            default_time_out = datetime.time(16, 0)
        
        # Generate attendance records
        created_count = 0
        
        for day_offset in range(days):
            current_date = start_date + datetime.timedelta(days=day_offset)
            
            # Skip weekends and future dates
            if current_date.weekday() >= 5 or current_date > now:
                continue
                
            for student in students:
                # Check if record already exists
                if Attendance.objects.filter(student=student, date=current_date).exists():
                    continue
                
                # Generate random status based on distribution
                rand_val = random.random()
                
                if rand_val < 0.55:  # 55% On Time
                    status = AttendanceStatus.ONTIME
                    time_in = (datetime.datetime.combine(datetime.date.today(), default_time_in) - 
                              datetime.timedelta(minutes=random.randint(0, 15))).time()
                    time_out = default_time_out
                    sent_email = False
                    sent_sms = False
                    
                elif rand_val < 0.85:  # 30% Late
                    status = AttendanceStatus.LATE
                    time_in = (datetime.datetime.combine(datetime.date.today(), default_time_in) + 
                              datetime.timedelta(minutes=random.randint(1, 30))).time()
                    time_out = default_time_out
                    # Sometimes we've sent notifications for late students
                    sent_email = random.random() < 0.7  # 70% chance email was sent
                    sent_sms = random.random() < 0.5    # 50% chance SMS was sent
                    
                elif rand_val < 0.95:  # 10% Absent
                    status = AttendanceStatus.ABSENT
                    time_in = None
                    time_out = None
                    # Usually we've sent notifications for absent students
                    sent_email = random.random() < 0.9  # 90% chance email was sent
                    sent_sms = random.random() < 0.7    # 70% chance SMS was sent
                    
                else:  # 5% Excused
                    status = AttendanceStatus.EXCUSED
                    time_in = None
                    time_out = None
                    sent_email = True
                    sent_sms = True
                    
                    # Create excused absence record if requested
                    if options['create_excuses']:
                        # Random excuse for 1-5 days
                        excuse_days = random.randint(1, 5)
                        ExcusedAbsence.objects.create(
                            student=student,
                            date_absent=current_date,
                            excuse_letter=f"excuses/student_{student.id}_{current_date}.pdf",
                            effective_date=current_date,
                            end_date=current_date + datetime.timedelta(days=excuse_days-1)
                        )
                
                # Create attendance record
                attendance = Attendance.objects.create(
                    student=student,
                    date=current_date,
                    time_in=time_in,
                    time_out=time_out,
                    status=status,
                    sent_email=sent_email,
                    sent_sms=sent_sms
                )
                created_count += 1
                
                # Create notifications if requested
                if options['create_notifications'] and admins and (status == AttendanceStatus.LATE or status == AttendanceStatus.ABSENT):
                    # Choose a random admin to notify
                    admin = random.choice(admins)
                    message = f"Student {student.first_name} {student.last_name} was {status.lower()} on {current_date}"
                    
                    Notification.objects.create(
                        user=admin,
                        message=message,
                        type=NotificationType.SYSTEM,
                        status=NotificationStatus.SENT,
                        category=NotificationCategory.ATTENDANCE,
                        sent_at=timezone.now() - datetime.timedelta(minutes=random.randint(1, 60))
                    )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} attendance records'))
