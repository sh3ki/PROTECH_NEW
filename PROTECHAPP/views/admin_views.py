from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from PROTECHAPP.models import CustomUser, Student, Section, Grade, Guardian, Attendance, UserRole

def is_admin(user):
    """Check if the logged-in user is an admin"""
    return user.is_authenticated and user.role == UserRole.ADMIN

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """View for admin dashboard"""
    context = {
        'current_date': timezone.now(),
        'user_count': CustomUser.objects.count(),
        'student_count': Student.objects.count(),
        'teacher_count': CustomUser.objects.filter(role=UserRole.TEACHER).count(),
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_users(request):
    """View for user management"""
    users = CustomUser.objects.all()
    context = {
        'users': users
    }
    return render(request, 'admin/users.html', context)

@login_required
@user_passes_test(is_admin)
def admin_teachers(request):
    """View for teacher management"""
    teachers = CustomUser.objects.filter(role=UserRole.TEACHER)
    context = {
        'teachers': teachers
    }
    return render(request, 'admin/teachers.html', context)

@login_required
@user_passes_test(is_admin)
def admin_grades(request):
    """View for grade management"""
    grades = Grade.objects.all()
    context = {
        'grades': grades
    }
    return render(request, 'admin/grades.html', context)

@login_required
@user_passes_test(is_admin)
def admin_sections(request):
    """View for section management"""
    sections = Section.objects.all()
    context = {
        'sections': sections
    }
    return render(request, 'admin/sections.html', context)

@login_required
@user_passes_test(is_admin)
def admin_students(request):
    """View for student management"""
    students = Student.objects.all()
    context = {
        'students': students
    }
    return render(request, 'admin/students.html', context)

@login_required
@user_passes_test(is_admin)
def admin_guardians(request):
    """View for guardian management"""
    guardians = Guardian.objects.all()
    context = {
        'guardians': guardians
    }
    return render(request, 'admin/guardians.html', context)

@login_required
@user_passes_test(is_admin)
def admin_attendance(request):
    """View for attendance management"""
    today = timezone.now().date()
    attendance_records = Attendance.objects.filter(date=today)
    context = {
        'attendance_records': attendance_records
    }
    return render(request, 'admin/attendance.html', context)

@login_required
@user_passes_test(is_admin)
def admin_settings(request):
    """View for system settings"""
    return render(request, 'admin/settings.html')
