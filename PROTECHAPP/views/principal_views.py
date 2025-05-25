from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from PROTECHAPP.models import CustomUser, Student, Section, Grade, Guardian, Attendance, UserRole

def is_principal(user):
    """Check if the logged-in user is a principal"""
    return user.is_authenticated and user.role == UserRole.PRINCIPAL

@login_required
@user_passes_test(is_principal)
def principal_dashboard(request):
    """View for principal dashboard"""
    current_date = timezone.now()
    
    # Example data for dashboard
    attendance_rate = 94.8
    student_count = Student.objects.count()
    teacher_count = CustomUser.objects.filter(role=UserRole.TEACHER).count()
    
    context = {
        'current_date': current_date,
        'attendance_rate': attendance_rate,
        'student_count': student_count,
        'teacher_count': teacher_count
    }
    
    return render(request, 'principal/dashboard.html', context)

@login_required
@user_passes_test(is_principal)
def principal_teachers(request):
    """View for teacher management"""
    teachers = CustomUser.objects.filter(role=UserRole.TEACHER)
    context = {
        'teachers': teachers
    }
    return render(request, 'principal/teachers.html', context)

@login_required
@user_passes_test(is_principal)
def principal_grades(request):
    """View for grade management"""
    grades = Grade.objects.all()
    context = {
        'grades': grades
    }
    return render(request, 'principal/grades.html', context)

@login_required
@user_passes_test(is_principal)
def principal_sections(request):
    """View for section management"""
    sections = Section.objects.all().select_related('grade')
    context = {
        'sections': sections
    }
    return render(request, 'principal/sections.html', context)

@login_required
@user_passes_test(is_principal)
def principal_students(request):
    """View for student management"""
    students = Student.objects.all().select_related('grade', 'section')
    context = {
        'students': students
    }
    return render(request, 'principal/students.html', context)

@login_required
@user_passes_test(is_principal)
def principal_guardians(request):
    """View for guardian management"""
    guardians = Guardian.objects.all().select_related('student')
    context = {
        'guardians': guardians
    }
    return render(request, 'principal/guardians.html', context)

@login_required
@user_passes_test(is_principal)
def principal_attendance(request):
    """View for attendance records"""
    today = timezone.now().date()
    attendance_records = Attendance.objects.filter(date=today).select_related('student')
    context = {
        'attendance_records': attendance_records
    }
    return render(request, 'principal/attendance.html', context)

@login_required
@user_passes_test(is_principal)
def principal_excused(request):
    """View for excused absences"""
    return render(request, 'principal/excused.html')

@login_required
@user_passes_test(is_principal)
def principal_announcements(request):
    """View for announcements"""
    return render(request, 'principal/announcements.html')

@login_required
@user_passes_test(is_principal)
def principal_messages(request):
    """View for messages"""
    return render(request, 'principal/messages.html')

@login_required
@user_passes_test(is_principal)
def principal_settings(request):
    """View for settings"""
    return render(request, 'principal/settings.html')
