from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from ..models import PasswordResetOTP
import json
import random
from datetime import datetime, timedelta

def landing_page(request):
    """Landing page with SELECT DEVICE and LOGIN buttons"""
    return render(request, 'landing_page.html')

def select_device(request):
    """Select device page with TIME IN and TIME OUT options"""
    from PROTECHAPP.models import SystemSettings
    
    # Get system settings to determine attendance mode
    try:
        settings_obj = SystemSettings.objects.get(pk=1)
        attendance_mode = settings_obj.attendance_mode
    except SystemSettings.DoesNotExist:
        attendance_mode = 'SEPARATE'  # Default to separate mode
    
    context = {
        'attendance_mode': attendance_mode
    }
    return render(request, 'select_device.html', context)

def login_view(request):
    """Login page without registration"""
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        # First try authenticating with the input as username
        user = authenticate(request, username=username_or_email, password=password)
        
        # If that fails, check if it's an email
        if user is None:
            User = get_user_model()
            try:
                # Find user with the provided email
                user_obj = User.objects.get(email=username_or_email)
                # If found, authenticate with their username
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        
        if user is not None:
            # For first-time login, require OTP verification before allowing password change
            if user.is_new:
                # Do NOT call login() yet; instead store the username in session and redirect to verification
                request.session['first_time_login'] = True
                request.session['first_time_username'] = user.username
                request.session['user_full_name'] = user.get_full_name() or user.username
                messages.info(request, 'First time login detected. Please verify your account to proceed.')
                return redirect('first_time_verify')

            # Normal login flow for non-first-time users
            login(request, user)
            messages.success(request, 'Login successful!')

            # Redirect based on user role
            if user.role == 'ADMIN':
                return redirect('admin_dashboard')
            elif user.role == 'PRINCIPAL':
                return redirect('principal_dashboard')
            elif user.role == 'REGISTRAR':
                return redirect('registrar_dashboard')
            elif user.role == 'TEACHER':
                # Check if teacher is advisory (has section assigned)
                if user.section:
                    return redirect('teacher_advisory_dashboard')
                else:
                    return redirect('teacher_non_advisory_dashboard')
            else:
                return redirect('landing_page')
        else:
            messages.error(request, 'Invalid username, email or password.')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing_page')

