from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def landing_page(request):
    """Landing page with SELECT DEVICE and LOGIN buttons"""
    return render(request, 'landing_page.html')

def select_device(request):
    """Select device page with TIME IN and TIME OUT options"""
    return render(request, 'select_device.html')

def login_view(request):
    """Login page without registration"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
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
                    return redirect('teacher_dashboard')
            else:
                return redirect('landing_page')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing_page')

# Admin views
@login_required
def admin_dashboard(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied: You do not have permission to view this page.')
        return redirect('landing_page')
    
    return render(request, 'admin/dashboard.html')

# Principal views
@login_required
def principal_dashboard(request):
    if request.user.role != 'PRINCIPAL':
        messages.error(request, 'Access denied: You do not have permission to view this page.')
        return redirect('landing_page')
    
    return render(request, 'principal/dashboard.html')

# Registrar views
@login_required
def registrar_dashboard(request):
    if request.user.role != 'REGISTRAR':
        messages.error(request, 'Access denied: You do not have permission to view this page.')
        return redirect('landing_page')
    
    return render(request, 'registrar/dashboard.html')

# Teacher views
@login_required
def teacher_advisory_dashboard(request):
    if request.user.role != 'TEACHER' or not request.user.section:
        messages.error(request, 'Access denied: You do not have permission to view this page.')
        return redirect('landing_page')
    
    return render(request, 'teacher/advisory/dashboard.html')

@login_required
def teacher_dashboard(request):
    if request.user.role != 'TEACHER' or request.user.section:
        messages.error(request, 'Access denied: You do not have permission to view this page.')
        return redirect('landing_page')
    
    return render(request, 'teacher/non_advisory/dashboard.html')
