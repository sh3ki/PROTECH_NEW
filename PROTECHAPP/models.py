from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# User Roles and Status Choices
class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrator'
    TEACHER = 'TEACHER', 'Teacher'
    PRINCIPAL = 'PRINCIPAL', 'Principal'
    REGISTRAR = 'REGISTRAR', 'Registrar'

class UserStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    DISAPPROVED = 'DISAPPROVED', 'Disapproved'

class StudentStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'

class AttendanceStatus(models.TextChoices):
    PRESENT = 'PRESENT', 'Present'
    ABSENT = 'ABSENT', 'Absent'
    EXCUSED = 'EXCUSED', 'Excused'

class NotificationType(models.TextChoices):
    EMAIL = 'EMAIL', 'Email'
    SMS = 'SMS', 'SMS'
    SYSTEM = 'SYSTEM', 'System'

class NotificationStatus(models.TextChoices):
    SENT = 'SENT', 'Sent'
    FAILED = 'FAILED', 'Failed'
    PENDING = 'PENDING', 'Pending'

class NotificationCategory(models.TextChoices):
    ATTENDANCE = 'ATTENDANCE', 'Attendance'
    MESSAGE = 'MESSAGE', 'Message'
    SYSTEM_ALERT = 'SYSTEM_ALERT', 'System Alert'

class ActivityCategory(models.TextChoices):
    AUTH = 'AUTH', 'Authentication'
    DATA = 'DATA', 'Data Manipulation'
    MESSAGING = 'MESSAGING', 'Messaging'
    SYSTEM = 'SYSTEM', 'System'

# 1. Users Model
class CustomUser(AbstractUser):
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    profile_pic = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.TEACHER)
    status = models.CharField(max_length=20, choices=UserStatus.choices, default=UserStatus.PENDING)
    section = models.ForeignKey('Section', on_delete=models.SET_NULL, null=True, blank=True, related_name='advisors')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

# 2. Grades Table
class Grade(models.Model):
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

# 3. Sections Table
class Section(models.Model):
    name = models.CharField(max_length=50)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='sections')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.grade.name} - {self.name}"

# 4. Students Table
class Student(models.Model):
    lrn = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='students')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='students')
    profile_pic = models.CharField(max_length=255, blank=True, null=True)
    face_path = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=StudentStatus.choices, default=StudentStatus.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.lrn})"

# 5. Guardians Table
class Guardian(models.Model):
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='guardians')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - Guardian of {self.student}"

# 6. Attendance Table
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=AttendanceStatus.choices)
    sent_email = models.BooleanField(default=False)
    sent_sms = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'date']
    
    def __str__(self):
        return f"{self.student} - {self.date} ({self.get_status_display()})"

# 7. Excused Absences Table
class ExcusedAbsence(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='excused_absences')
    date_absent = models.DateField()
    excuse_letter = models.CharField(max_length=255)  # Path to file
    effective_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student} - Excused from {self.effective_date} to {self.end_date}"

# 8. Notifications Table
class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    type = models.CharField(max_length=20, choices=NotificationType.choices)
    status = models.CharField(max_length=20, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    category = models.CharField(max_length=20, choices=NotificationCategory.choices)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_category_display()} notification to {self.user}"

# 9. Advisory Assignments Table
class AdvisoryAssignment(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='advisory_assignments')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='advisory_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['teacher', 'section']
    
    def __str__(self):
        return f"{self.teacher} - Advisor of {self.section}"

# 10. Activity Logs Table
class ActivityLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    action = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=ActivityCategory.choices)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user} - {self.action} ({self.timestamp})"

# 11. User Sessions Table
class UserSession(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    session_start = models.DateTimeField()
    session_end = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    ip_address = models.CharField(max_length=45)
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user} - Session from {self.session_start}"

# 12. Broadcast Announcements Table
class BroadcastAnnouncement(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_announcements')
    target_role = models.CharField(max_length=20, choices=UserRole.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - To {self.get_target_role_display()} by {self.sender}"

# 14. Chats Table (created before Messages to satisfy dependencies)
class Chat(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    is_group = models.BooleanField(default=False)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_chats')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name if self.name else f"Chat {self.id}"

# 13. Messages Table
class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Message from {self.sender} in {self.chat}"

# 15. Chat Participants Table
class ChatParticipant(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='chat_participations')
    joined_at = models.DateTimeField(default=timezone.now)
    is_muted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['chat', 'user']
    
    def __str__(self):
        return f"{self.user} in {self.chat}"

# 16. Message Notifications Table
class MessageNotification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='message_notifications')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='notifications')
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='message_notifications')
    is_read = models.BooleanField(default=False)
    notified_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['user', 'message']
    
    def __str__(self):
        return f"Notification to {self.user} for message {self.message.id}"

# 17. System Settings Table
class SystemSettings(models.Model):
    sms_gateway_url = models.CharField(max_length=255, blank=True, null=True)
    sms_api_key = models.CharField(max_length=255, blank=True, null=True)
    sms_sender_id = models.CharField(max_length=255, blank=True, null=True)
    email_host = models.CharField(max_length=255, blank=True, null=True)
    email_port = models.IntegerField(null=True, blank=True)
    email_username = models.CharField(max_length=255, blank=True, null=True)
    email_password = models.CharField(max_length=255, blank=True, null=True)
    face_confidence_min = models.FloatField(default=0.5)
    face_confidence_max = models.FloatField(default=0.9)
    attendance_time_in = models.TimeField(default='07:00:00')
    attendance_time_out = models.TimeField(default='16:00:00')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return "System Settings"
    
    class Meta:
        verbose_name_plural = "System Settings"