@csrf_exempt
@require_http_methods(["POST"])
def send_verification_code(request):
    """Send a 6-digit verification code to the user's email"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'}, status=400)
        
        # Check if user with this email exists (case-insensitive search)
        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Log for debugging
            print(f"No user found with email: {email}")
            return JsonResponse({'success': False, 'message': 'No account found with this email address'}, status=404)

        # Allow sending OTP for password reset or first-time verification.
        # If the account is neither verified nor a newly created account, disallow automatic email OTP.
        if not (getattr(user, 'is_verified', False) or getattr(user, 'is_new', False)):
            return JsonResponse({'success': False, 'message': 'Account is not eligible for email OTP. Please contact the administrator.'}, status=403)
        
        # Generate 6-digit verification code
        code = str(random.randint(100000, 999999))
        
        # Get client IP address
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if ip_address:
            ip_address = ip_address.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR', '')
        
        # Invalidate any existing unused codes for this email
        PasswordResetOTP.objects.filter(email=email, is_used=False).update(is_used=True)
        
        # Store code in database with expiration time (10 minutes)
        PasswordResetOTP.objects.create(
            email=email,
            otp_code=code,
            expires_at=timezone.now() + timedelta(minutes=10),
            ip_address=ip_address
        )
        
        print(f"Verification code generated for {email}: {code}")
        
        # Send email
        try:
            subject = 'Password Reset Verification Code'
            
            # Plain text version
            text_message = f'''
Hello {user.get_full_name() or user.username},

We received a request to reset your password. Your verification code is:

{code}

This code will expire in 10 minutes.

If you didn't request this, please ignore this message.

Attendance Monitoring System PROTECH
'''
            
            # HTML version with modern dark design
            html_message = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset Verification Code</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #1a1a1a;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #1a1a1a; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #2a2a2a; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);">
                    <!-- Header with icon -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); padding: 30px; text-align: center;">
                            <div style="background-color: rgba(255, 255, 255, 0.2); width: 60px; height: 60px; border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center;">
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                                    <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                                </svg>
                            </div>
                            <h1 style="color: white; font-size: 24px; font-weight: bold; margin: 0; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">Password Reset Verification Code</h1>
                        </td>
                    </tr>
                    
                    <!-- Badge -->
                    <tr>
                        <td style="padding: 20px 40px 0;">
                            <div style="background-color: #10b981; color: white; display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Inbox</div>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <h2 style="color: #ffffff; font-size: 18px; font-weight: 600; margin: 0 0 15px;">Password Reset Request</h2>
                            <p style="color: #d1d5db; font-size: 14px; line-height: 1.6; margin: 0 0 10px;">Hello {user.get_full_name() or user.username},</p>
                            <p style="color: #d1d5db; font-size: 14px; line-height: 1.6; margin: 0 0 25px;">We received a request to reset your password. Your verification code is:</p>
                            
                            <!-- Verification Code Box -->
                            <div style="background-color: #1a1a1a; border: 2px solid #3f3f46; border-radius: 8px; padding: 20px; text-align: center; margin: 0 0 25px;">
                                <div style="color: #ffffff; font-size: 36px; font-weight: bold; letter-spacing: 8px; font-family: 'Courier New', monospace;">{code}</div>
                            </div>
                            
                            <p style="color: #9ca3af; font-size: 13px; line-height: 1.5; margin: 0 0 10px;">This code will expire in <strong style="color: #ef4444;">10 minutes</strong>.</p>
                            <p style="color: #9ca3af; font-size: 13px; line-height: 1.5; margin: 0;">If you didn't request this, please ignore this message.</p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px 30px; border-top: 1px solid #3f3f46;">
                            <p style="color: #6b7280; font-size: 12px; margin: 0; line-height: 1.5;">Attendance Monitoring System PROTECH</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
'''
            
            from django.core.mail import EmailMultiAlternatives
            
            msg = EmailMultiAlternatives(
                subject,
                text_message,
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send(fail_silently=False)
            
            return JsonResponse({'success': True, 'message': 'Verification code sent to your email'})
        except Exception as e:
            print(f"Email send error: {e}")
            return JsonResponse({'success': False, 'message': 'Failed to send email. Please try again later.'}, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request data'}, status=400)
    except Exception as e:
        print(f"Error in send_verification_code: {e}")
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def verify_code(request):
    """Verify the code entered by the user"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        
        if not email or not code:
            return JsonResponse({'success': False, 'message': 'Email and code are required'}, status=400)
        
        # Check if code exists for this email
        try:
            otp = PasswordResetOTP.objects.filter(
                email=email,
                otp_code=code,
                is_used=False
            ).latest('created_at')
        except PasswordResetOTP.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid verification code. Please try again.'}, status=400)
        
        # Check if code has expired
        if otp.is_expired():
            return JsonResponse({'success': False, 'message': 'Verification code has expired. Please request a new code.'}, status=400)
        
        return JsonResponse({'success': True, 'message': 'Code verified successfully'})
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request data'}, status=400)
    except Exception as e:
        print(f"Error in verify_code: {e}")
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def reset_password(request):
    """Reset the user's password after verification"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        new_password = data.get('new_password', '')
        
        if not email or not code or not new_password:
            return JsonResponse({'success': False, 'message': 'All fields are required'}, status=400)
        
        # Verify code one more time
        try:
            otp = PasswordResetOTP.objects.filter(
                email=email,
                otp_code=code,
                is_used=False
            ).latest('created_at')
        except PasswordResetOTP.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid or expired verification session'}, status=400)
        
        # Check if expired
        if otp.is_expired():
            return JsonResponse({'success': False, 'message': 'Verification session expired'}, status=400)
        
        # Reset password
        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
            user.set_password(new_password)
            user.save()
            
            # Mark the OTP as used
            otp.is_used = True
            otp.save()
            
            return JsonResponse({'success': True, 'message': 'Password reset successfully'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request data'}, status=400)
    except Exception as e:
        print(f"Error in reset_password: {e}")
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'}, status=500)


def first_time_verify(request):
    """Render a simple page to handle first-time OTP verification and password setup."""
    # If no first_time_login in session, redirect to login
    if not request.session.get('first_time_login'):
        return redirect('login')

    username = request.session.get('first_time_username')
    # Try to get the user's email to prefill the form (more reliable UX)
    email = ''
    if username:
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            email = user.email or ''
        except User.DoesNotExist:
            email = ''

    return render(request, 'first_time_verify.html', {'username': username, 'email': email})

@csrf_exempt
@require_http_methods(["POST"])
def change_first_time_password(request):
    """Handle password change for first-time login users.

    This endpoint requires a valid OTP code for the user's email (or the email associated
    with the `first_time_username` saved in session). After successful OTP verification,
    the user's password is updated, `is_new` is cleared, `is_verified` is set True, and
    the user is logged in.
    """
    try:
        data = json.loads(request.body)
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        code = data.get('code', '').strip()

        # Validation
        if not new_password or not confirm_password or not code:
            return JsonResponse({'success': False, 'message': 'Password and verification code are required'}, status=400)

        if new_password != confirm_password:
            return JsonResponse({'success': False, 'message': 'Passwords do not match'}, status=400)

        if len(new_password) < 8:
            return JsonResponse({'success': False, 'message': 'Password must be at least 8 characters long'}, status=400)

        # Identify username/email from session
        username = request.session.get('first_time_username')
        if not username:
            return JsonResponse({'success': False, 'message': 'Session expired. Please login again.'}, status=400)

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found. Please contact administrator.'}, status=404)

        email = (user.email or '').strip().lower()

        # Verify OTP
        try:
            otp = PasswordResetOTP.objects.filter(
                email__iexact=email,
                otp_code=code,
                is_used=False
            ).latest('created_at')
        except PasswordResetOTP.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid or expired verification code'}, status=400)

        if otp.is_expired():
            return JsonResponse({'success': False, 'message': 'Verification code has expired. Please request a new code.'}, status=400)

        # All good: update password and flags
        user.set_password(new_password)
        user.is_new = False
        user.is_verified = True
        user.save()

        # Mark OTP as used
        otp.is_used = True
        otp.save()

        # Log the user in
        login(request, user)

        # Clear session flags
        request.session.pop('first_time_login', None)
        request.session.pop('first_time_username', None)
        request.session.pop('user_full_name', None)

        # Determine redirect URL based on user role
        redirect_url = '/dashboard/'
        if user.role == 'ADMIN':
            redirect_url = '/admin/dashboard/'
        elif user.role == 'PRINCIPAL':
            redirect_url = '/principal/dashboard/'
        elif user.role == 'REGISTRAR':
            redirect_url = '/registrar/dashboard/'
        elif user.role == 'TEACHER':
            if user.section:
                redirect_url = '/teacher/advisory/dashboard/'
            else:
                redirect_url = '/teacher/non-advisory/dashboard/'

        return JsonResponse({
            'success': True,
            'message': 'Password changed and account verified successfully. Redirecting...',
            'redirect_url': redirect_url
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request data'}, status=400)
    except Exception as e:
        print(f"Error in change_first_time_password: {e}")
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'}, status=500)
