from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

def landing_page(request):
    """Landing page with SELECT DEVICE and LOGIN buttons"""
    return render(request, 'landing_page.html')

def select_device(request):
    """Select device page with TIME IN and TIME OUT options"""
    return render(request, 'select_device.html')

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
