# Email Configuration for Password Reset

## Overview
The password reset functionality uses email to send verification codes to users. The system supports both development and production email configurations.

## Development Setup (Console Backend)
By default, the system uses Django's console email backend, which prints emails to the terminal/console instead of sending them. This is useful for development and testing.

**Configuration in `.env`:**
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

**Testing:**
1. Click "Forgot Password?" on the login page
2. Enter a user's email address
3. Click "Send Verification Code"
4. Check the terminal/console where Django is running - you'll see the verification code printed there
5. Copy the 6-digit code and enter it in the verification form

## Production Setup (Gmail SMTP)

### Step 1: Enable App-Specific Passwords
1. Go to your Google Account settings
2. Navigate to Security
3. Enable 2-Factor Authentication if not already enabled
4. Go to "App passwords" or search for it in settings
5. Generate a new app password for "Mail" and "Other (Custom name)"
6. Copy the 16-character password

### Step 2: Configure .env File
Update your `.env` file with these settings:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=PROTECH Attendance System <your-email@gmail.com>
```

### Step 3: Restart Django Server
After updating the `.env` file, restart your Django development server for the changes to take effect.

## Other Email Providers

### Microsoft Outlook/Office 365
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
```

### Custom SMTP Server
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-domain.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@your-domain.com
EMAIL_HOST_PASSWORD=your-password
```

## Testing the Password Reset Flow

1. **Request Code:**
   - Go to login page
   - Click "Forgot Password?"
   - Enter registered email address
   - Click "Send Verification Code"

2. **Verify Code:**
   - Check email (or console in development mode)
   - Enter the 6-digit code
   - Click "VERIFY CODE"

3. **Reset Password:**
   - Enter new password (minimum 8 characters)
   - Confirm new password
   - Click "Reset Password"

4. **Login:**
   - Return to login page
   - Use new password to login

## Security Notes

- Verification codes expire after 10 minutes
- Codes are stored in memory (consider using Redis or database cache for production)
- Never commit `.env` file with real credentials to version control
- Use app-specific passwords, not your main email password
- Ensure EMAIL_HOST_PASSWORD is kept secret

## Troubleshooting

**Issue: Emails not sending**
- Verify email settings in `.env`
- Check if 2FA is enabled for Gmail
- Confirm app password is correct (no spaces)
- Check Django console for error messages

**Issue: "No account found" error**
- Ensure the email address is registered in the database
- Check CustomUser model has correct email field

**Issue: "Verification code expired"**
- Code is valid for 10 minutes
- Request a new code if expired

**Issue: Console backend not showing emails**
- Verify EMAIL_BACKEND is set to console backend
- Check terminal/console where `python manage.py runserver` is running
