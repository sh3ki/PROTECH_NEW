from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from PROTECHAPP.face_recognition_engine import face_engine
from PROTECHAPP.models import Attendance, Student, UnauthorizedLog, SystemSettings, GateMode
from django.utils import timezone
from datetime import datetime, time as datetime_time
import pytz
from django.core.mail import send_mail
from django.conf import settings
from threading import Thread
from PROTECHAPP.philsms_service import send_sms
import requests
import os
import base64
import cv2
import numpy as np

def time_in(request):
    """Time In page for face recognition attendance"""
    from PROTECHAPP.models import SystemSettings
    settings_obj, _ = SystemSettings.objects.get_or_create(pk=1)
    return render(request, 'face_recognition/time_in.html', {
        'spoof_proof_enabled': settings_obj.spoof_proof_enabled,
        'holiday_mode': getattr(settings_obj, 'holiday_mode', False),
        'camera_count': getattr(settings_obj, 'camera_count', 1),
    })

def time_out(request):
    """Time Out page for face recognition attendance"""
    from PROTECHAPP.models import SystemSettings
    settings_obj, _ = SystemSettings.objects.get_or_create(pk=1)
    return render(request, 'face_recognition/time_out.html', {
        'spoof_proof_enabled': settings_obj.spoof_proof_enabled,
        'holiday_mode': getattr(settings_obj, 'holiday_mode', False),
        'camera_count': getattr(settings_obj, 'camera_count', 1),
    })

def hybrid_attendance(request):
    """Hybrid attendance page with both time in and time out cameras"""
    from PROTECHAPP.models import SystemSettings
    settings_obj, _ = SystemSettings.objects.get_or_create(pk=1)
    return render(request, 'face_recognition/hybrid_attendance.html', {
        'spoof_proof_enabled': settings_obj.spoof_proof_enabled,
        'holiday_mode': getattr(settings_obj, 'holiday_mode', False),
    })

@csrf_exempt
@require_http_methods(["POST"])
def recognize_faces_api(request):
    """
    Ultra-fast face recognition API
    Receives face embeddings and returns recognition results
    """
    try:
        # Check if holiday mode is enabled
        settings_obj, _ = SystemSettings.objects.get_or_create(pk=1)
        if getattr(settings_obj, 'holiday_mode', False):
            return JsonResponse({
                'success': False,
                'error': 'Face recognition is disabled during Holiday Mode'
            }, status=403)
        
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
        # Check if holiday mode is enabled
        settings_obj, _ = SystemSettings.objects.get_or_create(pk=1)
        if getattr(settings_obj, 'holiday_mode', False):
            return JsonResponse({
                'success': False,
                'error': 'Attendance recording is disabled during Holiday Mode'
            }, status=403)
        
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
        current_time_utc = utc_now.time()

        settings_obj, _ = SystemSettings.objects.get_or_create(pk=1)
        gate_mode = getattr(settings_obj, 'gate_mode', GateMode.CLOSED)

        manila_tz = pytz.timezone('Asia/Manila')
        manila_time = utc_now.astimezone(manila_tz).time()
        manila_datetime = utc_now.astimezone(manila_tz)

        def notify_time_in(attendance_obj):
            def _send():
                try:
                    email_enabled = settings_obj.email_notifications_enabled
                    sms_enabled = settings_obj.sms_notifications_enabled
                    guardians = student.guardians.all()

                    if guardians.exists():
                        for guardian in guardians:
                            guardian_name = f"{guardian.first_name} {guardian.last_name}"

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
Status: {attendance_obj.status}

This is an automated message from PROTECH Attendance System.
Please do not reply to this email.

Best regards,
PROTECH Administration
                                    """.strip()
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

                            if guardian.phone and sms_enabled:
                                try:
                                    sms_message = f"""PROTECH Time In Alert

Student: {student.first_name} {student.last_name}
ID: {student.lrn}
Grade: {student.grade.name if student.grade else 'N/A'} - {student.section.name if student.section else 'N/A'}
Date: {manila_datetime.strftime('%b %d, %Y')}
Time: {manila_time.strftime('%I:%M %p')}
Status: {attendance_obj.status}

-PROTECH Attendance System"""
                                    sms_result = send_sms(
                                        phone_number=guardian.phone,
                                        message=sms_message,
                                        sender_id=getattr(settings, 'PHILSMS_SENDER_ID', None)
                                    )
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

            Thread(target=_send).start()

        def notify_time_out(attendance_obj):
            def _send():
                try:
                    email_enabled = settings_obj.email_notifications_enabled
                    sms_enabled = settings_obj.sms_notifications_enabled
                    guardians = student.guardians.all()

                    if guardians.exists():
                        for guardian in guardians:
                            guardian_name = f"{guardian.first_name} {guardian.last_name}"

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

                            if guardian.phone and sms_enabled:
                                try:
                                    sms_message = f"""PROTECH Time Out Alert

