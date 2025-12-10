from django.core.management.base import BaseCommand
from django.db import transaction
from PROTECHAPP.models import Grade, Section, CustomUser, UserRole

class Command(BaseCommand):
    help = 'Seeds the database with grades 7-12 and 5 sections for each grade with Philippine high school section names'

    def handle(self, *args, **options):
        self.stdout.write('Starting to seed grades and sections...')
        
        # Delete existing grades and sections to avoid duplicates
        Section.objects.all().delete()
        Grade.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Cleared existing grades and sections'))
        
        # Varied Filipino high school section names for each grade
        grade_section_names = {
            7: ['Mabini', 'Rizal', 'Bonifacio', 'Del Pilar', 'Luna'],
            8: ['Aguinaldo', 'Jacinto', 'Malvar', 'Sakay', 'Tangkad'],
            9: ['Bataan', 'Corregidor', 'Leyte', 'Mindanao', 'Palawan'],
            10: ['Magallanes', 'Lapu-Lapu', 'Dagohoy', 'Silang', 'Gabriela'],
            11: ['Sampaguita', 'Narra', 'Banaba', 'Molave', 'Yakal'],
            12: ['Makiling', 'Mayon', 'Taal', 'Pinatubo', 'Apo']
        }
        
        with transaction.atomic():
            grades_created = 0
            sections_created = 0
            
            # First create the grade objects
            grade_objects = {}
            for grade_num in range(7, 13):
                grade_name = f"Grade {grade_num}"
                grade = Grade.objects.create(
                    name=grade_name
                )
                grade_objects[grade_num] = grade
                grades_created += 1
                self.stdout.write(f'Created grade: {grade_name}')
            
            # Then create sections for each grade with varied names
            section_objects = []
            for grade_num, grade_obj in grade_objects.items():
                section_names = grade_section_names[grade_num]
                for section_name in section_names:
                    section = Section.objects.create(
                        name=section_name,
                        grade=grade_obj
                    )
                    section_objects.append(section)
                    sections_created += 1
                    self.stdout.write(f'Created section: {grade_obj.name} - {section_name}')
            
            # Now assign advisory teachers to sections
            # Only get teachers with 'teacher_adv' username pattern (not 'teacher_non')
            advisory_teachers = CustomUser.objects.filter(
                role=UserRole.TEACHER,
                username__startswith='teacher_adv',  # Only advisory teachers
                section__isnull=True  # Teachers not yet assigned to sections
            ).order_by('username')[:30]  # Get first 30 advisory teachers
            
            # Import AdvisoryAssignment model
            from PROTECHAPP.models import AdvisoryAssignment
            
            teachers_assigned = 0
            for i, section in enumerate(section_objects):
                if i < len(advisory_teachers):
                    teacher = advisory_teachers[i]
                    teacher.section = section
                    teacher.save()
                    
                    # Create AdvisoryAssignment record
                    AdvisoryAssignment.objects.get_or_create(
                        teacher=teacher,
                        section=section
                    )
                    
                    teachers_assigned += 1
                    self.stdout.write(f'Assigned {teacher.first_name} {teacher.last_name} as advisor to {section.grade.name} - {section.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded database with {grades_created} grades and {sections_created} sections.\n'
                f'Created grades 7-12 with 5 varied Filipino section names per grade.\n'
                f'Grade 7: Mabini, Rizal, Bonifacio, Del Pilar, Luna\n'
                f'Grade 8: Aguinaldo, Jacinto, Malvar, Sakay, Tangkad\n'
                f'Grade 9: Bataan, Corregidor, Leyte, Mindanao, Palawan\n'
                f'Grade 10: Magallanes, Lapu-Lapu, Dagohoy, Silang, Gabriela\n'
                f'Grade 11: Sampaguita, Narra, Banaba, Molave, Yakal\n'
                f'Grade 12: Makiling, Mayon, Taal, Pinatubo, Apo\n'
                f'Assigned {teachers_assigned} advisory teachers to sections.\n'
                f'Total sections created: {sections_created}'
            )
        )
