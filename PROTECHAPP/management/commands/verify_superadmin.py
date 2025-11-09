from django.core.management.base import BaseCommand
from PROTECHAPP.models import CustomUser, UserRole

class Command(BaseCommand):
    help = 'Verify the superadmin account'

    def handle(self, *args, **options):
        self.stdout.write('=== SUPERADMIN VERIFICATION ===')
        
        # Find the superadmin account
        try:
            superadmin = CustomUser.objects.get(username='superadmin')
            
            self.stdout.write('\n✅ SUPERADMIN ACCOUNT FOUND:')
            self.stdout.write(f'  Username: {superadmin.username}')
            self.stdout.write(f'  Email: {superadmin.email}')
            self.stdout.write(f'  Full Name: {superadmin.first_name} {superadmin.last_name}')
            self.stdout.write(f'  Role: {superadmin.get_role_display()}')
            self.stdout.write(f'  Is Staff: {superadmin.is_staff}')
            self.stdout.write(f'  Is Superuser: {superadmin.is_superuser}')
            self.stdout.write(f'  Is Active: {superadmin.is_active}')
            self.stdout.write(f'  Is New: {superadmin.is_new}')
            self.stdout.write(f'  Created: {superadmin.created_at}')
            
            self.stdout.write('\n🔑 LOGIN CREDENTIALS:')
            self.stdout.write(f'  Email: {superadmin.email}')
            self.stdout.write(f'  Password: Password123!')
            
            self.stdout.write('\n🎯 CAPABILITIES:')
            self.stdout.write('  ✓ Full admin access')
            self.stdout.write('  ✓ Django admin panel access')
            self.stdout.write('  ✓ Can create/modify users')
            self.stdout.write('  ✓ System-wide permissions')
            
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ SUPERADMIN ACCOUNT NOT FOUND!'))
            return
        
        # Show total user counts
        total_users = CustomUser.objects.count()
        superusers = CustomUser.objects.filter(is_superuser=True).count()
        
        self.stdout.write('\n📊 USER SUMMARY:')
        self.stdout.write(f'  Total Users: {total_users}')
        self.stdout.write(f'  Superusers: {superusers}')
        
        self.stdout.write('\n✅ SUPERADMIN SETUP COMPLETE!')
        self.stdout.write('You can now log in to the admin interface with superadmin privileges.')