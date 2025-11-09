from django.core.management.base import BaseCommand
from PROTECHAPP.models import CustomUser, Grade, Section, Student, Guardian, UserRole

class Command(BaseCommand):
    help = 'Verifies the new data structure with correct user counts and varied section names'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== DATA VERIFICATION REPORT ==='))
        
        # User counts verification
        self.stdout.write('\n1. USER ACCOUNTS VERIFICATION:')
        self.stdout.write('==============================')
        
        total_users = CustomUser.objects.count()
        principals = CustomUser.objects.filter(role=UserRole.PRINCIPAL).count()
        admins = CustomUser.objects.filter(role=UserRole.ADMIN).count()
        registrars = CustomUser.objects.filter(role=UserRole.REGISTRAR).count()
        teachers = CustomUser.objects.filter(role=UserRole.TEACHER).count()
        advisory_teachers = CustomUser.objects.filter(role=UserRole.TEACHER, section__isnull=False).count()
        non_advisory_teachers = CustomUser.objects.filter(role=UserRole.TEACHER, section__isnull=True).count()
        
        self.stdout.write(f'Total Users: {total_users}')
        self.stdout.write(f'Principals: {principals} (Expected: 3)')
        self.stdout.write(f'Admins: {admins} (Expected: 3)')
        self.stdout.write(f'Registrars: {registrars} (Expected: 3)')
        self.stdout.write(f'Total Teachers: {teachers} (Expected: 35)')
        self.stdout.write(f'Advisory Teachers: {advisory_teachers} (Expected: 30)')
        self.stdout.write(f'Non-Advisory Teachers: {non_advisory_teachers} (Expected: 5)')
        
        # Verification status
        user_counts_correct = (
            principals == 3 and 
            admins == 3 and 
            registrars == 3 and 
            advisory_teachers == 30 and 
            non_advisory_teachers == 5
        )
        
        if user_counts_correct:
            self.stdout.write(self.style.SUCCESS('✓ User counts are CORRECT!'))
        else:
            self.stdout.write(self.style.ERROR('✗ User counts are INCORRECT!'))
        
        # Section names verification
        self.stdout.write('\n2. SECTION NAMES VERIFICATION:')
        self.stdout.write('==============================')
        
        expected_sections = {
            7: ['Mabini', 'Rizal', 'Bonifacio', 'Del Pilar', 'Luna'],
            8: ['Aguinaldo', 'Jacinto', 'Malvar', 'Sakay', 'Tangkad'],
            9: ['Bataan', 'Corregidor', 'Leyte', 'Mindanao', 'Palawan'],
            10: ['Magallanes', 'Lapu-Lapu', 'Dagohoy', 'Silang', 'Gabriela'],
            11: ['Sampaguita', 'Narra', 'Banaba', 'Molave', 'Yakal'],
            12: ['Makiling', 'Mayon', 'Taal', 'Pinatubo', 'Apo']
        }
        
        sections_correct = True
        for grade_num in range(7, 13):
            grade = Grade.objects.get(name=f'Grade {grade_num}')
            sections = Section.objects.filter(grade=grade).values_list('name', flat=True).order_by('name')
            expected = sorted(expected_sections[grade_num])
            actual = sorted(list(sections))
            
            self.stdout.write(f'\nGrade {grade_num}:')
            self.stdout.write(f'  Expected: {", ".join(expected)}')
            self.stdout.write(f'  Actual:   {", ".join(actual)}')
            
            if actual == expected:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Grade {grade_num} sections are CORRECT!'))
            else:
                self.stdout.write(self.style.ERROR(f'  ✗ Grade {grade_num} sections are INCORRECT!'))
                sections_correct = False
        
        # Summary statistics
        self.stdout.write('\n3. SUMMARY STATISTICS:')
        self.stdout.write('======================')
        
        total_grades = Grade.objects.count()
        total_sections = Section.objects.count()
        total_students = Student.objects.count()
        total_guardians = Guardian.objects.count()
        
        self.stdout.write(f'Total Grades: {total_grades}')
        self.stdout.write(f'Total Sections: {total_sections}')
        self.stdout.write(f'Total Students: {total_students}')
        self.stdout.write(f'Total Guardians: {total_guardians}')
        
        # Advisory assignments verification
        self.stdout.write('\n4. ADVISORY ASSIGNMENTS:')
        self.stdout.write('=========================')
        
        sections_with_advisors = Section.objects.filter(advisors__isnull=False).count()
        sections_without_advisors = Section.objects.filter(advisors__isnull=True).count()
        
        self.stdout.write(f'Sections with advisors: {sections_with_advisors}')
        self.stdout.write(f'Sections without advisors: {sections_without_advisors}')
        
        if sections_with_advisors == 30 and sections_without_advisors == 0:
            self.stdout.write(self.style.SUCCESS('✓ All sections have advisory teachers assigned!'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Not all sections have advisors assigned.'))
        
        # Final verification result
        self.stdout.write('\n5. OVERALL VERIFICATION RESULT:')
        self.stdout.write('================================')
        
        if user_counts_correct and sections_correct:
            self.stdout.write(self.style.SUCCESS('🎉 ALL VERIFICATIONS PASSED! Database structure is correct.'))
        else:
            self.stdout.write(self.style.ERROR('❌ Some verifications failed. Please check the details above.'))
        
        self.stdout.write('\n=== END OF VERIFICATION REPORT ===')