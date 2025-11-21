import smtplib
from email.mime.text import MIMEText

# Test with SSL (port 465) instead of TLS (port 587)
email_host = 'smtp.gmail.com'
email_port = 465  # SSL port
email_user = 'protech.management.official@gmail.com'
email_password = 'rhbyldsrvgcrgpum'  # Current password from .env

print("=" * 50)
print("Testing Gmail SMTP with SSL (port 465)")
print("=" * 50)
print(f"Host: {email_host}")
print(f"Port: {email_port}")
print(f"User: {email_user}")
print(f"Password: {email_password[:4]}****")
print("=" * 50)

try:
    # Use SMTP_SSL for port 465
    server = smtplib.SMTP_SSL(email_host, email_port)
    server.ehlo()
    print("✓ Connected to SMTP server")
    
    # Try login
    print(f"Attempting login...")
    server.login(email_user, email_password)
    print("✓ Login successful!")
    
    # Send test email
    msg = MIMEText('Test email body')
    msg['Subject'] = 'Test from Protech'
    msg['From'] = email_user
    msg['To'] = 'shekaigarcia@gmail.com'
    
    server.send_message(msg)
    print("✓ Email sent successfully!")
    server.quit()
    
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {str(e)}")
