from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from PROTECHAPP.views import admin_views, advisory_teacher_views, non_advisory_teacher_views, registrar_views, principal_views, public_views

urlpatterns = [
    # Public routes
    path('', public_views.landing_page, name='landing_page'),
    path('select-device/', public_views.select_device, name='select_device'),
    path('login/', public_views.login_view, name='login'),
    path('logout/', public_views.logout_view, name='logout'),

    # admin/users routes
    path('admin/users/', admin_views.admin_users, name='admin_users'),
    path('admin/users/create/', admin_views.create_user, name='admin_create_user'),
    path('admin/users/<int:user_id>/', admin_views.get_user, name='admin_get_user'),
    path('admin/users/<int:user_id>/update/', admin_views.update_user, name='admin_update_user'),
    path('admin/users/<int:user_id>/delete/', admin_views.delete_user, name='admin_delete_user'),
    path('admin/users/<int:user_id>/reset-password/', admin_views.reset_user_password, name='admin_reset_user_password'),
    path('admin/users/upload-profile-pic/', admin_views.upload_profile_pic, name='admin_upload_profile_pic'),
    path('profile-pics/<path:path>/', admin_views.serve_profile_pic, name='serve_profile_pic'),
    path('admin/users/search/', admin_views.search_users, name='admin_search_users'),

    #admin/teachers routes  
    path('admin/teachers/', admin_views.admin_teachers, name='admin_teachers'),
    path('admin/teachers/search/', admin_views.search_teachers, name='admin_search_teachers'),
    path('admin/teachers/assign-section/', admin_views.assign_teacher_section, name='assign_teacher_section'),
    path('admin/teachers/remove-section/', admin_views.remove_teacher_section, name='remove_teacher_section'),
    
    
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/students/', admin_views.admin_students, name='admin_students'),
    path('admin/guardians/', admin_views.admin_guardians, name='admin_guardians'),
    path('admin/grades/', admin_views.admin_grades, name='admin_grades'),
    path('admin/sections/', admin_views.admin_sections, name='admin_sections'),
    path('admin/attendance/', admin_views.admin_attendance, name='admin_attendance'),
    path('admin/excused/', admin_views.admin_excused, name='admin_excused'),
    path('admin/settings/', admin_views.admin_settings, name='admin_settings'),

    # Principal routes
    path('principal/dashboard/', principal_views.principal_dashboard, name='principal_dashboard'),
    path('principal/teachers/', principal_views.principal_teachers, name='principal_teachers'),
    path('principal/students/', principal_views.principal_students, name='principal_students'),
    path('principal/guardians/', principal_views.principal_guardians, name='principal_guardians'),
    path('principal/grades&sections/', principal_views.principal_grades, name='principal_grades_sections'),
    path('principal/attendance/', principal_views.principal_attendance, name='principal_attendance'),
    path('principal/excused/', principal_views.principal_excused, name='principal_excused'),
    path('principal/announcements/', principal_views.principal_announcements, name='principal_announcements'),
    path('principal/messages/', principal_views.principal_messages, name='principal_messages'),
    path('principal/settings/', principal_views.principal_settings, name='principal_settings'),
    
    # Registrar routes
    path('registrar/dashboard/', registrar_views.registrar_dashboard, name='registrar_dashboard'),
    path('registrar/students/', registrar_views.registrar_students, name='registrar_students'),
    path('registrar/face-enroll/', registrar_views.registrar_face_enroll, name='registrar_face_enroll'),
    path('registrar/guardians/', registrar_views.registrar_guardians, name='registrar_guardians'),
    path('registrar/grades-sections/', registrar_views.registrar_grades_sections, name='registrar_grades_sections'),
    path('registrar/attendance/', registrar_views.registrar_attendance, name='registrar_attendance'),
    path('registrar/excused/', registrar_views.registrar_excused, name='registrar_excused'),
    path('registrar/announcements/', registrar_views.registrar_announcements, name='registrar_announcements'),
    path('registrar/messages/', registrar_views.registrar_messages, name='registrar_messages'),
    path('registrar/settings/', registrar_views.registrar_settings, name='registrar_settings'), 
    
    # Advisory Teacher routes
    path('teacher/advisory/dashboard/', advisory_teacher_views.teacher_advisory_dashboard, name='teacher_advisory_dashboard'),
    path('teacher/advisory/students/', advisory_teacher_views.teacher_advisory_students, name='teacher_advisory_students'),
    path('teacher/advisory/attendance/', advisory_teacher_views.teacher_advisory_attendance, name='teacher_advisory_attendance'),
    path('teacher/advisory/excused/', advisory_teacher_views.teacher_advisory_excused, name='teacher_advisory_excused'),
    path('teacher/advisory/messages/', advisory_teacher_views.teacher_advisory_messages, name='teacher_advisory_messages'),
    path('teacher/advisory/settings/', advisory_teacher_views.teacher_advisory_settings, name='teacher_advisory_settings'),
       
    # Non-Advisory Teacher routes
    path('teacher/non-advisory/dashboard/', non_advisory_teacher_views.teacher_non_advisory_dashboard, name='teacher_non_advisory_dashboard'),
    path('teacher/non-advisory/students/', non_advisory_teacher_views.teacher_non_advisory_students, name='teacher_non_advisory_students'),
    path('teacher/non-advisory/guardians/', non_advisory_teacher_views.teacher_non_advisory_guardians, name='teacher_non_advisory_guardians'),
    path('teacher/non-advisory/attendance/', non_advisory_teacher_views.teacher_non_advisory_attendance, name='teacher_non_advisory_attendance'),
    path('teacher/non-advisory/excused/', non_advisory_teacher_views.teacher_non_advisory_excused, name='teacher_non_advisory_excused'),
    path('teacher/non-advisory/messages/', non_advisory_teacher_views.teacher_non_advisory_messages, name='teacher_non_advisory_messages'),
    path('teacher/non-advisory/settings/', non_advisory_teacher_views.teacher_non_advisory_settings, name='teacher_non_advisory_settings'),

  
]
