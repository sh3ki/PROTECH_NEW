from django.core.management.base import BaseCommand
from django.utils import timezone
from PROTECHAPP.models import (
    Student, Attendance, ExcusedAbsence, Guardian, 
    AttendanceStatus, StudentStatus
)
import random
import datetime
from faker import Faker
import os

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds realistic excused absence data that correlates with attendance records'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing excused absence records')
        parser.add_argument('--verbose', action='store_true', help='Show detailed progress')
        parser.add_argument('--create-letters', action='store_true', help='Create excuse letter file references')
        parser.add_argument('--generate-additional', action='store_true', help='Generate additional excused absences beyond attendance records')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing excused absence records...'))
            ExcusedAbsence.objects.all().delete()
            if options['verbose']:
                self.stdout.write('✓ Excused absence records cleared')
        
        verbose = options['verbose']
        
        self.stdout.write('🏥 Generating realistic excused absence records...')
        
        # Get all excused attendance records that don't have excused absence records yet
        excused_attendances = Attendance.objects.filter(
            status=AttendanceStatus.EXCUSED
        ).select_related('student')
        
        if verbose:
            self.stdout.write(f'📋 Found {excused_attendances.count()} excused attendance records')
        
        # Common excuse reasons and their typical durations
        EXCUSE_REASONS = {
            'medical_appointment': {
                'duration_days': [1],
                'letter_types': ['medical_certificate.pdf', 'doctor_note.pdf'],
                'weight': 20
            },
            'illness_minor': {
                'duration_days': [1, 2],
                'letter_types': ['parent_letter.pdf', 'medical_note.pdf'],
                'weight': 30
            },
            'illness_moderate': {
                'duration_days': [2, 3, 4],
                'letter_types': ['medical_certificate.pdf', 'doctor_note.pdf'],
                'weight': 15
            },
            'illness_severe': {
                'duration_days': [5, 6, 7, 8, 9, 10],
                'letter_types': ['medical_certificate.pdf', 'hospital_discharge.pdf'],
                'weight': 5
            },
            'family_emergency': {
                'duration_days': [1, 2],
                'letter_types': ['parent_letter.pdf', 'emergency_note.pdf'],
                'weight': 10
            },
            'family_event': {
                'duration_days': [1, 2, 3],
                'letter_types': ['parent_letter.pdf', 'family_event_note.pdf'],
                'weight': 8
            },
            'dental_appointment': {
                'duration_days': [1],
                'letter_types': ['dental_certificate.pdf', 'parent_letter.pdf'],
                'weight': 7
            },
            'therapy_session': {
                'duration_days': [1],
                'letter_types': ['therapy_note.pdf', 'medical_certificate.pdf'],
                'weight': 3
            },
            'religious_observance': {
                'duration_days': [1, 2],
                'letter_types': ['parent_letter.pdf', 'religious_note.pdf'],
                'weight': 2
            }
        }
        
        stats = {
            'created_from_attendance': 0,
            'created_additional': 0,
            'total_days_covered': 0,
            'excuse_reasons': {}
        }
        
        # Process existing excused attendance records
        for attendance in excused_attendances:
            # Check if excused absence already exists
            if ExcusedAbsence.objects.filter(
                student=attendance.student,
                date_absent=attendance.date
            ).exists():
                continue
            
            # Choose a random excuse reason
            excuse_reason = self._choose_excuse_reason(EXCUSE_REASONS)
            reason_data = EXCUSE_REASONS[excuse_reason]
            
            # Determine duration
            duration = random.choice(reason_data['duration_days'])
            
            # Calculate end date (considering weekends)
            effective_date = attendance.date
            end_date = self._calculate_end_date(effective_date, duration)
            
            # Choose excuse letter type
            letter_type = random.choice(reason_data['letter_types'])
            
            # Generate excuse letter path
            if options['create_letters']:
                letter_filename = f"student_{attendance.student.id}_{effective_date}_{letter_type}"
                excuse_letter_path = f"private_excuse_letters/{letter_filename}"
            else:
                excuse_letter_path = "default-excuse-letter.png"
            
            # Create excused absence record
            excused_absence = ExcusedAbsence.objects.create(
                student=attendance.student,
                date_absent=attendance.date,
                excuse_letter=excuse_letter_path,
                effective_date=effective_date,
                end_date=end_date
            )
            
            stats['created_from_attendance'] += 1
            stats['total_days_covered'] += (end_date - effective_date).days + 1
            stats['excuse_reasons'][excuse_reason] = stats['excuse_reasons'].get(excuse_reason, 0) + 1
            
            if verbose and stats['created_from_attendance'] % 50 == 0:
                self.stdout.write(f'  📝 Processed {stats["created_from_attendance"]} excused absences...')
        
        # Generate additional excused absences for variety (if requested)
        if options['generate_additional']:
            self.stdout.write('📈 Generating additional excused absences...')
            
            # Get active students
            students = Student.objects.filter(status=StudentStatus.ACTIVE)
            
            # Generate additional excused absences (3-7 per student over the year)
            for student in students:
                additional_count = random.randint(2, 5)  # Conservative number
                
                for _ in range(additional_count):
                    # Generate random date in the past 90 days
                    days_back = random.randint(10, 90)
                    absence_date = (timezone.now() - datetime.timedelta(days=days_back)).date()
                    
                    # Skip weekends
                    if absence_date.weekday() >= 5:
                        continue
                    
                    # Check if student already has attendance/excuse record for this date
                    if (Attendance.objects.filter(student=student, date=absence_date).exists() or
                        ExcusedAbsence.objects.filter(student=student, date_absent=absence_date).exists()):
                        continue
                    
                    # Choose excuse reason
                    excuse_reason = self._choose_excuse_reason(EXCUSE_REASONS)
                    reason_data = EXCUSE_REASONS[excuse_reason]
                    duration = random.choice(reason_data['duration_days'])
                    
                    # Calculate dates
                    effective_date = absence_date
                    end_date = self._calculate_end_date(effective_date, duration)
                    
                    # Generate letter path
                    letter_type = random.choice(reason_data['letter_types'])
                    if options['create_letters']:
                        letter_filename = f"student_{student.id}_{effective_date}_{letter_type}"
                        excuse_letter_path = f"private_excuse_letters/{letter_filename}"
                    else:
                        excuse_letter_path = "default-excuse-letter.png"
                    
                    # Create excused absence
                    ExcusedAbsence.objects.create(
                        student=student,
                        date_absent=absence_date,
                        excuse_letter=excuse_letter_path,
                        effective_date=effective_date,
                        end_date=end_date
                    )
                    
                    # Create corresponding attendance record as EXCUSED
                    if not Attendance.objects.filter(student=student, date=absence_date).exists():
                        Attendance.objects.create(
                            student=student,
                            date=absence_date,
                            time_in=None,
                            time_out=None,
                            status=AttendanceStatus.EXCUSED,
                            sent_email=True,
                            sent_sms=random.choice([True, False])
                        )
                    
                    stats['created_additional'] += 1
                    stats['total_days_covered'] += (end_date - effective_date).days + 1
                    stats['excuse_reasons'][excuse_reason] = stats['excuse_reasons'].get(excuse_reason, 0) + 1
        
        # Create excuse letter directory if requested
        if options['create_letters']:
            letter_dir = os.path.join('media', 'private_excuse_letters')
            os.makedirs(letter_dir, exist_ok=True)
            if verbose:
                self.stdout.write(f'📁 Created excuse letters directory: {letter_dir}')
        
        # Display results
        self.stdout.write(self.style.SUCCESS('\n✅ EXCUSED ABSENCE SEEDING COMPLETED'))
        self.stdout.write(f'📊 Statistics:')
        self.stdout.write(f'   From Attendance Records: {stats["created_from_attendance"]:,}')
        if options['generate_additional']:
            self.stdout.write(f'   Additional Generated: {stats["created_additional"]:,}')
        self.stdout.write(f'   Total Excused Absences: {stats["created_from_attendance"] + stats["created_additional"]:,}')
        self.stdout.write(f'   Total Days Covered: {stats["total_days_covered"]:,}')
        
        if stats['excuse_reasons']:
            self.stdout.write(f'\n📋 Excuse Reasons Breakdown:')
            for reason, count in sorted(stats['excuse_reasons'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / (stats["created_from_attendance"] + stats["created_additional"])) * 100
                formatted_reason = reason.replace('_', ' ').title()
                self.stdout.write(f'   {formatted_reason}: {count:,} ({percentage:.1f}%)')
        
        # Show some sample records
        if verbose:
            self.stdout.write(f'\n📋 Sample Excused Absence Records:')
            samples = ExcusedAbsence.objects.order_by('-created_at')[:5]
            for excuse in samples:
                duration = (excuse.end_date - excuse.effective_date).days + 1
                self.stdout.write(
                    f'   {excuse.student.first_name} {excuse.student.last_name} '
                    f'({excuse.student.grade.name} - {excuse.student.section.name}) '
                    f'- {excuse.effective_date} to {excuse.end_date} ({duration} day{"s" if duration > 1 else ""})'
                )

    def _choose_excuse_reason(self, reasons):
        """Choose an excuse reason based on weighted probabilities"""
        total_weight = sum(data['weight'] for data in reasons.values())
        rand_weight = random.randint(1, total_weight)
        
        current_weight = 0
        for reason, data in reasons.items():
            current_weight += data['weight']
            if rand_weight <= current_weight:
                return reason
        
        return list(reasons.keys())[0]  # Fallback

    def _calculate_end_date(self, start_date, duration_days):
        """Calculate end date considering weekends"""
        current_date = start_date
        days_added = 0
        
        while days_added < duration_days:
            # If it's a school day (Monday-Friday), count it
            if current_date.weekday() < 5:
                days_added += 1
            
            # If we haven't reached the target duration, move to next day
            if days_added < duration_days:
                current_date += datetime.timedelta(days=1)
        
        return current_date

    def _create_realistic_letter_content(self, student, reason, date):
        """Generate realistic excuse letter content (for future enhancement)"""
        # This could be expanded to create actual letter files with realistic content
        templates = {
            'medical': f"Medical Certificate: {student.first_name} {student.last_name} was unable to attend school on {date} due to medical reasons.",
            'family': f"Family Emergency: {student.first_name} {student.last_name} was absent on {date} due to a family emergency.",
            'appointment': f"Medical Appointment: {student.first_name} {student.last_name} had a scheduled medical appointment on {date}."
        }
        return templates.get(reason, f"Excuse letter for {student.first_name} {student.last_name} - {date}")