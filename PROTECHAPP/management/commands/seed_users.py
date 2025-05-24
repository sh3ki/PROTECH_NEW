from django.core.management.base import BaseCommand
from PROTECHAPP.models import CustomUser, UserRole, UserStatus
from django.db import transaction

class Command(BaseCommand):
    help = 'Seeds the database with initial user accounts for each role'

    def handle(self, *args, **options):
        self.stdout.write('Creating user accounts...')
        
        # Common password for all accounts
        password = 'Password123!'
        
        try:
            with transaction.atomic():
                # Create principal account
                principal, created = CustomUser.objects.get_or_create(
                    username='principal',
                    email='principal@protech.com',
                    defaults={
                        'first_name': 'Principal',
                        'last_name': 'User',
                        'role': UserRole.PRINCIPAL,
                        'status': UserStatus.APPROVED,
                        'is_staff': True,
                        'is_active': True,
                    }
                )
                if created:
                    principal.set_password(password)
                    principal.save()
                    self.stdout.write(self.style.SUCCESS(f'Created principal account: {principal.username}'))
                else:
                    self.stdout.write(f'Principal account already exists: {principal.username}')
                
                # Create registrar account
                registrar, created = CustomUser.objects.get_or_create(
                    username='registrar',
                    email='registrar@protech.com',
                    defaults={
                        'first_name': 'Registrar',
                        'last_name': 'User',
                        'role': UserRole.REGISTRAR,
                        'status': UserStatus.APPROVED,
                        'is_staff': True,
                        'is_active': True,
                    }
                )
                if created:
                    registrar.set_password(password)
                    registrar.save()
                    self.stdout.write(self.style.SUCCESS(f'Created registrar account: {registrar.username}'))
                else:
                    self.stdout.write(f'Registrar account already exists: {registrar.username}')
                
                # Create non-advisory teacher account
                teacher_non, created = CustomUser.objects.get_or_create(
                    username='teachernonadvisory',
                    email='teachernonadvisory@protech.com',
                    defaults={
                        'first_name': 'Teacher',
                        'last_name': 'Non-Advisory',
                        'role': UserRole.TEACHER,
                        'status': UserStatus.APPROVED,
                        'is_staff': False,
                        'is_active': True,
                        'section': None,  # No section assigned
                    }
                )
                if created:
                    teacher_non.set_password(password)
                    teacher_non.save()
                    self.stdout.write(self.style.SUCCESS(f'Created non-advisory teacher account: {teacher_non.username}'))
                else:
                    self.stdout.write(f'Non-advisory teacher account already exists: {teacher_non.username}')
                
                # Create advisory teacher account (section will be null for now)
                teacher_advisory, created = CustomUser.objects.get_or_create(
                    username='teacheradvisory',
                    email='teacheradvisory@protech.com',
                    defaults={
                        'first_name': 'Teacher',
                        'last_name': 'Advisory',
                        'role': UserRole.TEACHER,
                        'status': UserStatus.APPROVED,
                        'is_staff': False,
                        'is_active': True,
                        'section': None,  # Will be assigned later
                    }
                )
                if created:
                    teacher_advisory.set_password(password)
                    teacher_advisory.save()
                    self.stdout.write(self.style.SUCCESS(f'Created advisory teacher account: {teacher_advisory.username}'))
                else:
                    self.stdout.write(f'Advisory teacher account already exists: {teacher_advisory.username}')
                
                # Create admin account as well
                admin, created = CustomUser.objects.get_or_create(
                    username='admin',
                    email='admin@protech.com',
                    defaults={
                        'first_name': 'System',
                        'last_name': 'Administrator',
                        'role': UserRole.ADMIN,
                        'status': UserStatus.APPROVED,
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True,
                    }
                )
                if created:
                    admin.set_password(password)
                    admin.save()
                    self.stdout.write(self.style.SUCCESS(f'Created admin account: {admin.username}'))
                else:
                    self.stdout.write(f'Admin account already exists: {admin.username}')
                
                self.stdout.write(self.style.SUCCESS('All user accounts created successfully!'))
                
                self.stdout.write("\nUser Accounts Summary:")
                self.stdout.write("----------------------")
                self.stdout.write(f"Admin: admin@protech.com / {password}")
                self.stdout.write(f"Principal: principal@protech.com / {password}")
                self.stdout.write(f"Registrar: registrar@protech.com / {password}")
                self.stdout.write(f"Non-Advisory Teacher: teachernonadvisory@protech.com / {password}")
                self.stdout.write(f"Advisory Teacher: teacheradvisory@protech.com / {password}")
                self.stdout.write("----------------------")
                self.stdout.write("Note: Advisory teacher has no section assigned yet.")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating user accounts: {str(e)}'))
