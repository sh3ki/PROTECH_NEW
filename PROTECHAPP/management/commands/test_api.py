from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import authenticate, login
from PROTECHAPP.models import CustomUser, UserRole
import json

class Command(BaseCommand):
    help = 'Test the admin sections API to check advisor data'

    def handle(self, *args, **options):
        self.stdout.write('=== TESTING ADMIN SECTIONS API ===')
        
        # Create a test client
        client = Client()
        
        # Login as admin
        admin_user = CustomUser.objects.filter(role=UserRole.ADMIN).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found'))
            return
            
        # Login
        client.force_login(admin_user)
        
        # Test the search_sections API
        response = client.get('/admin/sections/search/')
        
        if response.status_code == 200:
            data = response.json()
            self.stdout.write(f'API Response Status: Success')
            self.stdout.write(f'Total sections returned: {len(data.get("sections", []))}')
            
            # Show first few sections and their advisor data
            sections = data.get('sections', [])[:3]
            for i, section in enumerate(sections, 1):
                self.stdout.write(f'\nSection {i}:')
                self.stdout.write(f'  Name: {section.get("name")}')
                self.stdout.write(f'  Grade: {section.get("grade_name")}')
                self.stdout.write(f'  Advisor: {section.get("advisor")}')
                
                if section.get("advisor"):
                    advisor = section.get("advisor")
                    if isinstance(advisor, dict):
                        self.stdout.write(f'    Advisor Name: {advisor.get("name", "No name")}')
                        self.stdout.write(f'    Advisor ID: {advisor.get("id", "No ID")}')
                    else:
                        self.stdout.write(f'    Advisor (string): {advisor}')
        else:
            self.stdout.write(self.style.ERROR(f'API Error: {response.status_code}'))
            self.stdout.write(f'Response: {response.content.decode()}')