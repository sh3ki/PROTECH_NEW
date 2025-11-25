import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PROTECH.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import secrets
import string

# Generate test password
password_chars = string.ascii_letters + string.digits + '!@#$%^&*'
test_password = ''.join(secrets.choice(password_chars) for _ in range(12))
test_email = 'shekaigarcia@gmail.com'  # Replace with your test email
test_username = 'test_user'
test_name = 'Test User'

print("="*60)
print("TESTING USER REGISTRATION EMAIL")
print("="*60)
print(f"From: {settings.DEFAULT_FROM_EMAIL}")
print(f"To: {test_email}")
print(f"Username: {test_username}")
print(f"Password: {test_password}")
print("="*60)

subject = 'Your PROTECH Account Credentials'

# Plain text version
text_message = f'''Hello {test_name},

Your account has been created successfully for the PROTECH Attendance Monitoring System.

Your login credentials:
Username: {test_username}
Password: {test_password}

Please log in and change your password after your first login.

Login URL: http://localhost:8000/login/

Attendance Monitoring System PROTECH
'''

# HTML version
html_message = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your PROTECH Account Credentials</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #1a1a1a;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #1a1a1a; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #2a2a2a; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);">
                    <tr>
                        <td style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); padding: 30px; text-align: center;">
                            <h1 style="color: white; font-size: 24px; font-weight: bold; margin: 0;">Welcome to PROTECH</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px 40px;">
                            <h2 style="color: #ffffff; font-size: 18px; font-weight: 600; margin: 0 0 15px;">Your Account Credentials</h2>
                            <p style="color: #d1d5db; font-size: 14px; line-height: 1.6; margin: 0 0 10px;">Hello {test_name},</p>
                            <p style="color: #d1d5db; font-size: 14px; line-height: 1.6; margin: 0 0 25px;">Your account has been created successfully. Please use the following credentials to log in:</p>
                            
                            <div style="background-color: #1a1a1a; border: 2px solid #3f3f46; border-radius: 8px; padding: 20px; margin: 0 0 25px;">
                                <p style="color: #9ca3af; font-size: 13px; margin: 0 0 10px;">Username:</p>
                                <p style="color: #ffffff; font-size: 16px; font-weight: bold; margin: 0 0 20px; font-family: 'Courier New', monospace;">{test_username}</p>
                                <p style="color: #9ca3af; font-size: 13px; margin: 0 0 10px;">Password:</p>
                                <p style="color: #10b981; font-size: 18px; font-weight: bold; margin: 0; font-family: 'Courier New', monospace; letter-spacing: 1px;">{test_password}</p>
                            </div>
                            
                            <p style="color: #ef4444; font-size: 13px; line-height: 1.5; margin: 0 0 10px;"><strong>Important:</strong> Please change your password after your first login.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''

try:
    print("\nSending email...")
    msg = EmailMultiAlternatives(
        subject,
        text_message,
        settings.DEFAULT_FROM_EMAIL,
        [test_email]
    )
    msg.attach_alternative(html_message, "text/html")
    result = msg.send(fail_silently=False)
    
    print(f"\n✓ Email sent successfully! Result: {result}")
    print("\nCheck your inbox at:", test_email)
    
except Exception as e:
    print(f"\n✗ Failed to send email!")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    
    print("\n" + "="*60)
    print("TROUBLESHOOTING TIPS:")
    print("="*60)
    print("1. Check if EMAIL_HOST_PASSWORD has extra spaces")
    print("2. Verify the app password is correct (not your regular password)")
    print("3. Make sure 2-Step Verification is enabled on the Gmail account")
    print("4. Generate a new app password at:")
    print("   https://myaccount.google.com/apppasswords")
    print("5. Check for blocked sign-in attempts at:")
    print("   https://myaccount.google.com/notifications")
