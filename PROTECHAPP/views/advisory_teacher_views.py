from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from PROTECHAPP.models import CustomUser, Student, Attendance, Guardian, UserRole, Section

def is_advisory_teacher(user):
    """Check if the logged-in user is an advisory teacher"""
    return user.is_authenticated and user.role == UserRole.TEACHER and user.section is not None

@login_required
@user_passes_test(is_advisory_teacher)
def teacher_advisory_dashboard(request):
    """View for advisory teacher dashboard"""
    # Get current class attendance statistics
    current_date = timezone.now()
    section = request.user.section
    
    # Get students in the teacher's advisory class
    students_in_section = Student.objects.filter(section=section).count() if section else 0
    
    # Example data for dashboard
    attendance_percentage = 96  # This would come from a database query
    
    context = {
        'current_date': current_date,
        'students_count': students_in_section,
        'attendance_percentage': attendance_percentage
    }
    
    return render(request, 'teacher/advisory/dashboard.html', context)

@login_required
@user_passes_test(is_advisory_teacher)
def teacher_advisory_students(request):
    """View for advisory students listing"""
    section = request.user.section
    students = Student.objects.filter(section=section) if section else []
    
    context = {
        'students': students,
        'section': section
    }
    return render(request, 'teacher/advisory/students.html', context)

@login_required
@user_passes_test(is_advisory_teacher)
def teacher_advisory_attendance(request):
    """View for advisory class attendance records"""
    section = request.user.section
    today = timezone.now().date()
    
    # Get attendance records for students in teacher's section
    attendance_records = Attendance.objects.filter(
        student__section=section,
        date=today
    ) if section else []
    
    context = {
        'attendance_records': attendance_records,
        'section': section
    }
    return render(request, 'teacher/advisory/attendance.html', context)

@login_required
@user_passes_test(is_advisory_teacher)
def teacher_advisory_excused(request):
    """View for excused absences for advisory class"""
    return render(request, 'teacher/advisory/excused.html')

@login_required
@user_passes_test(is_advisory_teacher)
def teacher_advisory_messages(request):
    """View for advisory messages"""
    return render(request, 'teacher/advisory/messages.html')

@login_required
@user_passes_test(is_advisory_teacher)
def teacher_advisory_settings(request):
    """View for advisory settings"""
    return render(request, 'teacher/advisory/settings.html')
