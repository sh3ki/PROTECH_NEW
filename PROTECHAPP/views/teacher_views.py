from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from PROTECHAPP.models import CustomUser, Student, Attendance, Guardian, UserRole

def is_teacher(user):
    """Check if the logged-in user is a teacher"""
    return user.is_authenticated and user.role == UserRole.TEACHER

@login_required
@user_passes_test(is_teacher)
def teacher_dashboard(request):
    """View for teacher dashboard"""
    # Retrieve today's date for the dashboard
    current_date = timezone.now()
    
    # Example data that might be needed for a teacher's dashboard
    today_attendance_percentage = 96  # This would come from a database query
    
    context = {
        'current_date': current_date,
        'today_attendance_percentage': today_attendance_percentage
    }
    
    return render(request, 'teacher/non_advisory/dashboard.html', context)

@login_required
@user_passes_test(is_teacher)
def teacher_students(request):
    """View for students listing"""
    students = Student.objects.all()
    context = {
        'students': students
    }
    return render(request, 'teacher/students.html', context)

@login_required
@user_passes_test(is_teacher)
def teacher_guardians(request):
    """View for guardians listing"""
    guardians = Guardian.objects.all()
    context = {
        'guardians': guardians
    }
    return render(request, 'teacher/guardians.html', context)

@login_required
@user_passes_test(is_teacher)
def teacher_attendance(request):
    """View for attendance records"""
    today = timezone.now().date()
    attendance_records = Attendance.objects.filter(date=today)
    context = {
        'attendance_records': attendance_records
    }
    return render(request, 'teacher/attendance.html', context)

@login_required
@user_passes_test(is_teacher)
def teacher_excused(request):
    """View for excused absences"""
    return render(request, 'teacher/excused.html')

@login_required
@user_passes_test(is_teacher)
def teacher_messages(request):
    """View for messages"""
    return render(request, 'teacher/messages.html')

@login_required
@user_passes_test(is_teacher)
def teacher_settings(request):
    """View for settings"""
    return render(request, 'teacher/settings.html')
