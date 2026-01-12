from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Grade, Section, Student, Guardian, Attendance, ExcusedAbsence,
    Notification, AdvisoryAssignment, ActivityLog, UserSession, BroadcastAnnouncement,
    Chat, Message, ChatParticipant, MessageNotification, SystemSettings, BackupLog
)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('middle_name', 'profile_pic', 'role')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('middle_name', 'profile_pic', 'role')}),
    )

class BackupLogAdmin(admin.ModelAdmin):
    list_display = ['filename', 'backup_type', 'status', 'file_size_mb', 'initiated_by', 'created_at']
    list_filter = ['backup_type', 'status', 'created_at']
    search_fields = ['filename', 'error_message']
    readonly_fields = ['filename', 'filepath', 'file_size_bytes', 'file_size_mb', 'backup_type', 'status', 'error_message', 'initiated_by', 'created_at']
    ordering = ['-created_at']


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'attendance_mode', 'recognition_display_mode', 'spoof_proof_enabled', 'email_notifications_enabled', 'sms_notifications_enabled']
    list_editable = ['spoof_proof_enabled']
    fieldsets = (
        ('Face Recognition', {
            'fields': (
                'face_confidence_min', 'face_confidence_max', 'recognition_display_mode', 'spoof_proof_enabled'
            )
        }),
        ('Attendance Windows', {
            'fields': (
                'attendance_time_in', 'attendance_time_out', 'attendance_mode',
                'first_class_start_time', 'second_class_start_time', 'grace_period_minutes'
            )
        }),
        ('Notifications', {
            'fields': (
                'email_notifications_enabled', 'sms_notifications_enabled'
            )
        }),
        ('SMS Gateway', {
            'fields': ('sms_gateway_url', 'sms_api_key', 'sms_sender_id')
        }),
        ('Email Gateway', {
            'fields': ('email_host', 'email_port', 'email_username', 'email_password')
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Grade)
admin.site.register(Section)
admin.site.register(Student)
admin.site.register(Guardian)
admin.site.register(Attendance)
admin.site.register(ExcusedAbsence)
admin.site.register(Notification)
admin.site.register(AdvisoryAssignment)
admin.site.register(ActivityLog)
admin.site.register(UserSession)
admin.site.register(BroadcastAnnouncement)
admin.site.register(Chat)
admin.site.register(Message)
admin.site.register(ChatParticipant)
admin.site.register(MessageNotification)
admin.site.register(BackupLog, BackupLogAdmin)
