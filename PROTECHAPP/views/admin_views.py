from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.core.paginator import Paginator
from django.db.models import Q, Count
from PROTECHAPP.models import CustomUser, Student, Section, Grade, Guardian, Attendance, UserRole, UserStatus, ExcusedAbsence, AdvisoryAssignment
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password
import json
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage

def is_admin(user):
    """Check if the logged-in user is an admin"""
    return user.is_authenticated and user.role == UserRole.ADMIN

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """View for admin dashboard"""
    context = {
        'current_date': timezone.now(),
        'user_count': CustomUser.objects.count(),
        'student_count': Student.objects.count(),
        'teacher_count': CustomUser.objects.filter(role=UserRole.TEACHER).count(),
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_users(request):
    """View for user management with filtering, searching and pagination"""
    # Get query parameters
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    page_number = request.GET.get('page', 1)
    items_per_page = request.GET.get('items_per_page', 10)
    sort_by = request.GET.get('sort_by', '-created_at')
    
    # Valid sorting fields - remove status and add is_active
    valid_sort_fields = ['username', '-username', 'email', '-email', 
                         'first_name', '-first_name', 'last_name', '-last_name',
                         'role', '-role', 'is_active', '-is_active', 
                         'created_at', '-created_at']
    
    if sort_by not in valid_sort_fields:
        sort_by = '-created_at'
    
    # Base queryset
    users = CustomUser.objects.all().order_by(sort_by)
    
    # Apply search if provided
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        )
    
    # Apply role filter if provided
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Apply status filter (now using is_active instead of status)
    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
    
    # Get total users before pagination for stats
    total_filtered = users.count()
    total_users = CustomUser.objects.count()
    
    # Get role distribution for dashboard widgets
    role_stats = CustomUser.objects.values('role').annotate(count=Count('id'))
    active_stats = CustomUser.objects.values('is_active').annotate(count=Count('id'))
    
    # Create dictionaries for easy template access
    role_counts = {role[0]: 0 for role in UserRole.choices}
    
    for stat in role_stats:
        role_counts[stat['role']] = stat['count']
    
    # Create active/inactive counts
    active_count = 0
    inactive_count = 0
    
    for stat in active_stats:
        if stat['is_active']:
            active_count = stat['count']
        else:
            inactive_count = stat['count']
    
    # Get recently added users for the sidebar
    recent_users = CustomUser.objects.order_by('-created_at')[:5]
    
    # Parse items_per_page as integer with validation
    try:
        items_per_page = int(items_per_page)
        if items_per_page <= 0:
            items_per_page = 10
    except (ValueError, TypeError):
        items_per_page = 10
    
    # Pagination
    paginator = Paginator(users, items_per_page)
    page_obj = paginator.get_page(page_number)
    
    # Calculate page range for pagination UI
    page_range = get_pagination_range(paginator, page_obj.number, 5)
    
    # Create simple status choices for the template
    status_choices = [
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ]
    
    context = {
        'users': page_obj,
        'role_choices': UserRole.choices,
        'status_choices': status_choices,  # Simple active/inactive choices
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'user_count': total_users,
        'total_filtered': total_filtered,
        'role_counts': role_counts,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'recent_users': recent_users,
        'page_range': page_range,
        'items_per_page': items_per_page,
        'items_per_page_options': [10, 25, 50, 100],
        'sort_options': [
            {'field': 'username', 'label': 'Username (A-Z)'},
            {'field': '-username', 'label': 'Username (Z-A)'},
            {'field': 'email', 'label': 'Email (A-Z)'},
            {'field': '-email', 'label': 'Email (Z-A)'},
            {'field': 'first_name', 'label': 'First Name (A-Z)'},
            {'field': '-first_name', 'label': 'First Name (Z-A)'},
            {'field': 'created_at', 'label': 'Created (Oldest First)'},
            {'field': '-created_at', 'label': 'Created (Newest First)'},
        ],
        # Add sections for modal dropdown
        'sections': Section.objects.select_related('grade').order_by('grade__name', 'name'),
        # Order grades by numeric value rather than alphabetically
        'grades': Grade.objects.all().order_by('name'),
    }
    return render(request, 'admin/users.html', context)

