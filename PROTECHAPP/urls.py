from django.shortcuts import render
from django.urls import path
from . import views

urlpatterns = [
    # Public routes
    path('', views.landing_page, name='landing_page'),
    path('select-device/', views.select_device, name='select_device'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Admin routes
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', lambda request: render(request, 'admin/users.html'), name='admin_users'),
    path('admin/teachers/', lambda request: render(request, 'admin/teachers.html'), name='admin_teachers'),
    path('admin/grades/', lambda request: render(request, 'admin/grades.html'), name='admin_grades'),
    path('admin/sections/', lambda request: render(request, 'admin/sections.html'), name='admin_sections'),
    path('admin/students/', lambda request: render(request, 'admin/students.html'), name='admin_students'),
    path('admin/guardians/', lambda request: render(request, 'admin/guardians.html'), name='admin_guardians'),
    path('admin/attendance/', lambda request: render(request, 'admin/attendance.html'), name='admin_attendance'),
    path('admin/excused/', lambda request: render(request, 'admin/excused.html'), name='admin_excused'),
    path('admin/settings/', lambda request: render(request, 'admin/settings.html'), name='admin_settings'),
    
    # Principal routes
    path('principal/dashboard/', views.principal_dashboard, name='principal_dashboard'),
    path('principal/teachers/', lambda request: render(request, 'principal/teachers.html'), name='principal_teachers'),
    path('principal/grades/', lambda request: render(request, 'principal/grades.html'), name='principal_grades'),
    path('principal/sections/', lambda request: render(request, 'principal/sections.html'), name='principal_sections'),
    path('principal/students/', lambda request: render(request, 'principal/students.html'), name='principal_students'),
    path('principal/guardians/', lambda request: render(request, 'principal/guardians.html'), name='principal_guardians'),
    path('principal/attendance/', lambda request: render(request, 'principal/attendance.html'), name='principal_attendance'),
    path('principal/excused/', lambda request: render(request, 'principal/excused.html'), name='principal_excused'),
    path('principal/announcements/', lambda request: render(request, 'principal/announcements.html'), name='principal_announcements'),
    path('principal/messages/', lambda request: render(request, 'principal/messages.html'), name='principal_messages'),
    path('principal/settings/', lambda request: render(request, 'principal/settings.html'), name='principal_settings'),
    
    # Registrar routes
    path('registrar/dashboard/', views.registrar_dashboard, name='registrar_dashboard'),
    path('registrar/students/', lambda request: render(request, 'registrar/students.html'), name='registrar_students'),
    path('registrar/face-enroll/', lambda request: render(request, 'registrar/face_enroll.html'), name='registrar_face_enroll'),
    path('registrar/guardians/', lambda request: render(request, 'registrar/guardians.html'), name='registrar_guardians'),
    path('registrar/grades-sections/', lambda request: render(request, 'registrar/grades_sections.html'), name='registrar_grades_sections'),
    path('registrar/attendance/', lambda request: render(request, 'registrar/attendance.html'), name='registrar_attendance'),
    path('registrar/excused/', lambda request: render(request, 'registrar/excused.html'), name='registrar_excused'),
    path('registrar/announcements/', lambda request: render(request, 'registrar/announcements.html'), name='registrar_announcements'),
    path('registrar/messages/', lambda request: render(request, 'registrar/messages.html'), name='registrar_messages'),
    path('registrar/settings/', lambda request: render(request, 'registrar/settings.html'), name='registrar_settings'),
    
    # Advisory Teacher routes
    path('teacher/advisory/dashboard/', views.teacher_advisory_dashboard, name='teacher_advisory_dashboard'),
    path('teacher/advisory/students/', lambda request: render(request, 'teacher/advisory/students.html'), name='teacher_advisory_students'),
    path('teacher/advisory/attendance/', lambda request: render(request, 'teacher/advisory/attendance.html'), name='teacher_advisory_attendance'),
    path('teacher/advisory/excused/', lambda request: render(request, 'teacher/advisory/excused.html'), name='teacher_advisory_excused'),
    path('teacher/advisory/messages/', lambda request: render(request, 'teacher/advisory/messages.html'), name='teacher_advisory_messages'),
    path('teacher/advisory/settings/', lambda request: render(request, 'teacher/advisory/settings.html'), name='teacher_advisory_settings'),
    
    # Non-Advisory Teacher routes
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/students/', lambda request: render(request, 'teacher/students.html'), name='teacher_students'),
    path('teacher/guardians/', lambda request: render(request, 'teacher/guardians.html'), name='teacher_guardians'),
    path('teacher/attendance/', lambda request: render(request, 'teacher/attendance.html'), name='teacher_attendance'),
    path('teacher/excused/', lambda request: render(request, 'teacher/excused.html'), name='teacher_excused'),
    path('teacher/messages/', lambda request: render(request, 'teacher/messages.html'), name='teacher_messages'),
    path('teacher/settings/', lambda request: render(request, 'teacher/settings.html'), name='teacher_settings'),
]
