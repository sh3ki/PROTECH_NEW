from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from PROTECHAPP.models import CustomUser, Student, Section, Grade, Guardian, Attendance, UserRole

def is_registrar(user):
    """Check if the logged-in user is a registrar"""
    return user.is_authenticated and user.role == UserRole.REGISTRAR

@login_required
@user_passes_test(is_registrar)
def registrar_dashboard(request):
    """View for registrar dashboard"""
    current_date = timezone.now()
    
    # Example data for dashboard
    student_count = Student.objects.count()
    face_enrolled_count = Student.objects.filter(face_path__isnull=False).count()
    pending_enrollments = 42  # This would be calculated based on actual data
    
    face_enrolled_percentage = (face_enrolled_count / student_count * 100) if student_count > 0 else 0
    
    context = {
        'current_date': current_date,
        'student_count': student_count,
        'face_enrolled_count': face_enrolled_count,
        'face_enrolled_percentage': round(face_enrolled_percentage),
        'pending_enrollments': pending_enrollments
    }
    
    return render(request, 'registrar/dashboard.html', context)

@login_required
@user_passes_test(is_registrar)
def registrar_students(request):
    """View for student management"""
    students = Student.objects.all().select_related('grade', 'section')
    context = {
        'students': students
    }
    return render(request, 'registrar/students.html', context)

@login_required
@user_passes_test(is_registrar)
def registrar_face_enroll(request):
    """View for face enrollment"""
    students_without_face = Student.objects.filter(face_path__isnull=True)
    context = {
        'students': students_without_face
    }
    return render(request, 'registrar/face_enroll.html', context)

@login_required
@user_passes_test(is_registrar)
def registrar_guardians(request):
    """View for guardian management"""
    guardians = Guardian.objects.all().select_related('student')
    context = {
        'guardians': guardians
    }
    return render(request, 'registrar/guardians.html', context)

@login_required
@user_passes_test(is_registrar)
def registrar_grades_sections(request):
    """View for grades and sections management"""
    grades = Grade.objects.all()
    sections = Section.objects.all().select_related('grade')
    context = {
        'grades': grades,
        'sections': sections
    }
    return render(request, 'registrar/grades_sections.html', context)

@login_required
@user_passes_test(is_registrar)
def registrar_attendance(request):
    """View for attendance records"""
    today = timezone.now().date()
    attendance_records = Attendance.objects.filter(date=today).select_related('student')
    context = {
        'attendance_records': attendance_records
    }
    return render(request, 'registrar/attendance.html', context)

@login_required
@user_passes_test(is_registrar)
def registrar_excused(request):
    """View for excused absences"""
    return render(request, 'registrar/excused.html')

@login_required
@user_passes_test(is_registrar)
def registrar_announcements(request):
    """View for announcements"""
    return render(request, 'registrar/announcements.html')

@login_required
@user_passes_test(is_registrar)
def registrar_messages(request):
    """View for messages"""
    return render(request, 'registrar/messages.html')

@login_required
@user_passes_test(is_registrar)
def registrar_settings(request):
    """View for settings"""
    return render(request, 'registrar/settings.html')
