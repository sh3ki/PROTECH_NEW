#!/usr/bin/env python
"""
Quick script to check existing user emails in the database
Run this to verify what emails are actually stored in the CustomUser table
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')
django.setup()

from PROTECHAPP.models import CustomUser

print("\n" + "="*60)
print("CHECKING USER EMAILS IN DATABASE")
print("="*60 + "\n")

users = CustomUser.objects.all()

if not users:
    print("⚠️  No users found in database!")
else:
    print(f"Found {users.count()} users:\n")
    for user in users:
        print(f"  • Username: {user.username}")
        print(f"    Email: {user.email}")
        print(f"    Name: {user.get_full_name() or 'N/A'}")
        print(f"    Role: {user.get_role_display()}")
        print(f"    Active: {user.is_active}")
        print()

print("="*60)
print("\nTo test password reset, use one of the emails listed above.")
print("="*60 + "\n")
