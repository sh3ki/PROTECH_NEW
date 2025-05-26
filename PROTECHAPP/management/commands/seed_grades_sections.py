from django.core.management.base import BaseCommand
from django.db import transaction
from PROTECHAPP.models import Grade, Section

class Command(BaseCommand):
    help = 'Seeds the database with grades 7-12 and 5 sections for each grade'

    def handle(self, *args, **options):
        self.stdout.write('Starting to seed grades and sections...')
        
        # Delete existing grades and sections to avoid duplicates
        Section.objects.all().delete()
        Grade.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Cleared existing grades and sections'))
        
        with transaction.atomic():
            grades_created = 0
            sections_created = 0
            
            # First create the grade objects
            grade_objects = {}
            for grade_num in range(7, 13):
                grade = Grade.objects.create(
                    name=str(grade_num)
                )
                grade_objects[grade_num] = grade
                grades_created += 1
            
            # Then create sections for each grade
            for grade_num, grade_obj in grade_objects.items():
                for section_num in range(1, 6):
                    section_name = str(section_num)
                    Section.objects.create(
                        name=section_name,
                        grade=grade_obj
                    )
                    sections_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded database with {grades_created} grades and {sections_created} sections.\n'
                f'Created grades 7-12 with 5 sections each (total: {sections_created} sections)'
            )
        )
