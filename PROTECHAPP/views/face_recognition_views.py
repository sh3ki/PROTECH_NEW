from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from PROTECHAPP.face_recognition_engine import face_engine
from PROTECHAPP.models import Attendance, Student
from django.utils import timezone
from datetime import datetime, time as datetime_time
import pytz
from django.core.mail import send_mail
from django.conf import settings
from threading import Thread
from PROTECHAPP.philsms_service import send_sms
import requests

def time_in(request):
    """Time In page for face recognition attendance"""
    return render(request, 'face_recognition/time_in.html')

def time_out(request):
    """Time Out page for face recognition attendance"""
    return render(request, 'face_recognition/time_out.html')

def hybrid_attendance(request):
    """Hybrid attendance page with both time in and time out cameras"""
    return render(request, 'face_recognition/hybrid_attendance.html')

@csrf_exempt
@require_http_methods(["POST"])
def recognize_faces_api(request):
    """
    Ultra-fast face recognition API
    Receives face embeddings and returns recognition results
    """
    try:
        data = json.loads(request.body)
        face_embeddings = data.get('face_embeddings', [])
        
        if not face_embeddings:
            return JsonResponse({'error': 'No face embeddings provided'}, status=400)
        
        # Recognize all faces in parallel
        results = face_engine.recognize_multiple_faces(face_embeddings)
        
        return JsonResponse({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        print(f"Error in recognize_faces_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def record_attendance_api(request):
    """
    Record attendance when face is recognized
    """
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        attendance_type = data.get('type')  # 'time_in' or 'time_out'
        
        if not student_id or not attendance_type:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Get student
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
        
        # Get current time in UTC (database will store UTC)
        utc_now = timezone.now()
        today = utc_now.date()
        
        # Check if attendance already exists for today
        attendance, created = Attendance.objects.get_or_create(
            student=student,
            date=today,
            defaults={
                'status': 'ON TIME'  # Will be updated based on time
            }
        )
        
        # Save as UTC time (database stores UTC)
        current_time_utc = utc_now.time()
        
        if attendance_type == 'time_in':
            # Record time in
            if not attendance.time_in:
                attendance.time_in = current_time_utc
                
                # Validate against UTC cutoff (8:00 AM Manila = 00:00 AM UTC)
                # Manila 8:00 AM is UTC 00:00 (midnight UTC)
                cutoff_time_utc = datetime_time(0, 0)  # Midnight UTC = 8:00 AM Manila
                if current_time_utc > cutoff_time_utc:
                    attendance.status = 'LATE'
                else:
                    attendance.status = 'ON TIME'
                
                attendance.save()
                
                # Convert to Manila time for display
                manila_tz = pytz.timezone('Asia/Manila')
                manila_time = utc_now.astimezone(manila_tz).time()
                manila_datetime = utc_now.astimezone(manila_tz)
                
                # Send email and SMS notification to guardian(s) in background
                def send_guardian_notification():
                    try:
                        # Check system settings for notification toggles
                        from PROTECHAPP.models import SystemSettings
                        settings_obj, _ = SystemSettings.objects.get_or_create(pk=1)
                        email_enabled = settings_obj.email_notifications_enabled
                        sms_enabled = settings_obj.sms_notifications_enabled
                        
                        # Get all guardians for this student
                        guardians = student.guardians.all()
                        
                        if guardians.exists():
                            # Send individual email and SMS to each guardian
                            for guardian in guardians:
                                guardian_name = f"{guardian.first_name} {guardian.last_name}"
                                
                                # STEP 1: Send email first (if guardian has email AND email notifications are enabled)
                                if guardian.email and email_enabled:
                                    try:
                                        subject = f"Student Time In Alert - {student.first_name} {student.last_name}"
                                        message = f"""
Dear Mr./Mrs. {guardian.first_name} {guardian.last_name},

This is to inform you that your child has arrived at school.

Student Details:
Name: {student.first_name} {student.middle_name or ''} {student.last_name}
Student ID: {student.lrn}
Grade & Section: {student.grade.name if student.grade else 'N/A'} - {student.section.name if student.section else 'N/A'}

Time In Details:
Date: {manila_datetime.strftime('%B %d, %Y')}
Time: {manila_time.strftime('%I:%M %p')}
Status: {attendance.status}

This is an automated message from PROTECH Attendance System.
Please do not reply to this email.

Best regards,
PROTECH Administration
                                        """.strip()
                                        
                                        # Send email
                                        send_mail(
                                            subject=subject,
                                            message=message,
                                            from_email=settings.DEFAULT_FROM_EMAIL,
                                            recipient_list=[guardian.email],
                                            fail_silently=True
                                        )
                                        print(f"✅ Email sent to {guardian_name} ({guardian.email})")
                                    except Exception as e:
                                        print(f"❌ Email failed for {guardian_name}: {e}")
                                elif guardian.email and not email_enabled:
                                    print(f"📧 Email notifications disabled - skipping email to {guardian_name}")
                                
                                # STEP 2: Send SMS after email (if guardian has phone number AND SMS notifications are enabled)
                                if guardian.phone and sms_enabled:
                                    try:
                                        sms_message = f"""PROTECH Time In Alert

Student: {student.first_name} {student.last_name}
ID: {student.lrn}
Grade: {student.grade.name if student.grade else 'N/A'} - {student.section.name if student.section else 'N/A'}
Date: {manila_datetime.strftime('%b %d, %Y')}
Time: {manila_time.strftime('%I:%M %p')}
Status: {attendance.status}

-PROTECH Attendance System"""
                                        
                                        # Send SMS after email
                                        sms_result = send_sms(
                                            phone_number=guardian.phone,
                                            message=sms_message,
                                            sender_id=getattr(settings, 'PHILSMS_SENDER_ID', None)
                                        )
                                        
                                        # Log SMS result
                                        if sms_result.get('success'):
                                            print(f"✅ SMS sent to {guardian_name} ({guardian.phone})")
                                        else:
                                            print(f"❌ SMS failed for {guardian_name} ({guardian.phone}): {sms_result.get('error', 'Unknown error')}")
                                    except Exception as e:
                                        print(f"❌ SMS exception for {guardian_name}: {e}")
                                elif guardian.phone and not sms_enabled:
                                    print(f"📱 SMS notifications disabled - skipping SMS to {guardian_name}")
                    except Exception as e:
                        print(f"Error sending guardian notification: {e}")
                
                # Send email in background thread
                Thread(target=send_guardian_notification).start()
                
                # Trigger gate opening
                trigger_gate_opening()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Time in recorded for {student.first_name} {student.last_name}',
                    'status': attendance.status,
                    'time': manila_time.strftime('%I:%M %p')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Already timed in today'
                }, status=400)
        
        elif attendance_type == 'time_out':
            # Record time out
            if attendance.time_in and not attendance.time_out:
                attendance.time_out = current_time_utc
                attendance.save()
                
                # Convert to Manila time for display
                manila_tz = pytz.timezone('Asia/Manila')
                manila_time = utc_now.astimezone(manila_tz).time()
                manila_datetime = utc_now.astimezone(manila_tz)
                
                # Send email and SMS notification to guardian(s) in background
                def send_guardian_notification():
                    try:
                        # Check system settings for notification toggles
                        from PROTECHAPP.models import SystemSettings
                        settings_obj, _ = SystemSettings.objects.get_or_create(pk=1)
                        email_enabled = settings_obj.email_notifications_enabled
                        sms_enabled = settings_obj.sms_notifications_enabled
                        
                        # Get all guardians for this student
                        guardians = student.guardians.all()
                        
                        if guardians.exists():
                            # Send individual email and SMS to each guardian
                            for guardian in guardians:
                                guardian_name = f"{guardian.first_name} {guardian.last_name}"
                                
                                # STEP 1: Send email first (if guardian has email AND email notifications are enabled)
                                if guardian.email and email_enabled:
                                    try:
                                        subject = f"Student Time Out Alert - {student.first_name} {student.last_name}"
                                        message = f"""
Dear Mr./Mrs. {guardian.first_name} {guardian.last_name},

This is to inform you that your child has left school.

Student Details:
Name: {student.first_name} {student.middle_name or ''} {student.last_name}
Student ID: {student.lrn}
Grade & Section: {student.grade.name if student.grade else 'N/A'} - {student.section.name if student.section else 'N/A'}

Time Out Details:
Date: {manila_datetime.strftime('%B %d, %Y')}
Time: {manila_time.strftime('%I:%M %p')}

This is an automated message from PROTECH Attendance System.
Please do not reply to this email.

Best regards,
PROTECH Administration
                                        """.strip()
                                        
                                        # Send email
                                        send_mail(
                                            subject=subject,
                                            message=message,
                                            from_email=settings.DEFAULT_FROM_EMAIL,
                                            recipient_list=[guardian.email],
                                            fail_silently=True
                                        )
                                        print(f"✅ Email sent to {guardian_name} ({guardian.email})")
                                    except Exception as e:
                                        print(f"❌ Email failed for {guardian_name}: {e}")
                                elif guardian.email and not email_enabled:
                                    print(f"📧 Email notifications disabled - skipping email to {guardian_name}")
                                
                                # STEP 2: Send SMS after email (if guardian has phone number AND SMS notifications are enabled)
                                if guardian.phone and sms_enabled:
                                    try:
                                        sms_message = f"""PROTECH Time Out Alert

Student: {student.first_name} {student.last_name}
ID: {student.lrn}
Grade: {student.grade.name if student.grade else 'N/A'} - {student.section.name if student.section else 'N/A'}
Date: {manila_datetime.strftime('%b %d, %Y')}
Time: {manila_time.strftime('%I:%M %p')}

-PROTECH Attendance System"""
                                        
                                        # Send SMS after email
                                        sms_result = send_sms(
                                            phone_number=guardian.phone,
                                            message=sms_message,
                                            sender_id=getattr(settings, 'PHILSMS_SENDER_ID', None)
                                        )
                                        
                                        # Log SMS result
                                        if sms_result.get('success'):
                                            print(f"✅ SMS sent to {guardian_name} ({guardian.phone})")
                                        else:
                                            print(f"❌ SMS failed for {guardian_name} ({guardian.phone}): {sms_result.get('error', 'Unknown error')}")
                                    except Exception as e:
                                        print(f"❌ SMS exception for {guardian_name}: {e}")
                                elif guardian.phone and not sms_enabled:
                                    print(f"📱 SMS notifications disabled - skipping SMS to {guardian_name}")
                    except Exception as e:
                        print(f"Error sending guardian notification: {e}")
                
                # Send email in background thread
                Thread(target=send_guardian_notification).start()
                
                # Trigger gate opening
                trigger_gate_opening()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Time out recorded for {student.first_name} {student.last_name}',
                    'time': manila_time.strftime('%I:%M %p')
                })
            elif not attendance.time_in:
                return JsonResponse({
                    'success': False,
                    'message': 'No time in record found'
                }, status=400)
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Already timed out today'
                }, status=400)
        
        return JsonResponse({'error': 'Invalid attendance type'}, status=400)
        
    except Exception as e:
        print(f"Error in record_attendance_api: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_today_attendance(request):
    """
    Get today's attendance list for Time In page
    Returns list of students who timed in today, ordered by latest first
    """
    try:
        # Get today's date in UTC (database stores UTC)
        today = timezone.now().date()
        
        # Get all attendance records for today with time_in, ordered by latest first
        attendances = Attendance.objects.filter(
            date=today,
            time_in__isnull=False
        ).select_related('student').order_by('-time_in')
        
        attendance_list = []
        for attendance in attendances:
            student = attendance.student
            
            # Determine status badge
            status = attendance.status
            if status == 'ON TIME':
                status_class = 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                status_text = 'On Time'
            elif status == 'LATE':
                status_class = 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                status_text = 'Late'
            else:
                status_class = 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                status_text = status
            
            # Convert UTC time to Manila time for display
            manila_tz = pytz.timezone('Asia/Manila')
            if attendance.time_in:
                # Combine date and time, make it UTC-aware, then convert to Manila
                utc_datetime = datetime.combine(attendance.date, attendance.time_in)
                utc_datetime = pytz.UTC.localize(utc_datetime)
                manila_datetime = utc_datetime.astimezone(manila_tz)
                time_in_str = manila_datetime.strftime('%I:%M %p')
            else:
                time_in_str = 'N/A'
            
            attendance_list.append({
                'id': attendance.id,
                'student_name': f"{student.first_name} {student.last_name}",
                'student_id': student.lrn,
                'time_in': time_in_str,
                'status': status,
                'status_text': status_text,
                'status_class': status_class,
                'date': 'Today'
            })
        
        return JsonResponse({
            'success': True,
            'count': len(attendance_list),
            'attendances': attendance_list
        })
        
    except Exception as e:
        print(f"Error in get_today_attendance: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_today_timeout(request):
    """
    Get today's time out list for Time Out page
    Returns list of students who timed out today, ordered by latest first
    """
    try:
        # Get today's date in UTC (database stores UTC)
        today = timezone.now().date()
        
        # Get all attendance records for today with time_out, ordered by latest first
        attendances = Attendance.objects.filter(
            date=today,
            time_out__isnull=False
        ).select_related('student').order_by('-time_out')
        
        attendance_list = []
        for attendance in attendances:
            student = attendance.student
            
            # Determine status badge (same as time in for consistency)
            status = attendance.status
            if status == 'ON TIME':
                status_class = 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                status_text = 'On Time'
            elif status == 'LATE':
                status_class = 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                status_text = 'Late'
            else:
                status_class = 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                status_text = status
            
            # Convert UTC time to Manila time for display
            manila_tz = pytz.timezone('Asia/Manila')
            if attendance.time_out:
                # Combine date and time, make it UTC-aware, then convert to Manila
                utc_datetime = datetime.combine(attendance.date, attendance.time_out)
                utc_datetime = pytz.UTC.localize(utc_datetime)
                manila_datetime = utc_datetime.astimezone(manila_tz)
                time_out_str = manila_datetime.strftime('%I:%M %p')
            else:
                time_out_str = 'N/A'
            
            attendance_list.append({
                'id': attendance.id,
                'student_name': f"{student.first_name} {student.last_name}",
                'student_id': student.lrn,
                'time_out': time_out_str,
                'status': status,
                'status_text': status_text,
                'status_class': status_class,
                'date': 'Today'
            })
        
        return JsonResponse({
            'success': True,
            'count': len(attendance_list),
            'attendances': attendance_list
        })
        
    except Exception as e:
        print(f"Error in get_today_timeout: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# Gate queue for controlling physical gate
gate_queue = []

def trigger_gate_opening():
    """
    Helper function to add gate trigger to queue
    Called internally when attendance is recorded
    """
    global gate_queue
    try:
        gate_queue.append(timezone.now())
        print(f"✅ Gate trigger added to queue. Queue length: {len(gate_queue)}")
    except Exception as e:
        print(f"❌ Error adding gate trigger to queue: {e}")

@csrf_exempt
@require_http_methods(["POST"])
def trigger_gate(request):
    """
    API endpoint for Arduino to trigger gate opening
    Called when attendance is recorded
    """
    global gate_queue
    
    try:
        # Add to queue
        gate_queue.append(timezone.now())
        
        return JsonResponse({
            'success': True,
            'queue_length': len(gate_queue),
            'message': 'Gate trigger added to queue'
        })
    except Exception as e:
        print(f"Error in trigger_gate: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def check_gate_queue(request):
    """
    API endpoint for Arduino to check if there are queued gate operations
    Returns the number of cycles to perform
    """
    global gate_queue
    
    try:
        queue_length = len(gate_queue)
        
        if queue_length > 0:
            # Clear the queue
            gate_queue = []
            
            return JsonResponse({
                'success': True,
                'cycles': queue_length,
                'message': f'{queue_length} gate cycle(s) to perform'
            })
        else:
            return JsonResponse({
                'success': True,
                'cycles': 0,
                'message': 'No gate cycles in queue'
            })
    except Exception as e:
        print(f"Error in check_gate_queue: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