def get_pagination_range(paginator, current_page, display_range=5):
    """
    Calculate pagination range to display in the template
    This creates a better UX by showing ellipsis for large page sets
    """
    total_pages = paginator.num_pages
    
    # If total pages is less than display range, show all pages
    if total_pages <= display_range:
        return range(1, total_pages + 1)
    
    # Calculate the range to display
    start_page = max(current_page - display_range // 2, 1)
    end_page = min(start_page + display_range - 1, total_pages)
    
    # Adjust if we're near the end
    if end_page - start_page + 1 < display_range:
        start_page = max(end_page - display_range + 1, 1)
    
    return range(start_page, end_page + 1)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_user(request):
    """API endpoint to create a new user"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields - remove status, add is_active
        required_fields = ['username', 'email', 'first_name', 'last_name', 'password', 'role']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'status': 'error', 'message': f'{field} is required'}, status=400)
        
        # Check if username or email already exists
        if CustomUser.objects.filter(username=data['username']).exists():
            return JsonResponse({'status': 'error', 'message': 'Username already exists'}, status=400)
        
        if CustomUser.objects.filter(email=data['email']).exists():
            return JsonResponse({'status': 'error', 'message': 'Email already exists'}, status=400)
        
        # Create user with is_active instead of status
        user = CustomUser.objects.create(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            middle_name=data.get('middle_name', ''),
            role=data['role'],
            is_active=data.get('is_active', True),  # Default to active if not specified
            password=make_password(data['password'])
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'User created successfully',
            'user_id': user.id
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def get_user(request, user_id):
    """API endpoint to get a single user's details"""
    try:
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Build the user data with additional fields
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'middle_name': user.middle_name or '',
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'profile_pic': user.profile_pic,  # Add profile pic path
        }
        
        # Add section and grade data if the user is a teacher with assigned section
        if user.role == UserRole.TEACHER and user.section:
            user_data['section'] = user.section.id
            user_data['grade'] = user.section.grade.id
        
        return JsonResponse({'status': 'success', 'user': user_data})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT", "PATCH"])
