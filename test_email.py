import os
import django
import smtplib
from email.mime.text import MIMEText

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

# Print current email settings
print("=" * 50)
print("CURRENT EMAIL SETTINGS:")
print("=" * 50)
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_HOST_PASSWORD length: {len(settings.EMAIL_HOST_PASSWORD)} chars")
print(f"EMAIL_HOST_PASSWORD (first 4 chars): {settings.EMAIL_HOST_PASSWORD[:4]}****")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print("=" * 50)

# Test 1: Direct SMTP connection (without Django)
print("\n[TEST 1] Direct SMTP connection test...")
try:
    server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    print("✓ Connected to SMTP server")
    
    # Try login
    print(f"Attempting login with: {settings.EMAIL_HOST_USER}")
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    print("✓ Login successful!")
    server.quit()
    
    # Test 2: Send email via Django
    print("\n[TEST 2] Sending email via Django...")
    result = send_mail(
        'Test Email from Protech',
        'This is a test email from Protech Management System.',
        settings.DEFAULT_FROM_EMAIL,
        ['shekaigarcia@gmail.com'],  # Replace with actual recipient
        fail_silently=False,
    )
    print(f"✓ Email sent successfully! Result: {result}")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"✗ Authentication failed: {e}")
    print("\nPossible issues:")
    print("1. The app password might be incorrect or expired")
    print("2. The app password might contain extra spaces - check the .env file")
    print("3. Try generating a completely new app password")
    print("4. Check https://myaccount.google.com/notifications for blocked sign-ins")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {str(e)}")
