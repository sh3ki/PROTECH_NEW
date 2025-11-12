from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from PROTECHAPP.face_recognition_engine import face_engine
from PROTECHAPP.models import Attendance, Student
from django.utils import timezone
from datetime import datetime, time as datetime_time

def time_in(request):
    """Time In page for face recognition attendance"""
    return render(request, 'face_recognition/time_in.html')

def time_out(request):
    """Time Out page for face recognition attendance"""
    return render(request, 'face_recognition/time_out.html')

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
        
        # Get today's date
        today = timezone.now().date()
        
        # Check if attendance already exists for today
        attendance, created = Attendance.objects.get_or_create(
            student=student,
            date=today,
            defaults={
                'status': 'ON TIME'  # Will be updated based on time
            }
        )
        
        current_time = timezone.now().time()
        
        if attendance_type == 'time_in':
            # Record time in
            if not attendance.time_in:
                attendance.time_in = current_time
                
                # Determine if late (assuming 8:00 AM cutoff)
                cutoff_time = datetime_time(8, 0)
                if current_time > cutoff_time:
                    attendance.status = 'LATE'
                else:
                    attendance.status = 'ON TIME'
                
                attendance.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Time in recorded for {student.first_name} {student.last_name}',
                    'status': attendance.status,
                    'time': current_time.strftime('%I:%M %p')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Already timed in today'
                }, status=400)
        
        elif attendance_type == 'time_out':
            # Record time out
            if attendance.time_in and not attendance.time_out:
                attendance.time_out = current_time
                attendance.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Time out recorded for {student.first_name} {student.last_name}',
                    'time': current_time.strftime('%I:%M %p')
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