def update_user(request, user_id):
    """API endpoint to update a user"""
    try:
        user = get_object_or_404(CustomUser, id=user_id)
        data = json.loads(request.body)
        
        # Update fields if provided
        if 'username' in data and data['username'] != user.username:
            if CustomUser.objects.filter(username=data['username']).exists():
                return JsonResponse({'status': 'error', 'message': 'Username already exists'}, status=400)
            user.username = data['username']
            
        if 'email' in data and data['email'] != user.email:
            if CustomUser.objects.filter(email=data['email']).exists():
                return JsonResponse({'status': 'error', 'message': 'Email already exists'}, status=400)
            user.email = data['email']
        
        # Update other fields
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.middle_name = data.get('middle_name', user.middle_name)
        user.role = data.get('role', user.role)
        
        # Update is_active instead of status
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        user.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'User updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def delete_user(request, user_id):
    """API endpoint to delete a user"""
    try:
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Don't allow deleting yourself
        if request.user.id == user.id:
            return JsonResponse({
                'status': 'error', 
                'message': 'You cannot delete your own account'
            }, status=400)
            
        # Store the username for the success message
        username = user.username
        
        # Delete the user
        user.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'User {username} deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def reset_user_password(request, user_id):
    """API endpoint to reset a user's password"""
    try:
        user = get_object_or_404(CustomUser, id=user_id)
        data = json.loads(request.body)
        
        # Validate new password
        new_password = data.get('new_password')
        if not new_password or len(new_password) < 8:
            return JsonResponse({
                'status': 'error', 
                'message': 'Password must be at least 8 characters long'
            }, status=400)
            
        # Update password
        user.password = make_password(new_password)
        user.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Password for {user.username} has been reset successfully'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def admin_teachers(request):
    """View for teacher management with filtering and section assignment"""
    # Get query parameters
    search_query = request.GET.get('search', '')
    advisory_filter = request.GET.get('advisory', '')
    section_filter = request.GET.get('section', '')
    status_filter = request.GET.get('status', '')
    page_number = request.GET.get('page', 1)
    
    # Base queryset - only teachers
    teachers = CustomUser.objects.filter(role=UserRole.TEACHER).order_by('first_name', 'last_name')
    
    # Apply search if provided
    if search_query:
        teachers = teachers.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        )
    
    # Apply status filter if provided
    if status_filter:
        teachers = teachers.filter(status=status_filter)
    
    # Get all advisory assignments for later use
    advisory_assignments = AdvisoryAssignment.objects.select_related('section', 'section__grade')
    
    # Create a dictionary of teacher_id -> section for quick lookup
    teacher_sections = {}
    for assignment in advisory_assignments:
        teacher_sections[assignment.teacher_id] = {
            'section': assignment.section,
            'section_id': assignment.section_id,
            'section_name': assignment.section.name,
            'grade_name': assignment.section.grade.name
        }
    
    # Get all available sections for assignment dropdown
    all_sections = Section.objects.select_related('grade').order_by('grade__name', 'name')
    
    # Filter by advisory status
    if advisory_filter == 'advisory':
        teachers = teachers.filter(id__in=teacher_sections.keys())
    elif advisory_filter == 'non-advisory':
        teachers = teachers.exclude(id__in=teacher_sections.keys())
    
    # Filter by section
    if section_filter:
        # Find teachers assigned to this section
        section_id = int(section_filter)
        teacher_ids = [teacher_id for teacher_id, data in teacher_sections.items() 
                       if data['section_id'] == section_id]
        teachers = teachers.filter(id__in=teacher_ids)
    
    # Get counts for dashboard
    total_teachers = CustomUser.objects.filter(role=UserRole.TEACHER).count()
    advisory_teachers_count = AdvisoryAssignment.objects.values('teacher').distinct().count()
    non_advisory_teachers_count = total_teachers - advisory_teachers_count
    active_teachers_count = CustomUser.objects.filter(role=UserRole.TEACHER, status=UserStatus.APPROVED).count()
    
    # Pagination
    paginator = Paginator(teachers, 10)
    page_obj = paginator.get_page(page_number)
    
    # Calculate page range for pagination UI
    page_range = get_pagination_range(paginator, page_obj.number, 5)
    
    context = {
        'teachers': page_obj,
        'teacher_sections': teacher_sections,
        'sections': all_sections,
        'status_choices': UserStatus.choices,
        'search_query': search_query,
        'advisory_filter': advisory_filter,
        'section_filter': section_filter,
        'status_filter': status_filter,
        'total_teachers': total_teachers,
        'advisory_teachers_count': advisory_teachers_count,
        'non_advisory_teachers_count': non_advisory_teachers_count,
        'active_teachers_count': active_teachers_count,
        'page_range': page_range
    }
    return render(request, 'admin/teachers.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def assign_teacher_section(request):
    """API endpoint to assign a teacher to a section as advisor"""
    try:
        data = json.loads(request.body)
        
        teacher_id = data.get('teacher_id')
        section_id = data.get('section_id')
        
        if not teacher_id or not section_id:
            return JsonResponse({'status': 'error', 'message': 'Teacher ID and Section ID are required'}, status=400)
        
        # Validate teacher is a teacher
        teacher = get_object_or_404(CustomUser, id=teacher_id, role=UserRole.TEACHER)
        section = get_object_or_404(Section, id=section_id)
        
        # Check if section already has an advisor
        existing_assignment = AdvisoryAssignment.objects.filter(section=section).first()
        if existing_assignment:
            return JsonResponse({
                'status': 'error', 
                'message': f'Section already has an advisor: {existing_assignment.teacher.first_name} {existing_assignment.teacher.last_name}'
            }, status=400)
        
        # Check if teacher is already assigned to another section
        existing_teacher_assignment = AdvisoryAssignment.objects.filter(teacher=teacher).first()
        if existing_teacher_assignment:
            return JsonResponse({
                'status': 'error', 
                'message': f'Teacher is already assigned to {existing_teacher_assignment.section.name}'
            }, status=400)
            
        # Create assignment
        assignment = AdvisoryAssignment.objects.create(
            teacher=teacher,
            section=section
        )
        
        # Also update teacher's section field
        teacher.section = section
        teacher.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Teacher {teacher.first_name} {teacher.last_name} assigned as advisor to {section.name}',
            'assignment_id': assignment.id
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def remove_teacher_section(request):
    """API endpoint to remove a teacher from advisory role"""
    try:
        data = json.loads(request.body)
        
        teacher_id = data.get('teacher_id')
        
        if not teacher_id:
            return JsonResponse({'status': 'error', 'message': 'Teacher ID is required'}, status=400)
        
        # Validate teacher is a teacher
        teacher = get_object_or_404(CustomUser, id=teacher_id, role=UserRole.TEACHER)
        
        # Find and delete assignment
        assignment = AdvisoryAssignment.objects.filter(teacher=teacher).first()
        if assignment:
            section_name = assignment.section.name
            assignment.delete()
            
            # Also update teacher's section field
            teacher.section = None
            teacher.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'Teacher {teacher.first_name} {teacher.last_name} removed as advisor from {section_name}'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Teacher is not an advisor to any section'
            }, status=400)
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def admin_grades(request):
    """View for grade management"""
    grades = Grade.objects.all()
    context = {
        'grades': grades
    }
    return render(request, 'admin/grades.html', context)

