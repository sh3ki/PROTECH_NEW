from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Grade, Section, Student, Guardian, Attendance, ExcusedAbsence,
    Notification, AdvisoryAssignment, ActivityLog, UserSession, BroadcastAnnouncement,
    Chat, Message, ChatParticipant, MessageNotification, SystemSettings
)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'status', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('middle_name', 'profile_pic', 'role', 'status')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('middle_name', 'profile_pic', 'role', 'status')}),
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
admin.site.register(SystemSettings)
