from django.core.management.base import BaseCommand
from PROTECHAPP.models import CustomUser, UserRole, Section

class Command(BaseCommand):
    help = 'Check advisory teacher assignments'

    def handle(self, *args, **options):
        self.stdout.write('=== ADVISORY TEACHER ASSIGNMENT CHECK ===')
        
        # Check teachers with sections assigned
        teachers_with_sections = CustomUser.objects.filter(
            role=UserRole.TEACHER, 
            section__isnull=False
        )
        
        self.stdout.write(f'Teachers with sections assigned: {teachers_with_sections.count()}')
        
        if teachers_with_sections.exists():
            self.stdout.write('\nFirst 10 assignments:')
            for teacher in teachers_with_sections[:10]:
                self.stdout.write(f'  {teacher.first_name} {teacher.last_name} -> {teacher.section.grade.name} - {teacher.section.name}')
        
        # Check sections and their advisors
        self.stdout.write('\n=== SECTIONS AND ADVISORS ===')
        sections = Section.objects.all()[:10]
        
        for section in sections:
            advisor = CustomUser.objects.filter(section=section).first()
            advisor_name = f"{advisor.first_name} {advisor.last_name}" if advisor else "No advisor"
            self.stdout.write(f'{section.grade.name} - {section.name}: {advisor_name}')
        
        # Check if there's a mismatch
        self.stdout.write('\n=== POTENTIAL ISSUES ===')
        sections_without_advisors = []
        for section in Section.objects.all():
            advisor = CustomUser.objects.filter(section=section).first()
            if not advisor:
                sections_without_advisors.append(f'{section.grade.name} - {section.name}')
        
        if sections_without_advisors:
            self.stdout.write(f'Sections without advisors ({len(sections_without_advisors)}):')
            for section_name in sections_without_advisors[:10]:
                self.stdout.write(f'  {section_name}')
        else:
            self.stdout.write('All sections have advisors assigned!')