Student: {student.first_name} {student.last_name}
ID: {student.lrn}
Grade: {student.grade.name if student.grade else 'N/A'} - {student.section.name if student.section else 'N/A'}
Date: {manila_datetime.strftime('%b %d, %Y')}
Time: {manila_time.strftime('%I:%M %p')}

-PROTECH Attendance System"""
                                    sms_result = send_sms(
                                        phone_number=guardian.phone,
                                        message=sms_message,
                                        sender_id=getattr(settings, 'PHILSMS_SENDER_ID', None)
                                    )
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

            Thread(target=_send).start()

        # -----------------
        # Gate Mode: OPEN
        # -----------------
        if gate_mode == GateMode.OPEN:
            latest_today = Attendance.objects.filter(student=student, date=today).order_by('-created_at').first()
            inside = bool(latest_today and latest_today.time_in and not latest_today.time_out)

            if attendance_type == 'time_in':
                if inside:
                    return JsonResponse({
                        'success': False,
                        'message': 'Already timed in (open gate)'
                    }, status=400)

                attendance = Attendance.objects.create(
                    student=student,
                    date=today,
                    time_in=current_time_utc,
                    status='ON TIME'
                )
                notify_time_in(attendance)
                trigger_gate_opening()

                return JsonResponse({
                    'success': True,
                    'message': f'Time in recorded for {student.first_name} {student.last_name}',
                    'status': attendance.status,
                    'time': manila_time.strftime('%I:%M %p')
                })

            elif attendance_type == 'time_out':
                if not inside or not latest_today:
                    return JsonResponse({
                        'success': False,
                        'message': 'No active time in record to time out (open gate)'
                    }, status=400)

                latest_today.time_out = current_time_utc
                latest_today.status = 'ON TIME'
                latest_today.save()
                notify_time_out(latest_today)
                trigger_gate_opening()

                return JsonResponse({
                    'success': True,
                    'message': f'Time out recorded for {student.first_name} {student.last_name}',
                    'time': manila_time.strftime('%I:%M %p')
                })

            return JsonResponse({'error': 'Invalid attendance type'}, status=400)

        # -----------------
        # Gate Mode: CLOSED (existing behavior)
        # -----------------
        attendance, created = Attendance.objects.get_or_create(
            student=student,
            date=today,
            defaults={
                'status': 'ON TIME'
            }
        )

        if attendance_type == 'time_in':
            if not attendance.time_in:
                attendance.time_in = current_time_utc

                # Calculate attendance status based on class timing and grace period
                status = 'LATE'

                if settings_obj.first_class_start_time:
                    grace_period = settings_obj.grace_period_minutes
                    first_class_time = settings_obj.first_class_start_time

                    from datetime import timedelta
                    first_class_datetime = datetime.combine(today, first_class_time)
                    present_start = first_class_datetime - timedelta(hours=2)
                    present_end = first_class_datetime + timedelta(minutes=grace_period)

                    current_datetime = datetime.combine(today, current_time_utc)

                    if present_start <= current_datetime <= present_end:
                        status = 'ON TIME'

                if status == 'LATE' and settings_obj.second_class_start_time:
                    second_class_time = settings_obj.second_class_start_time
                    grace_period = settings_obj.grace_period_minutes

                    from datetime import timedelta
                    second_class_datetime = datetime.combine(today, second_class_time)
                    present_start = second_class_datetime - timedelta(hours=2)
                    present_end = second_class_datetime + timedelta(minutes=grace_period)

                    current_datetime = datetime.combine(today, current_time_utc)

                    if present_start <= current_datetime <= present_end:
                        status = 'ON TIME'

                attendance.status = status
                attendance.save()

                notify_time_in(attendance)
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
            if attendance.time_in and not attendance.time_out:
                attendance.time_out = current_time_utc
                attendance.save()

                notify_time_out(attendance)
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
    Respects the recognition_display_mode setting (SCROLLABLE or LATEST)
    """
    try:
        # Get system settings for display mode
        from PROTECHAPP.models import SystemSettings
        settings_obj, _ = SystemSettings.objects.get_or_create(pk=1)
        display_mode = settings_obj.recognition_display_mode
        
        # Get today's date in UTC (database stores UTC)
        today = timezone.now().date()
        
        # Get all attendance records for today with time_in, ordered by latest first
        attendances = Attendance.objects.filter(
            date=today,
            time_in__isnull=False
        ).select_related('student').order_by('-time_in')
        
        # If display mode is LATEST, only get the most recent record
        if display_mode == 'LATEST' and attendances.exists():
            attendances = attendances[:1]
        
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
    Respects the recognition_display_mode setting (SCROLLABLE or LATEST)
    """
    try:
        # Get system settings for display mode
        from PROTECHAPP.models import SystemSettings
        settings_obj, _ = SystemSettings.objects.get_or_create(pk=1)
        display_mode = settings_obj.recognition_display_mode
        
        # Get today's date in UTC (database stores UTC)
        today = timezone.now().date()
        
        # Get all attendance records for today with time_out, ordered by latest first
        attendances = Attendance.objects.filter(
            date=today,
            time_out__isnull=False
        ).select_related('student').order_by('-time_out')
        
        # If display mode is LATEST, only get the most recent record
        if display_mode == 'LATEST' and attendances.exists():
            attendances = attendances[:1]
        
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
    
    This endpoint is controlled by the Prototype Gate System setting.
    When disabled, it returns 0 cycles regardless of queue status.
    """
    from PROTECHAPP.models import SystemSettings
    
    global gate_queue
    
    try:
        # Check if prototype gate system is enabled
        settings_obj, _ = SystemSettings.objects.get_or_create(pk=1)
        if not getattr(settings_obj, 'prototype_gate_system_enabled', True):
            # Prototype gate system is disabled - return 0 cycles
            return JsonResponse({
                'success': True,
                'cycles': 0,
                'message': 'Prototype Gate System is disabled'
            })
        
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

