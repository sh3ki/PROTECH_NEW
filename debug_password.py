import os
from decouple import config

# Load the password directly from .env
password = config('EMAIL_HOST_PASSWORD', default='')

print("Password Analysis:")
print(f"Length: {len(password)}")
print(f"Raw value: '{password}'")
print(f"Repr: {repr(password)}")
print(f"Bytes: {password.encode('utf-8')}")
print(f"Characters: {[c for c in password]}")

# Test if it matches expected values
without_spaces = password.replace(' ', '')
print(f"\nWithout spaces: '{without_spaces}' (length: {len(without_spaces)})")

# Try both versions
import smtplib

email_user = 'protech.management.official@gmail.com'

print("\n" + "="*50)
print("Test 1: With spaces as-is from .env")
print("="*50)
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_user, password)
    print("✓ SUCCESS with spaces!")
    server.quit()
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n" + "="*50)
print("Test 2: Without spaces")
print("="*50)
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_user, without_spaces)
    print("✓ SUCCESS without spaces!")
    server.quit()
except Exception as e:
    print(f"✗ Failed: {e}")

# Manually test with hardcoded password
print("\n" + "="*50)
print("Test 3: Hardcoded password without spaces")
print("="*50)
hardcoded = 'rhbyldsrvgcrgpum'
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_user, hardcoded)
    print("✓ SUCCESS with hardcoded!")
    server.quit()
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n" + "="*50)
print("Test 4: Hardcoded password WITH spaces")
print("="*50)
hardcoded_spaces = 'rhby ldsr vgcr gpum'
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_user, hardcoded_spaces)
    print("✓ SUCCESS with hardcoded spaces!")
    server.quit()
except Exception as e:
    print(f"✗ Failed: {e}")
