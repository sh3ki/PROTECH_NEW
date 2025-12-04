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
admin.site.register(SystemSettings)
admin.site.register(BackupLog, BackupLogAdmin)