@csrf_exempt
@require_http_methods(["POST"])
def save_unauthorized_face(request):
    """
    Save unauthorized face photo to local file and database
    Called when a face is detected but not recognized
    """
    try:
        data = json.loads(request.body)
        image_data = data.get('image')  # Base64 encoded image
        camera_name = data.get('camera_name', 'Unknown Camera')
        
        if not image_data:
            return JsonResponse({'error': 'No image data provided'}, status=400)
        
        # Decode base64 image
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return JsonResponse({'error': 'Invalid image data'}, status=400)
        except Exception as e:
            print(f"Error decoding image: {e}")
            return JsonResponse({'error': 'Failed to decode image'}, status=400)
        
        # Create date folder structure
        manila_tz = pytz.timezone('Asia/Manila')
        now_manila = timezone.now().astimezone(manila_tz)
        date_folder = now_manila.strftime('%Y-%m-%d')
        
        # Build folder path
        unauthorized_dir = os.path.join(settings.MEDIA_ROOT, 'unauthorized_faces', date_folder)
        os.makedirs(unauthorized_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp_str = now_manila.strftime('%Y%m%d_%H%M%S_%f')
        filename = f"unauthorized_{timestamp_str}.jpg"
        file_path = os.path.join(unauthorized_dir, filename)
        
        # Save image to file
        cv2.imwrite(file_path, img)
        
        # Create relative path for database storage
        relative_path = os.path.join('unauthorized_faces', date_folder, filename)
        
        # Save to database
        unauthorized_log = UnauthorizedLog.objects.create(
            photo_path=relative_path,
            camera_name=camera_name,
            timestamp=timezone.now()
        )
        
        print(f"✅ Unauthorized face saved: {relative_path} from {camera_name}")
        
        return JsonResponse({
            'success': True,
            'message': 'Unauthorized face saved',
            'log_id': unauthorized_log.id,
            'photo_path': relative_path
        })
        
    except Exception as e:
        print(f"Error in save_unauthorized_face: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def delete_unauthorized_log(request):
    """Delete unauthorized face log(s)"""
    try:
        data = json.loads(request.body)
        log_ids = data.get('log_ids', [])
        
        if not log_ids:
            return JsonResponse({
                'status': 'error',
                'message': 'No log IDs provided'
            }, status=400)
        
        # Get logs and delete associated photos
        logs = UnauthorizedLog.objects.filter(id__in=log_ids)
        deleted_count = 0
        
        for log in logs:
            # Delete the photo file
            try:
                photo_path = os.path.join(settings.MEDIA_ROOT, log.photo_path)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            except Exception as e:
                print(f"Error deleting photo file: {e}")
            
            # Delete the database record
            log.delete()
            deleted_count += 1
        
        return JsonResponse({
            'status': 'success',
            'message': f'Successfully deleted {deleted_count} log(s)',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        print(f"Error in delete_unauthorized_log: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
