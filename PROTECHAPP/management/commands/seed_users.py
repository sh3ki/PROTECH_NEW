from django.core.management.base import BaseCommand
from PROTECHAPP.models import CustomUser, UserRole, UserStatus
from django.db import transaction

class Command(BaseCommand):
    help = 'Seeds the database with at least 3 user accounts for each role'

    def handle(self, *args, **options):
        self.stdout.write('Creating user accounts...')
        
        # Common password for all accounts
        password = 'Password123!'
        
        try:
            with transaction.atomic():
                # Clear existing users first
                CustomUser.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Cleared existing user accounts'))
                
                created_users = []
                
                # Create 3 principal accounts
                principal_names = [
                    ('Maria', 'Santos', 'principal1'),
                    ('Jose', 'Reyes', 'principal2'), 
                    ('Ana', 'Cruz', 'principal3')
                ]
                
                for first_name, last_name, username in principal_names:
                    principal = CustomUser.objects.create(
                        username=username,
                        email=f'{username}@protech.com',
                        first_name=first_name,
                        last_name=last_name,
                        role=UserRole.PRINCIPAL,
                        is_staff=True,
                        is_active=True,
                        is_new=False
                    )
                    principal.set_password(password)
                    principal.save()
                    created_users.append(f'Principal: {username}@protech.com')
                    self.stdout.write(self.style.SUCCESS(f'Created principal account: {principal.username}'))
                
                # Create 3 admin accounts
                admin_names = [
                    ('Roberto', 'Garcia', 'admin1'),
                    ('Carmen', 'Gonzales', 'admin2'),
                    ('Pedro', 'Martinez', 'admin3')
                ]
                
                for first_name, last_name, username in admin_names:
                    admin = CustomUser.objects.create(
                        username=username,
                        email=f'{username}@protech.com',
                        first_name=first_name,
                        last_name=last_name,
                        role=UserRole.ADMIN,
                        is_staff=True,
                        is_superuser=True,
                        is_active=True,
                        is_new=False
                    )
                    admin.set_password(password)
                    admin.save()
                    created_users.append(f'Admin: {username}@protech.com')
                    self.stdout.write(self.style.SUCCESS(f'Created admin account: {admin.username}'))
                
                # Create 3 registrar accounts
                registrar_names = [
                    ('Elena', 'Rodriguez', 'registrar1'),
                    ('Miguel', 'Lopez', 'registrar2'),
                    ('Sofia', 'Hernandez', 'registrar3')
                ]
                
                for first_name, last_name, username in registrar_names:
                    registrar = CustomUser.objects.create(
                        username=username,
                        email=f'{username}@protech.com',
                        first_name=first_name,
                        last_name=last_name,
                        role=UserRole.REGISTRAR,
                        is_staff=True,
                        is_active=True,
                        is_new=False
                    )
                    registrar.set_password(password)
                    registrar.save()
                    created_users.append(f'Registrar: {username}@protech.com')
                    self.stdout.write(self.style.SUCCESS(f'Created registrar account: {registrar.username}'))
                
                # Create 5 non-advisory teacher accounts
                non_advisory_teachers = [
                    ('Juan', 'Dela Cruz', 'teacher_non1'),
                    ('Rosa', 'Aquino', 'teacher_non2'),
                    ('Mario', 'Villanueva', 'teacher_non3'),
                    ('Luz', 'Mercado', 'teacher_non4'),
                    ('Antonio', 'Ramos', 'teacher_non5')
                ]
                
                for first_name, last_name, username in non_advisory_teachers:
                    teacher = CustomUser.objects.create(
                        username=username,
                        email=f'{username}@protech.com',
                        first_name=first_name,
                        last_name=last_name,
                        role=UserRole.TEACHER,
                        is_staff=False,
                        is_active=True,
                        is_new=False,
                        section=None  # No section assigned (non-advisory)
                    )
                    teacher.set_password(password)
                    teacher.save()
                    created_users.append(f'Non-Advisory Teacher: {username}@protech.com')
                    self.stdout.write(self.style.SUCCESS(f'Created non-advisory teacher account: {teacher.username}'))
                
                # Create 30 advisory teacher accounts (will be assigned to sections later)
                advisory_teachers = [
                    ('Teresa', 'Fernandez', 'teacher_adv1'),
                    ('Ricardo', 'Torres', 'teacher_adv2'),
                    ('Margarita', 'Flores', 'teacher_adv3'),
                    ('Eduardo', 'Morales', 'teacher_adv4'),
                    ('Gloria', 'Castillo', 'teacher_adv5'),
                    ('Fernando', 'Jimenez', 'teacher_adv6'),
                    ('Esperanza', 'Ruiz', 'teacher_adv7'),
                    ('Alejandro', 'Mendoza', 'teacher_adv8'),
                    ('Dolores', 'Aguilar', 'teacher_adv9'),
                    ('Sergio', 'Ortega', 'teacher_adv10'),
                    ('Concepcion', 'Vargas', 'teacher_adv11'),
                    ('Raul', 'Gutierrez', 'teacher_adv12'),
                    ('Pilar', 'Chavez', 'teacher_adv13'),
                    ('Enrique', 'Herrera', 'teacher_adv14'),
                    ('Soledad', 'Medina', 'teacher_adv15'),
                    ('Francisco', 'Sandoval', 'teacher_adv16'),
                    ('Remedios', 'Campos', 'teacher_adv17'),
                    ('Alfredo', 'Cortez', 'teacher_adv18'),
                    ('Amparo', 'Vega', 'teacher_adv19'),
                    ('Gerardo', 'Romero', 'teacher_adv20'),
                    ('Esperanza', 'Silva', 'teacher_adv21'),
                    ('Guillermo', 'Contreras', 'teacher_adv22'),
                    ('Rosario', 'Luna', 'teacher_adv23'),
                    ('Arturo', 'Guerrero', 'teacher_adv24'),
                    ('Catalina', 'Lara', 'teacher_adv25'),
                    ('Hector', 'Marin', 'teacher_adv26'),
                    ('Manuela', 'Paz', 'teacher_adv27'),
                    ('Ignacio', 'Cano', 'teacher_adv28'),
                    ('Josefina', 'Galvan', 'teacher_adv29'),
                    ('Salvador', 'Rojas', 'teacher_adv30')
                ]
                
                for first_name, last_name, username in advisory_teachers:
                    teacher = CustomUser.objects.create(
                        username=username,
                        email=f'{username}@protech.com',
                        first_name=first_name,
                        last_name=last_name,
                        role=UserRole.TEACHER,
                        is_staff=False,
                        is_active=True,
                        is_new=False,
                        section=None  # Will be assigned after sections are created
                    )
                    teacher.set_password(password)
                    teacher.save()
                    created_users.append(f'Advisory Teacher: {username}@protech.com')
                    self.stdout.write(self.style.SUCCESS(f'Created advisory teacher account: {teacher.username}'))
                
                self.stdout.write(self.style.SUCCESS('All user accounts created successfully!'))
                
                self.stdout.write("\nUser Accounts Summary:")
                self.stdout.write("======================")
                self.stdout.write(f"Password for all accounts: {password}")
                self.stdout.write("----------------------")
                for user_info in created_users:
                    self.stdout.write(user_info)
                self.stdout.write("----------------------")
                self.stdout.write(f"Total users created: {len(created_users)}")
                self.stdout.write("Note: Advisory teachers will be assigned to sections after sections are created.")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating user accounts: {str(e)}'))
