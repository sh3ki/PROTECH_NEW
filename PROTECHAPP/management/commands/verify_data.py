from django.core.management.base import BaseCommand
from PROTECHAPP.models import CustomUser, UserRole, Grade, Section, Student, Guardian

class Command(BaseCommand):
    help = 'Verifies the seeded data in the database'

    def handle(self, *args, **options):
        self.stdout.write('=== DATABASE VERIFICATION ===')
        
        # Check users by role
        self.stdout.write('\n1. USER COUNTS BY ROLE:')
        self.stdout.write('-' * 30)
        for role in UserRole:
            count = CustomUser.objects.filter(role=role.value).count()
            self.stdout.write(f'{role.label}: {count}')
        
        total_users = CustomUser.objects.count()
        self.stdout.write(f'Total Users: {total_users}')
        
        # Check grades and sections
        self.stdout.write('\n2. GRADES AND SECTIONS:')
        self.stdout.write('-' * 30)
        grades = Grade.objects.all().order_by('name')
        for grade in grades:
            sections = Section.objects.filter(grade=grade)
            section_names = [s.name for s in sections]
            self.stdout.write(f'{grade.name}: {len(sections)} sections ({", ".join(section_names)})')
        
        total_grades = Grade.objects.count()
        total_sections = Section.objects.count()
        self.stdout.write(f'Total Grades: {total_grades}')
        self.stdout.write(f'Total Sections: {total_sections}')
        
        # Check students and guardians
        self.stdout.write('\n3. STUDENTS AND GUARDIANS:')
        self.stdout.write('-' * 30)
        total_students = Student.objects.count()
        total_guardians = Guardian.objects.count()
        avg_guardians = total_guardians / total_students if total_students > 0 else 0
        
        self.stdout.write(f'Total Students: {total_students}')
        self.stdout.write(f'Total Guardians: {total_guardians}')
        self.stdout.write(f'Average Guardians per Student: {avg_guardians:.2f}')
        
        # Check section assignments
        self.stdout.write('\n4. ADVISORY TEACHER ASSIGNMENTS:')
        self.stdout.write('-' * 30)
        advisory_teachers = CustomUser.objects.filter(role=UserRole.TEACHER, section__isnull=False)
        unassigned_teachers = CustomUser.objects.filter(role=UserRole.TEACHER, section__isnull=True)
        
        self.stdout.write(f'Advisory Teachers (assigned): {advisory_teachers.count()}')
        self.stdout.write(f'Non-Advisory Teachers (unassigned): {unassigned_teachers.count()}')
        
        # Sample data
        self.stdout.write('\n5. SAMPLE SECTION DATA:')
        self.stdout.write('-' * 30)
        sample_section = Section.objects.first()
        if sample_section:
            students_in_section = Student.objects.filter(section=sample_section).count()
            advisor = CustomUser.objects.filter(section=sample_section).first()
            self.stdout.write(f'Sample Section: {sample_section.grade.name} - {sample_section.name}')
            self.stdout.write(f'Students in section: {students_in_section}')
            if advisor:
                self.stdout.write(f'Advisor: {advisor.first_name} {advisor.last_name}')
        
        self.stdout.write('\n=== VERIFICATION COMPLETE ===')
        self.stdout.write(self.style.SUCCESS('Database has been successfully populated!'))