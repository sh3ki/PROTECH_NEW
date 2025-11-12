from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from PROTECHAPP.views import admin_views, advisory_teacher_views, non_advisory_teacher_views, registrar_views, principal_views, public_views, face_recognition_views

urlpatterns = [
    # Public routes
    path('', public_views.landing_page, name='landing_page'),
    path('select-device/', public_views.select_device, name='select_device'),
    path('login/', public_views.login_view, name='login'),
    path('logout/', public_views.logout_view, name='logout'),

    # Face Recognition routes
    path('time-in/', face_recognition_views.time_in, name='time_in'),
    path('time-out/', face_recognition_views.time_out, name='time_out'),
    path('api/recognize-faces/', face_recognition_views.recognize_faces_api, name='recognize_faces_api'),
    path('api/record-attendance/', face_recognition_views.record_attendance_api, name='record_attendance_api'),

# ==========================
#  ADMIN ROUTES
# ==========================

    # admin/users routes
    path('admin/users/', admin_views.admin_users, name='admin_users'),
    path('admin/users/create/', admin_views.create_user, name='admin_create_user'),
    path('admin/users/<int:user_id>/', admin_views.get_user, name='admin_get_user'),
    path('admin/users/<int:user_id>/update/', admin_views.update_user, name='admin_update_user'),
    path('admin/users/<int:user_id>/delete/', admin_views.delete_user, name='admin_delete_user'),
    path('admin/users/<int:user_id>/reset-password/', admin_views.reset_user_password, name='admin_reset_user_password'),
    path('admin/users/upload-profile-pic/', admin_views.upload_profile_pic, name='admin_upload_profile_pic'),
    path('admin/users/search/', admin_views.search_users, name='admin_search_users'),
    # path('admin/users/import/', admin_views.import_users, name='import_users'),

    #admin/teachers routes  
    path('admin/teachers/', admin_views.admin_teachers, name='admin_teachers'),
    path('admin/teachers/search/', admin_views.search_teachers, name='admin_search_teachers'),
    path('admin/teachers/assign-section/', admin_views.assign_teacher_section, name='assign_teacher_section'),
    path('admin/teachers/remove-section/', admin_views.remove_teacher_section, name='remove_teacher_section'),
    
    # admin/grades routes
    path('admin/grades/', admin_views.admin_grades, name='admin_grades'),
    path('admin/grades/search/', admin_views.search_grades, name='admin_search_grades'),
    path('admin/grades/create/', admin_views.create_grade, name='admin_create_grade'),
    path('admin/grades/<int:grade_id>/update/', admin_views.update_grade, name='admin_update_grade'),
    path('admin/grades/<int:grade_id>/delete/', admin_views.delete_grade, name='admin_delete_grade'),
    path('admin/grades/<int:grade_id>/sections/', admin_views.get_grade_sections, name='admin_get_grade_sections'),
    
    # admin/sections routes
    path('admin/sections/', admin_views.admin_sections, name='admin_sections'),
    path('admin/sections/search/', admin_views.search_sections, name='admin_search_sections'),
    path('admin/sections/create/', admin_views.create_section, name='admin_create_section'),
    path('admin/sections/<int:section_id>/update/', admin_views.update_section, name='admin_update_section'),
    path('admin/sections/<int:section_id>/delete/', admin_views.delete_section, name='admin_delete_section'),
    path('admin/sections/<int:section_id>/students/', admin_views.get_section_students, name='admin_get_section_students'),

    # admin/students routes
    path('admin/students/', admin_views.admin_students, name='admin_students'),
    path('admin/students/search/', admin_views.search_students, name='admin_search_students'),
    path('admin/students/create/', admin_views.create_student, name='admin_create_student'),
    path('admin/students/<int:student_id>/', admin_views.get_student, name='admin_get_student'),
    path('admin/students/<int:student_id>/update/', admin_views.update_student, name='admin_update_student'),
    path('admin/students/<int:student_id>/delete/', admin_views.delete_student, name='admin_delete_student'),
    path('admin/students/<int:student_id>/reset-password/', admin_views.reset_student_password, name='admin_reset_student_password'),

    # admin/guardians routes
    path('admin/guardians/search/', admin_views.search_guardians, name='admin_search_guardians'),
    path('admin/guardians/create/', admin_views.create_guardian, name='admin_create_guardian'),
    path('admin/guardians/<int:guardian_id>/update/', admin_views.update_guardian, name='admin_update_guardian'),
    path('admin/guardians/<int:guardian_id>/delete/', admin_views.delete_guardian, name='admin_delete_guardian'),
    path('admin/guardians/<int:guardian_id>/children/', admin_views.get_guardian_children, name='admin_get_guardian_children'),
    path('admin/guardians/<int:guardian_id>/details/', admin_views.get_guardian_details, name='admin_get_guardian_details'),
    path('admin/guardians/sections-by-grade/', admin_views.admin_get_sections_by_grade, name='admin_get_sections_by_grade'),
    path('admin/guardians/students-by-section/', admin_views.admin_get_students_by_section, name='admin_get_students_by_section'),

    # admin/attendance routes
    path('admin/attendance-records/', admin_views.admin_attendance_records, name='admin_attendance'),
    path('admin/attendance-records/search/', admin_views.search_attendance_records, name='admin_search_attendance'),
    path('admin/attendance-records/create/', admin_views.create_attendance_record, name='admin_create_attendance'),
    path('admin/attendance-records/<int:attendance_id>/', admin_views.get_attendance_record, name='admin_get_attendance'),
    path('admin/attendance-records/<int:attendance_id>/update/', admin_views.update_attendance_record, name='admin_update_attendance'),
    path('admin/attendance-records/<int:attendance_id>/delete/', admin_views.delete_attendance_record, name='admin_delete_attendance'),
    path('admin/attendance-records/students/', admin_views.get_students_for_attendance, name='admin_get_students_for_attendance'),

    # admin/excused routes
    path('admin/excused/', admin_views.admin_excused, name='admin_excused'),
    path('admin/excused/search/', admin_views.search_excused_absences, name='admin_search_excused'),
    path('admin/excused/create/', admin_views.create_excused_absence, name='admin_create_excused'),
    path('admin/excused/<int:excused_id>/', admin_views.get_excused_absence, name='admin_get_excused'),
    path('admin/excused/<int:excused_id>/update/', admin_views.update_excused_absence, name='admin_update_excused'),
    path('admin/excused/<int:excused_id>/delete/', admin_views.delete_excused_absence, name='admin_delete_excused'),
    path('private-excuse-letters/<str:filename>/', views.serve_private_excuse_letter, name='serve_private_excuse_letter'),
    path('admin/excused/upload_excuse_letter/', admin_views.upload_excuse_letter, name='admin_upload_excuse_letter'),
    path('admin/excused/delete_excuse_letter/', admin_views.delete_excuse_letter, name='admin_delete_excuse_letter'),

    # admin other routes
    path('profile-pics/', admin_views.serve_profile_pic_default, name='serve_profile_pic_default'),
    path('profile-pics/<path:path>/', admin_views.serve_profile_pic, name='serve_profile_pic'),
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/guardians/', admin_views.admin_guardians, name='admin_guardians'),
    path('admin/settings/', admin_views.admin_settings, name='admin_settings'),


# ==========================
#  PRINCIPAL ROUTES
# ==========================

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


# ==========================
#  REGISTRAR ROUTES
# ==========================   
    
    # Registrar dashboard and main routes
    path('registrar/dashboard/', registrar_views.registrar_dashboard, name='registrar_dashboard'),
    path('registrar/face-enroll/', registrar_views.registrar_face_enroll, name='registrar_face_enroll'),
    path('registrar/announcements/', registrar_views.registrar_announcements, name='registrar_announcements'),
    path('registrar/messages/', registrar_views.registrar_messages, name='registrar_messages'),
    path('registrar/settings/', registrar_views.registrar_settings, name='registrar_settings'),

    # registrar/grades routes
    path('registrar/grades/', registrar_views.registrar_grades, name='registrar_grades'),
    path('registrar/grades/search/', registrar_views.registrar_search_grades, name='registrar_search_grades'),
    path('registrar/grades/create/', registrar_views.registrar_create_grade, name='registrar_create_grade'),
    path('registrar/grades/<int:grade_id>/update/', registrar_views.registrar_update_grade, name='registrar_update_grade'),
    path('registrar/grades/<int:grade_id>/delete/', registrar_views.registrar_delete_grade, name='registrar_delete_grade'),
    path('registrar/grades/<int:grade_id>/sections/', registrar_views.registrar_get_grade_sections, name='registrar_get_grade_sections'),
    
    # registrar/sections routes
    path('registrar/sections/', registrar_views.registrar_sections, name='registrar_sections'),
    path('registrar/sections/search/', registrar_views.registrar_search_sections, name='registrar_search_sections'),
    path('registrar/sections/create/', registrar_views.registrar_create_section, name='registrar_create_section'),
    path('registrar/sections/<int:section_id>/update/', registrar_views.registrar_update_section, name='registrar_update_section'),
    path('registrar/sections/<int:section_id>/delete/', registrar_views.registrar_delete_section, name='registrar_delete_section'),
    path('registrar/sections/<int:section_id>/students/', registrar_views.registrar_get_section_students, name='registrar_get_section_students'),

    # registrar/students routes
    path('registrar/students/', registrar_views.registrar_students, name='registrar_students'),
    path('registrar/students/search/', registrar_views.registrar_search_students, name='registrar_search_students'),
    path('registrar/students/create/', registrar_views.registrar_create_student, name='registrar_create_student'),
    path('registrar/students/<int:student_id>/', registrar_views.registrar_get_student, name='registrar_get_student'),
    path('registrar/students/<int:student_id>/update/', registrar_views.registrar_update_student, name='registrar_update_student'),
    path('registrar/students/<int:student_id>/delete/', registrar_views.registrar_delete_student, name='registrar_delete_student'),
    path('registrar/students/<int:student_id>/reset-password/', registrar_views.registrar_reset_student_password, name='registrar_reset_student_password'),
    
    # registrar/students import routes
    path('registrar/students/download-template/', registrar_views.registrar_download_student_template, name='registrar_download_student_template'),
    path('registrar/students/import/', registrar_views.registrar_import_students, name='registrar_import_students'),

    # registrar/guardians routes
    path('registrar/guardians/', registrar_views.registrar_guardians, name='registrar_guardians'),
    path('registrar/guardians/search/', registrar_views.registrar_search_guardians, name='registrar_search_guardians'),
    path('registrar/guardians/create/', registrar_views.registrar_create_guardian, name='registrar_create_guardian'),
    path('registrar/guardians/<int:guardian_id>/update/', registrar_views.registrar_update_guardian, name='registrar_update_guardian'),
    path('registrar/guardians/<int:guardian_id>/delete/', registrar_views.registrar_delete_guardian, name='registrar_delete_guardian'),
    path('registrar/guardians/<int:guardian_id>/children/', registrar_views.registrar_get_guardian_children, name='registrar_get_guardian_children'),
    path('registrar/guardians/<int:guardian_id>/details/', registrar_views.registrar_get_guardian_details, name='registrar_get_guardian_details'),
    path('registrar/guardians/sections-by-grade/', registrar_views.registrar_get_sections_by_grade, name='registrar_get_sections_by_grade'),
    path('registrar/guardians/students-by-section/', registrar_views.registrar_get_students_by_section, name='registrar_get_students_by_section'),

    # registrar/attendance routes
    path('registrar/attendance-records/', registrar_views.registrar_attendance_records, name='registrar_attendance'),
    path('registrar/attendance-records/search/', registrar_views.registrar_search_attendance_records, name='registrar_search_attendance'),
    path('registrar/attendance-records/create/', registrar_views.registrar_create_attendance_record, name='registrar_create_attendance'),
    path('registrar/attendance-records/<int:attendance_id>/', registrar_views.registrar_get_attendance_record, name='registrar_get_attendance'),
    path('registrar/attendance-records/<int:attendance_id>/update/', registrar_views.registrar_update_attendance_record, name='registrar_update_attendance'),
    path('registrar/attendance-records/<int:attendance_id>/delete/', registrar_views.registrar_delete_attendance_record, name='registrar_delete_attendance'),
    path('registrar/attendance-records/students/', registrar_views.registrar_get_students_for_attendance, name='registrar_get_students_for_attendance'),

    # registrar/excused routes
    path('registrar/excused/', registrar_views.registrar_excused, name='registrar_excused'),
    path('registrar/excused/search/', registrar_views.registrar_search_excused_absences, name='registrar_search_excused'),
    path('registrar/excused/create/', registrar_views.registrar_create_excused_absence, name='registrar_create_excused'),
    path('registrar/excused/<int:excused_id>/', registrar_views.registrar_get_excused_absence, name='registrar_get_excused'),
    path('registrar/excused/<int:excused_id>/update/', registrar_views.registrar_update_excused_absence, name='registrar_update_excused'),
    path('registrar/excused/<int:excused_id>/delete/', registrar_views.registrar_delete_excused_absence, name='registrar_delete_excused'),
    
    # registrar/face-enrollment routes
    path('registrar/face-enrollment/students/search/', registrar_views.registrar_search_students_for_face_enrollment, name='registrar_search_students_for_face_enrollment'),
    path('registrar/face-enrollment/save/', registrar_views.registrar_save_face_embedding, name='registrar_save_face_embedding'),
    path('registrar/face-enrollment/<int:student_id>/status/', registrar_views.registrar_get_student_face_status, name='registrar_get_student_face_status'),
    path('registrar/face-enrollment/<int:student_id>/delete/', registrar_views.registrar_delete_face_embedding, name='registrar_delete_face_embedding'), 
    

# ==========================
#  ADVISORY TEACHER ROUTES
# ==========================

    # Advisory Teacher routes
    path('teacher/advisory/dashboard/', advisory_teacher_views.teacher_advisory_dashboard, name='teacher_advisory_dashboard'),
    path('teacher/advisory/students/', advisory_teacher_views.teacher_advisory_students, name='teacher_advisory_students'),
    path('teacher/advisory/attendance/', advisory_teacher_views.teacher_advisory_attendance, name='teacher_advisory_attendance'),
    path('teacher/advisory/excused/', advisory_teacher_views.teacher_advisory_excused, name='teacher_advisory_excused'),
    path('teacher/advisory/messages/', advisory_teacher_views.teacher_advisory_messages, name='teacher_advisory_messages'),
    path('teacher/advisory/settings/', advisory_teacher_views.teacher_advisory_settings, name='teacher_advisory_settings'),

  
# ==========================
#  NON-ADVISORY TEACHER ROUTES
# ==========================
     
    # Non-Advisory Teacher routes
    path('teacher/non-advisory/dashboard/', non_advisory_teacher_views.teacher_non_advisory_dashboard, name='teacher_non_advisory_dashboard'),
    path('teacher/non-advisory/students/', non_advisory_teacher_views.teacher_non_advisory_students, name='teacher_non_advisory_students'),
    path('teacher/non-advisory/guardians/', non_advisory_teacher_views.teacher_non_advisory_guardians, name='teacher_non_advisory_guardians'),
    path('teacher/non-advisory/attendance/', non_advisory_teacher_views.teacher_non_advisory_attendance, name='teacher_non_advisory_attendance'),
    path('teacher/non-advisory/excused/', non_advisory_teacher_views.teacher_non_advisory_excused, name='teacher_non_advisory_excused'),
    path('teacher/non-advisory/messages/', non_advisory_teacher_views.teacher_non_advisory_messages, name='teacher_non_advisory_messages'),
    path('teacher/non-advisory/settings/', non_advisory_teacher_views.teacher_non_advisory_settings, name='teacher_non_advisory_settings'),

]
