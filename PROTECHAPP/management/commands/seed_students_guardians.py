from django.core.management.base import BaseCommand
from django.db import transaction
from PROTECHAPP.models import Student, Guardian, Grade, Section
import random
from faker import Faker
import string

class Command(BaseCommand):
    help = 'Seeds the database with random students and guardians'

    def handle(self, *args, **options):
        self.stdout.write('Starting to seed students and guardians...')
        
        fake = Faker()
        
        # Get all sections from the database
        sections = Section.objects.select_related('grade').all()
        
        if not sections.exists():
            self.stdout.write(self.style.ERROR('No sections found. Please run seed_grades_sections first.'))
            return
        
        # Set relationship weights to favor FATHER and MOTHER
        relationship_choices = [
            'FATHER', 'FATHER', 'FATHER', 'FATHER',  # 4x weight for FATHER
            'MOTHER', 'MOTHER', 'MOTHER', 'MOTHER',  # 4x weight for MOTHER
            'GUARDIAN', 'GRANDMOTHER', 'GRANDFATHER', 
            'AUNT', 'UNCLE', 'SIBLING', 'OTHER'
        ]
        
        # Track total counts
        total_students = 0
        total_guardians = 0
        
        try:
            with transaction.atomic():
                # Clear existing data
                Guardian.objects.all().delete()
                Student.objects.all().delete()
                
                # For each section, create 15-30 students
                for section in sections:
                    self.stdout.write(f"Creating students for Grade {section.grade.name} Section {section.name}...")
                    
                    # Generate a random number of students for this section (15-30)
                    num_students = random.randint(15, 30)
                    
                    for _ in range(num_students):
                        # Generate student data
                        first_name = fake.first_name()
                        middle_name = fake.first_name() if random.random() > 0.3 else ''  # 70% have middle name
                        last_name = fake.last_name()
                        
                        # Generate a 12-digit LRN
                        lrn = ''.join(random.choices(string.digits, k=12))
                        
                        # Create student
                        student = Student.objects.create(
                            lrn=lrn,
                            first_name=first_name,
                            middle_name=middle_name,
                            last_name=last_name,
                            grade=section.grade,
                            section=section,
                            status='ACTIVE'
                        )
                        total_students += 1
                        
                        # Generate 1-2 guardians for this student (80% chance of having only 1 guardian)
                        num_guardians = 1 if random.random() < 0.8 else 2
                        
                        # If two guardians, make them a mother-father pair
                        if num_guardians == 2:
                            relationships = ['FATHER', 'MOTHER']
                        else:
                            # If only one guardian, use weighted relationship choices
                            relationships = [random.choice(relationship_choices)]
                        
                        # Create the guardians
                        for relationship in relationships:
                            # Determine last name based on relationship
                            guardian_last_name = last_name
                            if relationship in ['AUNT', 'UNCLE', 'GRANDMOTHER', 'GRANDFATHER'] and random.random() < 0.5:
                                # 50% chance for these relations to have different last name
                                guardian_last_name = fake.last_name()
                            
                            # Generate contact info - ALWAYS provide email and phone number since they're required
                            email = fake.email()  # Always generate an email
                            phone = f"+63{fake.msisdn()[3:]}"  # Always generate a valid phone number
                            
                            # Create guardian
                            guardian = Guardian.objects.create(
                                first_name=fake.first_name(),
                                middle_name=fake.first_name() if random.random() > 0.5 else '',  # 50% have middle name
                                last_name=guardian_last_name,
                                relationship=relationship,
                                email=email,
                                phone=phone,  # Always set a phone number
                                student=student  # Link to student
                            )
                            total_guardians += 1
                
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully seeded database with {total_students} students '
                    f'and {total_guardians} guardians.\n'
                    f'Average guardians per student: {total_guardians / total_students:.2f}'
                ))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error seeding students and guardians: {str(e)}'))
            raise
