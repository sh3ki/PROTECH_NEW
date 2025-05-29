from django.core.management.base import BaseCommand
from django.utils import timezone
from PROTECHAPP.models import Student, ExcusedAbsence
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Populate ExcusedAbsence records based on students with EXCUSED status in Attendance.'

    def handle(self, *args, **options):
        from PROTECHAPP.models import Attendance

        excused_attendance = Attendance.objects.filter(status='EXCUSED')
        created_count = 0

        for att in excused_attendance:
            # Avoid duplicate ExcusedAbsence for same student/date
            exists = ExcusedAbsence.objects.filter(
                student=att.student,
                date_absent=att.date
            ).exists()
            if exists:
                continue

            ExcusedAbsence.objects.create(
                student=att.student,
                date_absent=att.date,
                excuse_letter='default-excuse-letter.png',
                effective_date=att.date,
                end_date=att.date,
            )
            created_count += 1
            self.stdout.write(self.style.SUCCESS(
                f'Created ExcusedAbsence for {att.student} on {att.date}'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'ExcusedAbsence seeding complete. {created_count} records created.'
        ))