@login_required
@user_passes_test(is_admin)
def admin_sections(request):
    """View for section management"""
    sections = Section.objects.all()
    context = {
        'sections': sections
    }
    return render(request, 'admin/sections.html', context)

@login_required
@user_passes_test(is_admin)
def admin_students(request):
    """View for student management"""
    students = Student.objects.all()
    context = {
        'students': students
    }
    return render(request, 'admin/students.html', context)

@login_required
@user_passes_test(is_admin)
def admin_guardians(request):
    """View for guardian management"""
    guardians = Guardian.objects.all()
    context = {
        'guardians': guardians
    }
    return render(request, 'admin/guardians.html', context)

@login_required
@user_passes_test(is_admin)
def admin_attendance(request):
    """View for attendance management"""
    today = timezone.now().date()
    attendance_records = Attendance.objects.filter(date=today)
    context = {
        'attendance_records': attendance_records
    }
    return render(request, 'admin/attendance.html', context)

@login_required
@user_passes_test(is_admin)
def admin_excused(request):
    """View for ecused absences management"""
    excused_absences = ExcusedAbsence.objects.all()
    context = {
        'excused_absences': excused_absences
    }
    return render(request, 'admin/excused.html', context)

@login_required
@user_passes_test(is_admin)
def admin_settings(request):
    """View for system settings"""
    return render(request, 'admin/settings.html')

# Create profile pics directory if it doesn't exist
PROFILE_PICS_DIR = os.path.join(settings.BASE_DIR, 'private_profile_pics')
os.makedirs(PROFILE_PICS_DIR, exist_ok=True)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def upload_profile_pic(request):
    """API endpoint to upload a profile picture"""
    try:
        if 'profile_pic' not in request.FILES:
            return JsonResponse({'status': 'error', 'message': 'No file uploaded'}, status=400)
            
        # Check for user_id in POST data (required)
        user_id = request.POST.get('user_id')
        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'User ID is required'}, status=400)
            
        # Verify user exists
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
            
        uploaded_file = request.FILES['profile_pic']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if uploaded_file.content_type not in allowed_types:
            return JsonResponse({'status': 'error', 'message': 'Invalid file type. Only JPEG, PNG, and GIF images are allowed.'}, status=400)
            
        # Validate file size (max 5MB)
        if uploaded_file.size > 5 * 1024 * 1024:
            return JsonResponse({'status': 'error', 'message': 'File too large. Maximum file size is 5MB.'}, status=400)
        
        # Create a safe filename
        import uuid
        file_name = f"{uuid.uuid4()}_{uploaded_file.name}"
        
        # Save file to private directory
        fs = FileSystemStorage(location=PROFILE_PICS_DIR)
        filename = fs.save(file_name, uploaded_file)
        
        # Store just the filename in the user model, not the full path
        user.profile_pic = filename
        user.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Profile picture uploaded successfully',
            'file_path': filename
        })
    
    except Exception as e:
        import traceback
        print(f"Error uploading profile picture: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def serve_profile_pic(request, path):
    """View to securely serve profile pictures from private directory"""
    try:
        # The path parameter should now just be the filename
        filename = path
        
        # Construct the full file path
        file_path = os.path.join(PROFILE_PICS_DIR, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            # Provide a default image or 404
            default_pic_path = os.path.join(settings.STATIC_ROOT, 'images', 'default_profile.png')
            if os.path.exists(default_pic_path):
                with open(default_pic_path, 'rb') as image_file:
                    return HttpResponse(image_file.read(), content_type='image/png')
            return HttpResponseNotFound("Profile picture not found")
        
        # Determine content type based on file extension
        content_type = 'image/jpeg'  # Default
        if filename.lower().endswith('.png'):
            content_type = 'image/png'
        elif filename.lower().endswith('.gif'):
            content_type = 'image/gif'
        
        # Serve the file
        with open(file_path, 'rb') as image_file:
            return HttpResponse(image_file.read(), content_type=content_type)
    except Exception as e:
        import traceback
        print(f"Error serving image: {str(e)}")
        print(traceback.format_exc())
        return HttpResponseNotFound("Error serving profile picture")
