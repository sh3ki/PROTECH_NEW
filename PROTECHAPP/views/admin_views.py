from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.core.paginator import Paginator
from django.db.models import Q, Count
from PROTECHAPP.models import CustomUser, Student, Section, Grade, Guardian, Attendance, UserRole, UserStatus, ExcusedAbsence, AdvisoryAssignment
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth.hashers import make_password
import json
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage

def is_admin(user):
    """Check if the logged-in user is an admin"""
    return user.is_authenticated and user.role == UserRole.ADMIN


# ==========================
#  USER MANAGEMENT VIEWS
# ==========================

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
        
        # Validate required fields
        required_fields = ['username', 'email', 'first_name', 'last_name', 'password', 'role']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'status': 'error', 'message': f'{field} is required'}, status=400)
        
        # Check if username or email already exists
        if CustomUser.objects.filter(username=data['username']).exists():
            return JsonResponse({'status': 'error', 'message': 'Username already exists'}, status=400)
        
        if CustomUser.objects.filter(email=data['email']).exists():
            return JsonResponse({'status': 'error', 'message': 'Email already exists'}, status=400)
        
        # Create user with basic fields
        user = CustomUser(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            middle_name=data.get('middle_name', ''),
            role=data['role'],
            is_active=data.get('is_active', True)  # Default to active if not specified
        )
        
        # Set password
        user.password = make_password(data['password'])
        
        # Handle section assignment for teachers
        if data['role'] == UserRole.TEACHER and 'section' in data and data['section']:
            try:
                section = Section.objects.get(id=data['section'])
                user.section = section
            except Section.DoesNotExist:
                pass  # Silently ignore invalid section IDs
        
        user.save()
        
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
        
        # Handle section assignment for teachers
        if user.role == UserRole.TEACHER:
            if 'section' in data and data['section']:
                try:
                    section = Section.objects.get(id=data['section'])
                    user.section = section
                except Section.DoesNotExist:
                    pass  # Silently ignore invalid section IDs
            else:
                # Clear section if not provided or empty
                user.section = None
        else:
            # Non-teachers should not have sections
            user.section = None
        
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
def search_users(request):
    """API endpoint to search and filter users for AJAX requests"""
    # Get query parameters
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    page_number = request.GET.get('page', 1)
    items_per_page = request.GET.get('items_per_page', 10)
    sort_by = request.GET.get('sort_by', '-created_at')
    
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
    
    # Apply status filter
    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
    
    # Get total count for pagination
    total_count = users.count()
    
    # Parse page number and items_per_page
    try:
        page_number = int(page_number)
        items_per_page = int(items_per_page)
    except (ValueError, TypeError):
        page_number = 1
        items_per_page = 10
    
    # Create paginator
    paginator = Paginator(users, items_per_page)
    page_obj = paginator.get_page(page_number)
    
    # Prepare user data for JSON response
    user_data = []
    for user in page_obj:
        user_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'role_display': user.get_role_display(),
            'is_active': user.is_active,
            'created_at': user.created_at.strftime('%Y-%m-%d'),
            'created_at_display': user.created_at.strftime('%b %d, %Y'),
            'profile_pic': user.profile_pic,
        })
    
    # Prepare pagination data
    pagination = {
        'current_page': page_obj.number,
        'num_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'page_range': list(get_pagination_range(paginator, page_obj.number, 5)),
        'start_index': page_obj.start_index(),
        'end_index': page_obj.end_index(),
        'total_count': total_count,
    }
    
    return JsonResponse({
        'status': 'success',
        'users': user_data,
        'pagination': pagination,
        'total_count': total_count,
    })


# ==========================
#  TEACHER MANAGEMENT VIEWS
# ==========================

@login_required
@user_passes_test(is_admin)
def admin_teachers(request):
    """View for teacher management with filtering and section assignment"""
    # Get query parameters
    search_query = request.GET.get('search', '')
    advisory_filter = request.GET.get('advisory', '')
    status_filter = request.GET.get('status', '')
    section_filter = request.GET.get('section', '')
    page_number = request.GET.get('page', 1)

    # Base queryset - only teachers, order by created_at DESC (newest first)
    teachers = CustomUser.objects.filter(role=UserRole.TEACHER).select_related('section', 'section__grade').order_by('-created_at')

    # Apply search if provided
    if search_query:
        teachers = teachers.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        )

    # Apply status filter using is_active
    if status_filter:
        if status_filter == 'active':
            teachers = teachers.filter(is_active=True)
        elif status_filter == 'inactive':
            teachers = teachers.filter(is_active=False)

    # Get all advisory assignments for later use
    advisory_assignments = AdvisoryAssignment.objects.select_related('section', 'section__grade')

    # Create a dictionary of teacher_id -> section for quick lookup
    teacher_sections = {}
    for assignment in advisory_assignments:
        teacher_sections[assignment.teacher_id] = {
            'section': assignment.section,
            'section_id': assignment.section_id,
            'section_name': assignment.section.name,
            'grade_id': assignment.section.grade.id,
            'grade_name': assignment.section.grade.name
        }

    # Get all available sections for assignment dropdown
    all_sections = Section.objects.select_related('grade').order_by('grade__name', 'name')

    # Filter by advisory status
    if advisory_filter == 'advisory':
        teachers = teachers.filter(Q(id__in=teacher_sections.keys()) | Q(section__isnull=False))
    elif advisory_filter == 'non-advisory':
        teachers = teachers.exclude(Q(id__in=teacher_sections.keys()) | Q(section__isnull=False))

    # Filter by section (if needed)
    if section_filter:
        try:
            section_id = int(section_filter)
            teacher_ids = [teacher_id for teacher_id, data in teacher_sections.items() 
                           if data['section_id'] == section_id]
            teachers = teachers.filter(Q(id__in=teacher_ids) | Q(section_id=section_id))
        except Exception:
            pass

    # Get counts for dashboard
    total_teachers = CustomUser.objects.filter(role=UserRole.TEACHER).count()
    advisory_teachers = CustomUser.objects.filter(
        Q(role=UserRole.TEACHER) & 
        (Q(id__in=AdvisoryAssignment.objects.values('teacher')) | Q(section__isnull=False))
    ).distinct()
    advisory_teachers_count = advisory_teachers.count()
    non_advisory_teachers_count = total_teachers - advisory_teachers_count
    active_teachers_count = CustomUser.objects.filter(role=UserRole.TEACHER, is_active=True).count()

    # Pagination
    paginator = Paginator(teachers, 10)
    page_obj = paginator.get_page(page_number)

    # Calculate page range for pagination UI
    page_range = get_pagination_range(paginator, page_obj.number, 5)

    # Annotate each teacher in the page with section/grade info and advisory status
    for teacher in page_obj:
        section_info = teacher_sections.get(teacher.id)
        teacher.is_advisory = bool(section_info) or teacher.section is not None
        if section_info:
            teacher.section_name = section_info['section_name']
            teacher.grade_name = section_info['grade_name']
            teacher.section_id = section_info['section_id']
            teacher.grade_id = section_info['grade_id']
        elif teacher.section:
            teacher.section_name = teacher.section.name
            teacher.grade_name = teacher.section.grade.name
            teacher.section_id = teacher.section.id
            teacher.grade_id = teacher.section.grade.id
        else:
            teacher.section_name = None
            teacher.grade_name = None
            teacher.section_id = None
            teacher.grade_id = None
        # Add status for frontend
        teacher.status = 'Active' if teacher.is_active else 'Inactive'

    context = {
        'teachers': page_obj,
        'teacher_sections': teacher_sections,
        'sections': all_sections,
        'grades': Grade.objects.all().order_by('name'), 
        'status_choices': [('active', 'Active'), ('inactive', 'Inactive')],
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
@require_GET
def search_teachers(request):
    """API endpoint to search/filter/paginate teachers for AJAX requests"""
    search_query = request.GET.get('search', '')
    advisory_filter = request.GET.get('advisory', '')
    status_filter = request.GET.get('status', '')
    section_filter = request.GET.get('section', '')
    page_number = request.GET.get('page', 1)
    items_per_page = request.GET.get('items_per_page', 10)

    teachers = CustomUser.objects.filter(role=UserRole.TEACHER).select_related('section', 'section__grade').order_by('-created_at')

    if search_query:
        teachers = teachers.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # Status filter
    if status_filter:
        if status_filter == 'active':
            teachers = teachers.filter(is_active=True)
        elif status_filter == 'inactive':
            teachers = teachers.filter(is_active=False)

    advisory_assignments = AdvisoryAssignment.objects.select_related('section', 'section__grade')
    teacher_sections = {}
    for assignment in advisory_assignments:
        teacher_sections[assignment.teacher_id] = {
            'section': assignment.section,
            'section_id': assignment.section_id,
            'section_name': assignment.section.name,
            'grade_id': assignment.section.grade.id,
            'grade_name': assignment.section.grade.name
        }

    if advisory_filter == 'advisory':
        teachers = teachers.filter(Q(id__in=teacher_sections.keys()) | Q(section__isnull=False))
    elif advisory_filter == 'non-advisory':
        teachers = teachers.exclude(Q(id__in=teacher_sections.keys()) | Q(section__isnull=False))

    if section_filter:
        try:
            section_id = int(section_filter)
            teacher_ids = [tid for tid, data in teacher_sections.items() if data['section_id'] == section_id]
            teachers = teachers.filter(Q(id__in=teacher_ids) | Q(section_id=section_id))
        except Exception:
            pass

    paginator = Paginator(teachers, items_per_page)
    page_obj = paginator.get_page(page_number)

    teacher_data = []
    for teacher in page_obj:
        section_info = teacher_sections.get(teacher.id)
        grade = None
        section = None
        grade_id = None
        section_id = None
        is_advisory = bool(section_info) or teacher.section is not None
        if section_info:
            grade = section_info['grade_name']
            section = section_info['section_name']
            grade_id = section_info['grade_id']
            section_id = section_info['section_id']
        elif teacher.section:
            grade = teacher.section.grade.name
            section = teacher.section.name
            grade_id = teacher.section.grade.id
            section_id = teacher.section.id
        teacher_data.append({
            'id': teacher.id,
            'username': teacher.username,
            'email': teacher.email,
            'first_name': teacher.first_name,
            'last_name': teacher.last_name,
            'profile_pic': teacher.profile_pic,
            'created_at': teacher.created_at.strftime('%Y-%m-%d'),
            'created_at_display': teacher.created_at.strftime('%b %d, %Y'),
            'advisory': is_advisory,
            'section': section,
            'section_id': section_id,
            'grade': grade,
            'grade_id': grade_id,
            'is_active': teacher.is_active,  # Include status for frontend
            'status': 'Active' if teacher.is_active else 'Inactive'
        })

    pagination = {
        'current_page': page_obj.number,
        'num_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'page_range': list(get_pagination_range(paginator, page_obj.number, 5)),
        'start_index': page_obj.start_index(),
        'end_index': page_obj.end_index(),
        'total_count': paginator.count,
    }

    return JsonResponse({
        'status': 'success',
        'teachers': teacher_data,
        'pagination': pagination,
        'total_count': paginator.count,
    })


# ==========================
#  GRADE MANAGEMENT VIEWS
# ==========================

@login_required
@user_passes_test(is_admin)
def admin_grades(request):
    """View for grade management"""
    # Get query parameters
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)
    
    # Base queryset - order by created_at DESC (newest first)
    grades = Grade.objects.all().order_by('-created_at')
    
    # Apply search if provided
    if search_query:
        grades = grades.filter(name__icontains=search_query)
    
    # Annotate with section and student counts
    grades = grades.annotate(
        sections_count=Count('sections'),
        students_count=Count('sections__students', distinct=True)
    )
    
    # Get stats for dashboard
    total_grades = Grade.objects.count()
    grades_with_sections = Grade.objects.filter(sections__isnull=False).distinct().count()
    total_sections = Section.objects.count()
    total_students = Student.objects.count()
    
    # Pagination
    paginator = Paginator(grades, 10)
    page_obj = paginator.get_page(page_number)
    
    # Calculate page range for pagination UI
    page_range = get_pagination_range(paginator, page_obj.number, 5)
    
    context = {
        'grades': page_obj,
        'search_query': search_query,
        'total_grades': total_grades,
        'grades_with_sections': grades_with_sections,
        'total_sections': total_sections,
        'total_students': total_students,
        'page_range': page_range,
    }
    return render(request, 'admin/grades.html', context)

@login_required
@user_passes_test(is_admin)
@require_GET
def search_grades(request):
    """AJAX search/filter for grades"""
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)
    items_per_page = request.GET.get('items_per_page', 10)
    
    # Base queryset - order by created_at DESC (newest first)
    grades = Grade.objects.all().order_by('-created_at')
    
    # Apply search if provided
    if search_query:
        grades = grades.filter(name__icontains=search_query)
    
    # Annotate with counts (fix: use distinct for sections_count)
    grades = grades.annotate(
        sections_count=Count('sections', distinct=True),
        students_count=Count('sections__students', distinct=True)
    )
    
    # Get total count for pagination
    total_count = grades.count()
    
    # Parse page number and items_per_page
    try:
        page_number = int(page_number)
        items_per_page = int(items_per_page)
    except (ValueError, TypeError):
        page_number = 1
        items_per_page = 10
    
    # Create paginator
    paginator = Paginator(grades, items_per_page)
    page_obj = paginator.get_page(page_number)
    
    # Prepare grade data for JSON response
    grade_data = []
    for grade in page_obj:
        grade_data.append({
            'id': grade.id,
            'name': grade.name,
            'sections_count': grade.sections_count,
            'students_count': grade.students_count,
            'created_at': grade.created_at.strftime('%Y-%m-%d'),
            'created_at_display': grade.created_at.strftime('%b %d, %Y'),
        })
    
    # Prepare pagination data
    pagination = {
        'current_page': page_obj.number,
        'num_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'page_range': list(get_pagination_range(paginator, page_obj.number, 5)),
        'start_index': page_obj.start_index(),
        'end_index': page_obj.end_index(),
        'total_count': total_count,
    }
    
    return JsonResponse({
        'status': 'success',
        'grades': grade_data,
        'pagination': pagination,
        'total_count': total_count,
    })

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_grade(request):
    """Create a new grade"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        
        if not name:
            return JsonResponse({'status': 'error', 'message': 'Grade name is required.'}, status=400)
        
        if Grade.objects.filter(name__iexact=name).exists():
            return JsonResponse({'status': 'error', 'message': 'Grade with this name already exists.'}, status=400)
        
        grade = Grade.objects.create(name=name)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Grade "{name}" created successfully.',
            'grade': {
                'id': grade.id,
                'name': grade.name,
                'sections_count': 0,
                'students_count': 0,
                'created_at': grade.created_at.strftime('%Y-%m-%d'),
                'created_at_display': grade.created_at.strftime('%b %d, %Y'),
            }
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["PATCH"])
def update_grade(request, grade_id):
    """Update an existing grade"""
    try:
        grade = get_object_or_404(Grade, id=grade_id)
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        
        if not name:
            return JsonResponse({'status': 'error', 'message': 'Grade name is required.'}, status=400)
        
        if Grade.objects.filter(name__iexact=name).exclude(id=grade_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Another grade with this name already exists.'}, status=400)
        
        old_name = grade.name
        grade.name = name
        grade.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Grade "{old_name}" updated to "{name}" successfully.'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def delete_grade(request, grade_id):
    """Delete a grade"""
    try:
        grade = get_object_or_404(Grade, id=grade_id)
        
        # Check if grade has sections
        sections_count = grade.sections.count()
        students_count = Student.objects.filter(grade=grade).count()
        
        if sections_count > 0 or students_count > 0:
            return JsonResponse({
                'status': 'error', 
                'message': f'Cannot delete grade "{grade.name}" because it has {sections_count} section(s) and {students_count} student(s). Please remove all sections and students first.'
            }, status=400)
        
        grade_name = grade.name
        grade.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Grade "{grade_name}" deleted successfully.'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_GET
def get_grade_sections(request, grade_id):
    """Get sections for a specific grade"""
    try:
        grade = get_object_or_404(Grade, id=grade_id)
        sections = Section.objects.filter(grade=grade).annotate(
            students_count=Count('students')
        ).order_by('name')
        
        sections_data = []
        for section in sections:
            sections_data.append({
                'id': section.id,
                'name': section.name,
                'students_count': section.students_count,
                'created_at': section.created_at.strftime('%b %d, %Y'),
            })
        
        return JsonResponse({
            'status': 'success',
            'grade': {
                'id': grade.id,
                'name': grade.name
            },
            'sections': sections_data,
            'total_sections': len(sections_data)
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ==========================
#  SECTION MANAGEMENT VIEWS
# ==========================

@login_required
@user_passes_test(is_admin)
def admin_sections(request):
    """View for section management"""
    # Get query parameters
    search_query = request.GET.get('search', '')
    grade_filter = request.GET.get('grade', '')
    advisor_filter = request.GET.get('advisor', '')
    page_number = request.GET.get('page', 1)
    
    # Base queryset - order by created_at DESC (newest first)
    sections = Section.objects.select_related('grade').order_by('-created_at')
    
    # Apply search if provided
    if search_query:
        sections = sections.filter(
            Q(name__icontains=search_query) | 
            Q(grade__name__icontains=search_query)
        )
    
    # Apply grade filter if provided
    if grade_filter:
        try:
            grade_id = int(grade_filter)
            sections = sections.filter(grade_id=grade_id)
        except (ValueError, TypeError):
            pass
    
    # Apply advisor filter if provided
    if advisor_filter:
        if advisor_filter == 'with_advisor':
            sections = sections.filter(advisory_assignments__isnull=False).distinct()
        elif advisor_filter == 'without_advisor':
            sections = sections.filter(advisory_assignments__isnull=True)
    
    # Annotate with student counts and teacher info
    sections = sections.annotate(
        students_count=Count('students')
    ).prefetch_related('advisory_assignments__teacher')
    
    # Get stats for dashboard
    total_sections = Section.objects.count()
    sections_with_students = Section.objects.filter(students__isnull=False).distinct().count()
    sections_with_advisors = Section.objects.filter(advisory_assignments__isnull=False).distinct().count()
    total_students = Student.objects.count()
    
    # Get all grades for filter dropdown
    all_grades = Grade.objects.all().order_by('name')
    
    # Pagination
    paginator = Paginator(sections, 10)
    page_obj = paginator.get_page(page_number)
    
    # Calculate page range for pagination UI
    page_range = get_pagination_range(paginator, page_obj.number, 5)
    
    context = {
        'sections': page_obj,
        'grades': all_grades,
        'search_query': search_query,
        'grade_filter': grade_filter,
        'advisor_filter': advisor_filter,
        'total_sections': total_sections,
        'sections_with_students': sections_with_students,
        'sections_with_advisors': sections_with_advisors,
        'total_students': total_students,
        'page_range': page_range,
    }
    return render(request, 'admin/sections.html', context)

@login_required
@user_passes_test(is_admin)
@require_GET
def search_sections(request):
    """AJAX search/filter for sections"""
    search_query = request.GET.get('search', '')
    grade_filter = request.GET.get('grade', '')
    advisor_filter = request.GET.get('advisor', '')
    page_number = request.GET.get('page', 1)
    items_per_page = request.GET.get('items_per_page', 10)
    
    # Base queryset - order by created_at DESC (newest first)
    sections = Section.objects.select_related('grade').order_by('-created_at')
    
    # Apply search if provided
    if search_query:
        sections = sections.filter(
            Q(name__icontains=search_query) | 
            Q(grade__name__icontains=search_query)
        )
    
    # Apply grade filter if provided
    if grade_filter:
        try:
            grade_id = int(grade_filter)
            sections = sections.filter(grade_id=grade_id)
        except (ValueError, TypeError):
            pass
    
    # Apply advisor filter if provided
    if advisor_filter:
        if advisor_filter == 'with_advisor':
            sections = sections.filter(advisory_assignments__isnull=False).distinct()
        elif advisor_filter == 'without_advisor':
            sections = sections.filter(advisory_assignments__isnull=True)
    
    # Annotate with counts and prefetch related data
    sections = sections.annotate(
        students_count=Count('students')
    ).prefetch_related('advisory_assignments__teacher')
    
    # Get total count for pagination
    total_count = sections.count()
    
    # Parse page number and items_per_page
    try:
        page_number = int(page_number)
        items_per_page = int(items_per_page)
    except (ValueError, TypeError):
        page_number = 1
        items_per_page = 10
    
    # Create paginator
    paginator = Paginator(sections, items_per_page)
    page_obj = paginator.get_page(page_number)

    # Prepare section data for JSON response
    section_data = []
    for section in page_obj:
        # Get advisor info
        advisor = None
        advisory_assignment = section.advisory_assignments.first()
        if advisory_assignment:
            advisor = {
                'id': advisory_assignment.teacher.id,
                'name': f"{advisory_assignment.teacher.first_name} {advisory_assignment.teacher.last_name}",
                'username': advisory_assignment.teacher.username
            }
        
        section_data.append({
            'id': section.id,
            'name': section.name,
            'grade_id': section.grade.id,
            'grade_name': section.grade.name,
            'students_count': section.students_count,
            'advisor': advisor,
            'created_at': section.created_at.strftime('%Y-%m-%d'),
            'created_at_display': section.created_at.strftime('%b %d, %Y'),
        })
    
    # Prepare pagination data
    pagination = {
        'current_page': page_obj.number,
        'num_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'page_range': list(get_pagination_range(paginator, page_obj.number, 5)),
        'start_index': page_obj.start_index(),
        'end_index': page_obj.end_index(),
        'total_count': total_count,
    }
    
    return JsonResponse({
        'status': 'success',
        'sections': section_data,
        'pagination': pagination,
        'total_count': total_count,
    })

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_section(request):
    """Create a new section"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        grade_id = data.get('grade_id')
        
        if not name:
            return JsonResponse({'status': 'error', 'message': 'Section name is required.'}, status=400)
        
        if not grade_id:
            return JsonResponse({'status': 'error', 'message': 'Grade is required.'}, status=400)
        
        # Check if grade exists
        try:
            grade = Grade.objects.get(id=grade_id)
        except Grade.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Selected grade does not exist.'}, status=400)
        
        # Check if section with same name exists in the same grade
        if Section.objects.filter(name__iexact=name, grade=grade).exists():
            return JsonResponse({'status': 'error', 'message': f'Section "{name}" already exists in {grade.name}.'}, status=400)
        
        section = Section.objects.create(name=name, grade=grade)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Section "{name}" created successfully in {grade.name}.',
            'section': {
                'id': section.id,
                'name': section.name,
                'grade_id': section.grade.id,
                'grade_name': section.grade.name,
                'students_count': 0,
                'advisor': None,
                'created_at': section.created_at.strftime('%Y-%m-%d'),
                'created_at_display': section.created_at.strftime('%b %d, %Y'),
            }
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["PATCH"])
def update_section(request, section_id):
    """Update an existing section"""
    try:
        section = get_object_or_404(Section, id=section_id)
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        grade_id = data.get('grade_id')
        
        if not name:
            return JsonResponse({'status': 'error', 'message': 'Section name is required.'}, status=400)
        
        if not grade_id:
            return JsonResponse({'status': 'error', 'message': 'Grade is required.'}, status=400)
        
        # Check if grade exists
        try:
            grade = Grade.objects.get(id=grade_id)
        except Grade.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Selected grade does not exist.'}, status=400)
        
        # Check if section with same name exists in the same grade (excluding current section)
        if Section.objects.filter(name__iexact=name, grade=grade).exclude(id=section_id).exists():
            return JsonResponse({'status': 'error', 'message': f'Section "{name}" already exists in {grade.name}.'}, status=400)
        
        old_name = section.name
        old_grade = section.grade.name
        section.name = name
        section.grade = grade
        section.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Section updated from "{old_name}" ({old_grade}) to "{name}" ({grade.name}) successfully.'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def delete_section(request, section_id):
    """Delete a section"""
    try:
        section = get_object_or_404(Section, id=section_id)
        
        # Check if section has students
        students_count = section.students.count()
        
        if students_count > 0:
            return JsonResponse({
                'status': 'error', 
                'message': f'Cannot delete section "{section.name}" because it has {students_count} student(s). Please move or remove all students first.'
            }, status=400)
        
        section_name = section.name
        grade_name = section.grade.name
        section.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Section "{section_name}" from {grade_name} deleted successfully.'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_GET
def get_section_students(request, section_id):
    """Get students for a specific section"""
    try:
        section = get_object_or_404(Section, id=section_id)
        students = Student.objects.filter(section=section).order_by('last_name', 'first_name')
        
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'lrn': student.lrn,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'full_name': f"{student.first_name} {student.last_name}",
                'status': student.status,
                'created_at': student.created_at.strftime('%b %d, %Y'),
            })
        
        return JsonResponse({
            'status': 'success',
            'section': {
                'id': section.id,
                'name': section.name,
                'grade_name': section.grade.name
            },
            'students': students_data,
            'total_students': len(students_data)
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ==========================
#  STUDENTS MANAGEMENT VIEWS
# ==========================

@login_required
@user_passes_test(is_admin)
def admin_students(request):
    """View for student management"""
    # Get query parameters
    search_query = request.GET.get('search', '')
    grade_filter = request.GET.get('grade', '')
    section_filter = request.GET.get('section', '')
    status_filter = request.GET.get('status', '')
    page_number = request.GET.get('page', 1)

    # Base queryset
    students = Student.objects.select_related('grade', 'section').all().order_by('-created_at')

    # Apply search
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(lrn__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Apply grade filter
    if grade_filter:
        students = students.filter(grade_id=grade_filter)

    # Apply section filter
    if section_filter:
        students = students.filter(section_id=section_filter)

    # Apply status filter
    if status_filter:
        students = students.filter(status=status_filter)

    # Dashboard stats
    total_students = Student.objects.count()
    active_students = Student.objects.filter(status='ACTIVE').count()
    inactive_students = Student.objects.filter(status='INACTIVE').count()
    face_enrolled_count = Student.objects.exclude(face_path__isnull=True).exclude(face_path__exact='').count()

    # For filter dropdowns
    grades = Grade.objects.all().order_by('name')
    sections = Section.objects.select_related('grade').order_by('grade__name', 'name')

    # Pagination
    paginator = Paginator(students, 10)
    page_obj = paginator.get_page(page_number)
    page_range = get_pagination_range(paginator, page_obj.number, 5)

    context = {
        'students': page_obj,
        'grades': grades,
        'sections': sections,
        'search_query': search_query,
        'grade_filter': grade_filter,
        'section_filter': section_filter,
        'status_filter': status_filter,
        'total_students': total_students,
        'active_students': active_students,
        'inactive_students': inactive_students,
        'face_enrolled_count': face_enrolled_count,
        'page_range': page_range,
    }
    return render(request, 'admin/students.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def search_students(request):
    """AJAX search/filter for students"""
    try:
        search_query = request.GET.get('search', '')
        grade_filter = request.GET.get('grade', '')
        section_filter = request.GET.get('section', '')
        status_filter = request.GET.get('status', '')
        page_number = request.GET.get('page', 1)
        items_per_page = request.GET.get('items_per_page', 10)

        students = Student.objects.select_related('grade', 'section').all().order_by('-created_at')

        if search_query:
            students = students.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(lrn__icontains=search_query)
            )
        if grade_filter:
            students = students.filter(grade_id=grade_filter)
        if section_filter:
            students = students.filter(section_id=section_filter)
        if status_filter:
            students = students.filter(status=status_filter)

        total_count = students.count()
        try:
            page_number = int(page_number)
            items_per_page = int(items_per_page)
        except (ValueError, TypeError):
            page_number = 1
            items_per_page = 10

        paginator = Paginator(students, items_per_page)
        page_obj = paginator.get_page(page_number)

        student_data = []
        for student in page_obj:
            # Complete the missing profile_pic handling code
            profile_pic = None
            if student.profile_pic:
                profile_pic = student.profile_pic

            student_data.append({
                'id': student.id,
                'lrn': student.lrn,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'full_name': f"{student.first_name} {student.last_name}",
                'grade': student.grade.name if student.grade else '',
                'grade_id': student.grade.id if student.grade else None,
                'section': student.section.name if student.section else '',
                'section_id': student.section.id if student.section else None,
                'status': student.status,
                'profile_pic': profile_pic,
                'created_at': student.created_at.strftime('%Y-%m-%d'),
                'created_at_display': student.created_at.strftime('%b %d, %Y'),
            })

        pagination = {
            'current_page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page_range': list(get_pagination_range(paginator, page_obj.number, 5)),
            'start_index': page_obj.start_index(),
            'end_index': page_obj.end_index(),
            'total_count': total_count,
        }

        return JsonResponse({
            'status': 'success',
            'students': student_data,
            'pagination': pagination,
            'total_count': total_count,
        })
    except Exception as e:
        import traceback
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_student(request):
    """Create a new student"""
    try:
        # Handle form data with file upload
        lrn = request.POST.get('lrn', '')
        first_name = request.POST.get('first_name', '')
        middle_name = request.POST.get('middle_name', '')
        last_name = request.POST.get('last_name', '')
        grade_id = request.POST.get('grade_id', '')
        section_id = request.POST.get('section_id', '')
        status = request.POST.get('status', 'ACTIVE')
        
        # Validate required fields
        if not lrn or not first_name or not last_name or not grade_id or not section_id:
            return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)
        
        # Check if LRN is unique
        if Student.objects.filter(lrn=lrn).exists():
            return JsonResponse({'status': 'error', 'message': 'LRN already exists'}, status=400)
        
        # Get grade and section objects
        try:
            grade = Grade.objects.get(id=grade_id)
            section = Section.objects.get(id=section_id)
        except (Grade.DoesNotExist, Section.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Invalid grade or section'}, status=400)
        
        # Create the student
        student = Student(
            lrn=lrn,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            grade=grade,
            section=section,
            status=status
        )
        
        # Handle profile picture if provided
        if 'profile_pic' in request.FILES:
            profile_pic = request.FILES['profile_pic']
            
            # Validate file size and type
            if profile_pic.size > 2 * 1024 * 1024:  # 2MB limit
                return JsonResponse({'status': 'error', 'message': 'File size must be less than 2MB'}, status=400)
            
            if not profile_pic.content_type.startswith('image/'):
                return JsonResponse({'status': 'error', 'message': 'Only image files are allowed'}, status=400)
            
            # Save the profile picture
            filename = f"student_{int(timezone.now().timestamp())}_{profile_pic.name}"
            fs = FileSystemStorage(location=PROFILE_PICS_DIR)
            filename = fs.save(filename, profile_pic)
            student.profile_pic = filename
        
        student.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Student {first_name} {last_name} created successfully',
            'student_id': student.id
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def get_student(request, student_id):
    """
    Endpoint to retrieve a specific student's data for editing
    """
    try:
        student = get_object_or_404(Student, id=student_id)
        
        # Build the student data for response
        student_data = {
            'id': student.id,
            'lrn': student.lrn,
            'first_name': student.first_name,
            'middle_name': student.middle_name or '',
            'last_name': student.last_name,
            'grade_id': str(student.grade.id) if student.grade else '',
            'grade': student.grade.name if student.grade else '',
            'section_id': str(student.section.id) if student.section else '',
            'section': student.section.name if student.section else '',
            'status': student.status,
            'full_name': f"{student.first_name} {student.last_name}",
            'created_at': student.created_at.strftime('%Y-%m-%d'),
            'profile_pic': student.profile_pic or None
        };
        
        return JsonResponse({
            'status': 'success',
            'student': student_data
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST", "PATCH"])
def update_student(request, student_id):
    """Update an existing student (supports file upload via POST)"""
    try:
        student = get_object_or_404(Student, id=student_id)
        
        # Check if the request is a PATCH request
        if request.method == 'PATCH':
            # Check content type to determine how to process data
            if 'multipart/form-data' in request.content_type:
                # Handle form data the same way as POST request
                # For PATCH with form data, use request.POST and request.FILES
                lrn = request.POST.get('lrn', student.lrn)
                first_name = request.POST.get('first_name', student.first_name)
                middle_name = request.POST.get('middle_name', '')
                last_name = request.POST.get('last_name', student.last_name)
                grade_id = request.POST.get('grade_id', student.grade.id if student.grade else None)
                section_id = request.POST.get('section_id', student.section.id if student.section else None)
                status = request.POST.get('status', student.status)
                
                # Validate required fields
                if not lrn or not first_name or not last_name or not grade_id or not section_id:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Missing required fields'
                    }, status=400)
                
                # Check if LRN already exists for another student
                if Student.objects.filter(lrn=lrn).exclude(id=student_id).exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Student with LRN {lrn} already exists'
                    }, status=400)
                
                # Get grade and section objects
                try:
                    grade = Grade.objects.get(id=grade_id)
                    section = Section.objects.get(id=section_id)
                except (Grade.DoesNotExist, Section.DoesNotExist):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid grade or section'
                    }, status=400)
                
                # Update student fields
                student.lrn = lrn
                student.first_name = first_name
                student.middle_name = middle_name
                student.last_name = last_name
                student.grade = grade
                student.section = section
                student.status = status
                
                # Handle profile picture if provided
                if 'profile_pic' in request.FILES:
                    profile_pic = request.FILES['profile_pic']
                    
                    # Validate file size and type
                    if profile_pic.size > 2 * 1024 * 1024:  # 2MB limit
                        return JsonResponse({'status': 'error', 'message': 'File size must be less than 2MB'}, status=400)
                    
                    if not profile_pic.content_type.startswith('image/'):
                        return JsonResponse({'status': 'error', 'message': 'Only image files are allowed'}, status=400)
                    
                    # Delete old profile picture if exists
                    if student.profile_pic:
                        old_profile_pic_path = os.path.join(PROFILE_PICS_DIR, student.profile_pic)
                        if os.path.exists(old_profile_pic_path):
                            os.remove(old_profile_pic_path)
                    
                    # Save the new profile picture
                    filename = f"student_{int(timezone.now().timestamp())}_{profile_pic.name}"
                    fs = FileSystemStorage(location=PROFILE_PICS_DIR)
                    filename = fs.save(filename, profile_pic)
                    student.profile_pic = filename
                
                student.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Student {first_name} {last_name} updated successfully',
                    'student_id': student.id
                })
                
            elif request.content_type == 'application/json':
                # Handle JSON data
                data = json.loads(request.body)
                
                # Update student fields from JSON data
                if 'lrn' in data:
                    student.lrn = data.get('lrn')
                if 'first_name' in data:
                    student.first_name = data.get('first_name')
                if 'middle_name' in data:
                    student.middle_name = data.get('middle_name', '')
                if 'last_name' in data:
                    student.last_name = data.get('last_name')
                if 'grade_id' in data and data['grade_id']:
                    student.grade = get_object_or_404(Grade, id=data['grade_id'])
                if 'section_id' in data and data['section_id']:
                    student.section = get_object_or_404(Section, id=data['section_id'])
                if 'status' in data:
                    student.status = data.get('status')
                
                student.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Student {student.first_name} {student.last_name} updated successfully',
                    'student_id': student.id
                })
            else:
                # Unsupported content-type
                return JsonResponse({
                    'status': 'error',
                    'message': 'Unsupported content type. Use multipart/form-data for file uploads or application/json for JSON data.'
                }, status=400)
        
        # Handle POST requests (usually form data with files)
        # Get values from POST data
        lrn = request.POST.get('lrn', student.lrn)
        first_name = request.POST.get('first_name', student.first_name)
        middle_name = request.POST.get('middle_name', '')
        last_name = request.POST.get('last_name', student.last_name)
        grade_id = request.POST.get('grade_id', student.grade.id if student.grade else None)
        section_id = request.POST.get('section_id', student.section.id if student.section else None)
        status = request.POST.get('status', student.status)
        
        # Validate required fields
        if not lrn or not first_name or not last_name or not grade_id or not section_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required fields'
            }, status=400)
        
        # Check if LRN already exists for another student
        if Student.objects.filter(lrn=lrn).exclude(id=student_id).exists():
            return JsonResponse({
                'status': 'error',
                'message': f'Student with LRN {lrn} already exists'
            }, status=400)
        
        # Get grade and section objects
        try:
            grade = Grade.objects.get(id=grade_id)
            section = Section.objects.get(id=section_id)
        except (Grade.DoesNotExist, Section.DoesNotExist):
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid grade or section'
            }, status=400)
        
        # Update student fields
        student.lrn = lrn
        student.first_name = first_name
        student.middle_name = middle_name
        student.last_name = last_name
        student.grade = grade
        student.section = section
        student.status = status
        
        # Handle profile picture if provided
        if 'profile_pic' in request.FILES:
            profile_pic = request.FILES['profile_pic']
            
            # Validate file size and type
            if profile_pic.size > 2 * 1024 * 1024:  # 2MB limit
                return JsonResponse({'status': 'error', 'message': 'File size must be less than 2MB'}, status=400)
            
            if not profile_pic.content_type.startswith('image/'):
                return JsonResponse({'status': 'error', 'message': 'Only image files are allowed'}, status=400)
            
            # Delete old profile picture if exists
            if student.profile_pic:
                old_profile_pic_path = os.path.join(PROFILE_PICS_DIR, student.profile_pic)
                if os.path.exists(old_profile_pic_path):
                    os.remove(old_profile_pic_path)
        
            # Save the new profile picture
            filename = f"student_{int(timezone.now().timestamp())}_{profile_pic.name}"
            fs = FileSystemStorage(location=PROFILE_PICS_DIR)
            filename = fs.save(filename, profile_pic)
            student.profile_pic = filename
        
        student.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Student {first_name} {last_name} updated successfully',
            'student_id': student.id
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def delete_student(request, student_id):
    """Delete a student"""
    try:
        student = get_object_or_404(Student, id=student_id)
        
        # Store student name for success message
        student_name = f"{student.first_name} {student.last_name}"
        
        # Delete the profile picture file if it exists
        if student.profile_pic:
            profile_pic_path = os.path.join(PROFILE_PICS_DIR, student.profile_pic)
            if os.path.exists(profile_pic_path):
                os.remove(profile_pic_path)
        
        # Delete the student
        student.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Student {student_name} deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def reset_student_password(request, student_id):
    """Reset a student's password (if applicable)"""
    # If students have user accounts, implement password reset logic here.
    return JsonResponse({'status': 'error', 'message': 'Not implemented.'}, status=400)

@login_required
@user_passes_test(is_admin)
def get_student(request, student_id):
    """
    Endpoint to retrieve a specific student's data for editing
    """
    try:
        student = get_object_or_404(Student, id=student_id)
        
        # Build the student data for response
        student_data = {
            'id': student.id,
            'lrn': student.lrn,
            'first_name': student.first_name,
            'middle_name': student.middle_name or '',
            'last_name': student.last_name,
            'grade_id': str(student.grade.id) if student.grade else '',
            'grade': student.grade.name if student.grade else '',
            'section_id': str(student.section.id) if student.section else '',
            'section': student.section.name if student.section else '',
            'status': student.status,
            'full_name': f"{student.first_name} {student.last_name}",
            'created_at': student.created_at.strftime('%Y-%m-%d'),
            'profile_pic': student.profile_pic or None
        }
        
        return JsonResponse({
            'status': 'success',
            'student': student_data
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# ==========================
#  GUARDIAN MANAGEMENT VIEWS
# ==========================

@login_required
@user_passes_test(is_admin)
def admin_guardians(request):
    """Guardian management view with dashboard cards"""
    # Calculate dashboard statistics
    total_guardians = Guardian.objects.count()
    
    # Count guardians with children (since each guardian has exactly one student)
    guardians_with_children = Guardian.objects.exclude(student=None).count()
    
    # Count mother guardians
    mother_count = Guardian.objects.filter(relationship='MOTHER').count()
    
    # Count father guardians
    father_count = Guardian.objects.filter(relationship='FATHER').count()
    
    # Get relationship choices for filter dropdown
    relationship_choices = [
        ('FATHER', 'Father'),
        ('MOTHER', 'Mother'),
        ('GUARDIAN', 'Guardian'),
        ('GRANDMOTHER', 'Grandmother'),
        ('GRANDFATHER', 'Grandfather'),
        ('AUNT', 'Aunt'),
        ('UNCLE', 'Uncle'),
        ('SIBLING', 'Sibling'),
        ('OTHER', 'Other'),
    ]
    
    # Get all grades for filter dropdown
    grades = Grade.objects.all().order_by('name')
    
    # Get all sections for filter dropdown
    sections = Section.objects.select_related('grade').order_by('grade__name', 'name')
    
    # Get students for children dropdown
    students = Student.objects.select_related('grade', 'section').filter(status='ACTIVE')
    
    context = {
        'total_guardians': total_guardians,
        'guardians_with_children': guardians_with_children,
        'mother_count': mother_count,
        'father_count': father_count,
        'relationship_choices': relationship_choices,
        'grades': grades,
        'sections': sections,
        'students': students,
    }
    
    return render(request, 'admin/guardians.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def search_guardians(request):
    """API endpoint to search and filter guardians for AJAX requests"""
    try:
        # Get query parameters
        search_query = request.GET.get('search', '')
        relationship_filter = request.GET.get('relationship', '')
        grade_filter = request.GET.get('grade', '')
        section_filter = request.GET.get('section', '')
        page_number = request.GET.get('page', 1)
        items_per_page = request.GET.get('items_per_page', 10)
        
        # Base queryset
        guardians = Guardian.objects.all().order_by('-created_at')
        
        # Apply search if provided
        if search_query:
            guardians = guardians.filter(
                Q(first_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query)  # Use phone instead of phone_number
            )
        
        # Apply relationship filter if provided
        if relationship_filter:
            guardians = guardians.filter(relationship=relationship_filter)
        
        # Apply grade filter if provided
        if grade_filter:
            # Find students in this grade, then filter guardians related to them
            student_ids = Student.objects.filter(grade_id=grade_filter).values_list('id', flat=True)
            guardians = guardians.filter(student_id__in=student_ids)
        
        # Apply section filter if provided
        if section_filter:
            # Find students in this section, then filter guardians related to them
            student_ids = Student.objects.filter(section_id=section_filter).values_list('id', flat=True)
            guardians = guardians.filter(student_id__in=student_ids)
        
        # Get total count for pagination
        total_count = guardians.count()
        
        # Parse page number and items_per_page
        try:
            page_number = int(page_number)
            items_per_page = int(items_per_page)
        except (ValueError, TypeError):
            page_number = 1
            items_per_page = 10
        
        # Create paginator
        paginator = Paginator(guardians, items_per_page)
        page_obj = paginator.get_page(page_number)
        
        # Prepare guardian data for JSON response
        guardian_data = []
        for guardian in page_obj:
            try:
                # Create guardian data dict with safe fallbacks
                data = {
                    'id': guardian.id,
                    'full_name': f"{guardian.first_name} {guardian.last_name}",
                    'first_name': guardian.first_name,
                    'middle_name': guardian.middle_name or '',
                    'last_name': guardian.last_name,
                    'email': guardian.email or 'No email',
                    'phone_number': guardian.phone or 'No phone',  # Use phone instead of phone_number
                    'relationship': guardian.relationship,
                    'created_at_display': guardian.created_at.strftime('%B %d, %Y') if guardian.created_at else 'N/A'
                }
                
                # Safely handle relationship display and children data
                try:
                    data['relationship_display'] = guardian.get_relationship_display()
                except (AttributeError, TypeError):
                    data['relationship_display'] = guardian.relationship
                
                # Child info with safe fallbacks
                try:
                    student = Student.objects.filter(id=guardian.student_id).first() if hasattr(guardian, 'student_id') else None
                    if student:
                        data['children_count'] = 1
                        data['children_preview'] = f"{student.first_name} {student.last_name}"
                    else:
                        data['children_count'] = 0
                        data['children_preview'] = 'No children'
                except Exception as e:
                    data['children_count'] = 0
                    data['children_preview'] = 'Error loading children'



                    print(f"Error loading children for guardian {guardian.id}: {str(e)}")
                
                guardian_data.append(data)
            except Exception as e:
                print(f"Error processing guardian {guardian.id if hasattr(guardian, 'id') else 'unknown'}: {str(e)}")
                continue
        
        # Prepare pagination data
        pagination = {
            'current_page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page_range': list(get_pagination_range(paginator, page_obj.number, 5)),
            'start_index': page_obj.start_index(),
            'end_index': page_obj.end_index(),
            'total_count': total_count,
        }
        
        return JsonResponse({
            'status': 'success',
            'guardians': guardian_data,
            'pagination': pagination,
            'total_count': total_count,
        })
    
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error in search_guardians: {str(e)}")
        print(error_traceback)
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred: {str(e)}',
            'traceback': error_traceback
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_guardian(request):
    """Create a new guardian"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'phone_number', 'relationship', 'student_id']
        for field in required_fields:
            if not field in data or not data[field]:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Field {field} is required'
                }, status=400)
        
        # Check if student exists and doesn't already have a guardian
       

        try:
            student = Student.objects.get(id=data['student_id'])
        except Student.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Student not found'
            }, status=404)
        
        # Validate email if provided
        email = data.get('email', '').strip()
        if email:
            # Add email validation if needed
            pass
        
        # Create guardian - Note: using phone_number from form but storing in phone field
        guardian = Guardian.objects.create(
            first_name=data['first_name'].strip(),
            middle_name=data.get('middle_name', '').strip(),
            last_name=data['last_name'].strip(),
            email=email,
            phone=data['phone_number'].strip(),  # Changed to map phone_number to phone
            relationship=data['relationship'],
            student=student
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Guardian created successfully',
            'guardian': {
                'id': guardian.id,
                'full_name': f"{guardian.first_name} {guardian.last_name}",
                'email': guardian.email or '',
                'phone_number': guardian.phone,  # Return as phone_number for consistency with form
                'relationship': guardian.relationship,
                'student_name': f"{student.first_name} {student.last_name}",
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["PATCH"])
def update_guardian(request, guardian_id):
    """Update an existing guardian"""
    try:
        data = json.loads(request.body)
        
        guardian = get_object_or_404(Guardian, id=guardian_id)
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'phone_number', 'relationship', 'student_id']
        for field in required_fields:
            if not field in data or not data[field]:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Field {field} is required'
                }, status=400)
        
        # Check if student exists and validate assignment
        try:
            student = Student.objects.get(id=data['student_id'])
        except Student.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Student not found'
            }, status=404)
        
        # Validate email if provided
        email = data.get('email', '').strip()
        # Email validation could go here if needed
        
        # Update guardian fields
        guardian.first_name = data['first_name'].strip()
        guardian.middle_name = data.get('middle_name', '').strip()
        guardian.last_name = data['last_name'].strip()
        guardian.email = email
        guardian.phone = data['phone_number'].strip()  # Map phone_number from form to phone field in model
        guardian.relationship = data['relationship']
        guardian.student = student
        guardian.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Guardian updated successfully',
            'guardian': {
                'id': guardian.id,
                'full_name': f"{guardian.first_name} {guardian.last_name}",
                'email': guardian.email or '',
                'phone_number': guardian.phone,  # Return as phone_number for consistency with form
                'relationship': guardian.relationship,
                'student_name': f"{student.first_name} {student.last_name}"
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"Error in update_guardian: {str(e)}")
        print(error_traceback)
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred: {str(e)}',
            'traceback': error_traceback
        }, status=500)  # Changed to 500 for server errors

@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def delete_guardian(request, guardian_id):
    """Delete a guardian"""
    try:
        guardian = get_object_or_404(Guardian, id=guardian_id)
        guardian_name = f"{guardian.first_name} {guardian.last_name}"  # Use direct concatenation instead of get_full_name
        guardian.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Guardian {guardian_name} deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_GET
def get_guardian_children(request, guardian_id):
    """Get children for a specific guardian"""
    try:
        guardian = get_object_or_404(Guardian, id=guardian_id)
        
        children = []
        if guardian.student:
            children.append({
                'id': guardian.student.id,
                'full_name': f"{guardian.student.first_name} {guardian.student.last_name}",  # Direct concatenation
                'lrn': guardian.student.lrn,
                'grade': guardian.student.grade.name if guardian.student.grade else 'N/A',
                'section': guardian.student.section.name if guardian.student.section else 'N/A',
                'status': guardian.student.status
            })
        
        return JsonResponse({
            'status': 'success',
            'guardian': {
                'name': f"{guardian.first_name} {guardian.last_name}",  # Direct concatenation
                'relationship': guardian.get_relationship_display() if hasattr(guardian, 'get_relationship_display') else guardian.relationship
            },
            'children': children
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_GET
def admin_get_sections_by_grade(request):
    """Get sections for a specific grade"""
    try:
        grade_id = request.GET.get('grade_id')
        if not grade_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Grade ID is required'
            }, status=400)
        
        sections = Section.objects.filter(grade_id=grade_id).order_by('name')
        sections_data = [
            {
                'id': section.id,
                'name': section.name,
                'grade_id': section.grade.id,
                'grade_name': section.grade.name
            }
            for section in sections
        ]
        
        return JsonResponse({
            'status': 'success',
            'sections': sections_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_GET
def admin_get_students_by_section(request):
    """Get students for a specific section"""
    try:
        section_id = request.GET.get('section_id')
        if not section_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Section ID is required'
            }, status=400)
        

        
        # Get students who don't already have a guardian assigned (for create) or are assigned to the current guardian (for edit)
        students = Student.objects.filter(
            section_id=section_id,
            status='ACTIVE'
        ).select_related('grade', 'section').order_by('first_name', 'last_name')
        
        students_data = [
            {
                'id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'lrn': student.lrn,
                'grade': student.grade.name if student.grade else 'N/A',
                'section': student.section.name if student.section else 'N/A',
                'grade_id': student.grade.id if student.grade else None,
                'section_id': student.section.id if student.section else None,
                'has_guardian': hasattr(student, 'guardian') and student.guardian is not None
            }
            for student in students
        ]
        
        return JsonResponse({
            'status': 'success',
            'students': students_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_GET
def get_guardian_details(request, guardian_id):
    """
    Endpoint to retrieve a specific guardian's data for editing
    """
    try:
        guardian = get_object_or_404(Guardian, id=guardian_id)
        
        # Prepare children data
        children = []
        if guardian.student:
            child = guardian.student
            children.append({
                'id': child.id,
                'grade_id': child.grade.id if child.grade else '',
                'grade': child.grade.name if child.grade else '',
                'section_id': child.section.id if child.section else '',
                'section': child.section.name if child.section else '',
                'first_name': child.first_name,
                'last_name': child.last_name,
                'full_name': f"{child.first_name} {child.last_name}"  # Direct concatenation
            })
        
        guardian_data = {
            'id': guardian.id,
            'first_name': guardian.first_name,
            'middle_name': guardian.middle_name or '',
            'last_name': guardian.last_name,
            'email': guardian.email or '',
            'phone_number': guardian.phone,  # Return phone field as phone_number for form
            'relationship': guardian.relationship,
            'children': children,
            'created_at': guardian.created_at.isoformat() if guardian.created_at else None
        }
        
        return JsonResponse({
            'status': 'success',
            'guardian': guardian_data
        })
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error in get_guardian_details: {str(e)}")
        print(error_traceback)
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred: {str(e)}',
            'traceback': error_traceback
        }, status=500)


# ==========================
#  ATTENDANCE MANAGEMENT VIEWS
# ==========================

@login_required
@user_passes_test(is_admin)
def admin_attendance_records(request):
    """Attendance management view with dashboard cards and filters"""
    from django.db.models import Q
    from datetime import date

    # Dashboard stats
    total_records = Attendance.objects.count()
    present_count = Attendance.objects.filter(status='ON TIME').count() + Attendance.objects.filter(status='LATE').count()
    absent_count = Attendance.objects.filter(status='ABSENT').count()
    excused_count = Attendance.objects.filter(status='EXCUSED').count()

    grades = Grade.objects.all().order_by('name')
    sections = Section.objects.select_related('grade').order_by('grade__name', 'name')

    # Filters (for initial page load)
    grade_filter = request.GET.get('grade', '')
    section_filter = request.GET.get('section', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    context = {
        'grades': grades,
        'sections': sections,
        'grade_filter': grade_filter,
        'section_filter': section_filter,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'excused_count': excused_count,
    }
    return render(request, 'admin/attendance.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET"])
def search_attendance_records(request):
    """AJAX search/filter for attendance records"""
    search_query = request.GET.get('search', '')
    grade_filter = request.GET.get('grade', '')
    section_filter = request.GET.get('section', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    page_number = request.GET.get('page', 1)
    items_per_page = request.GET.get('items_per_page', 10)

    records = Attendance.objects.select_related('student', 'student__grade', 'student__section').all().order_by('-date', '-student__last_name')

    if search_query:
        records = records.filter(
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(student__lrn__icontains=search_query) |
            Q(student__section__name__icontains=search_query)
        )
    if grade_filter:
        records = records.filter(student__grade_id=grade_filter)
    if section_filter:
        records = records.filter(student__section_id=section_filter)
    if status_filter:
        records = records.filter(status=status_filter)
    if date_filter:
        records = records.filter(date=date_filter)

    total_count = records.count()
    try:
        page_number = int(page_number)
        items_per_page = int(items_per_page)
    except (ValueError, TypeError):
        page_number = 1
        items_per_page = 10

    paginator = Paginator(records, items_per_page)
    page_obj = paginator.get_page(page_number)

    attendance_data = []
    for record in page_obj:
        attendance_data.append({
            'id': record.id,
            'lrn': record.student.lrn,
            'full_name': f"{record.student.first_name} {record.student.last_name}",
            'grade': record.student.grade.name if record.student.grade else '',
            'section': record.student.section.name if record.student.section else '',
            'date': record.date.strftime('%Y-%m-%d'),
            'time_in': record.time_in.strftime('%H:%M:%S') if record.time_in else '',
            'time_out': record.time_out.strftime('%H:%M:%S') if record.time_out else '',
            'status': record.status,
            'profile_pic': record.student.profile_pic or None,
        })

    pagination = {
        'current_page': page_obj.number,
        'num_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'page_range': list(get_pagination_range(paginator, page_obj.number, 5)),
        'start_index': page_obj.start_index(),
        'end_index': page_obj.end_index(),
        'total_count': total_count,
    }

    return JsonResponse({
        'status': 'success',
        'records': attendance_data,
        'pagination': pagination,
        'total_count': total_count,
    })

@login_required
@user_passes_test(is_admin)
@require_GET
def get_attendance_record(request, attendance_id):
    """API endpoint to get details of a specific attendance record"""
    try:
        record = get_object_or_404(Attendance, id=attendance_id)
        
        data = {
            'id': record.id,
            'student_id': record.student.id,
            'student_name': f"{record.student.first_name} {record.student.last_name}",
            'lrn': record.student.lrn,
            'date': record.date.strftime('%Y-%m-%d'),
            'time_in': record.time_in.strftime('%H:%M:%S') if record.time_in else None,
            'time_out': record.time_out.strftime('%H:%M:%S') if record.time_out else None,
            'status': record.status,
            'notes': record.notes or '',
            'section': record.student.section.name if record.student.section else '',
            'section_id': record.student.section.id if record.student.section else None,
            'grade': record.student.grade.name if record.student.grade else '',
            'grade_id': record.student.grade.id if record.student.grade else None,
        }
        
        return JsonResponse({
            'status': 'success',
            'record': data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_attendance_record(request):
    """API endpoint to create a new attendance record"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['student_id', 'date', 'status']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({
                    'status': 'error',
                    'message': f'{field} is required'
                }, status=400)
        
        # Check if student exists
        try:
            student = Student.objects.get(id=data['student_id'])
        except Student.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Student not found'
            }, status=404)
        
        # Check if an attendance record already exists for this student on this date
        if Attendance.objects.filter(student=student, date=data['date']).exists():
            return JsonResponse({
                'status': 'error',
                'message': f'Attendance record already exists for {student.first_name} {student.last_name} on {data["date"]}'
            }, status=400)
        
        # Parse time fields if provided
        time_in = None
        if data.get('time_in'):
            try:
                from datetime import datetime
                time_in = datetime.strptime(data['time_in'], '%H:%M:%S').time()
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid time_in format. Use HH:MM:SS'
                }, status=400)
                
        time_out = None
        if data.get('time_out'):
            try:
                from datetime import datetime
                time_out = datetime.strptime(data['time_out'], '%H:%M:%S').time()
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid time_out format. Use HH:MM:SS'
                }, status=400)
        
        # Create attendance record
        record = Attendance(
            student=student,
            date=data['date'],
            time_in=time_in,
            time_out=time_out,
            status=data['status']
        )
        record.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Attendance record for {student.first_name} {student.last_name} created successfully',
            'record_id': record.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        import traceback
        print("Error in create_attendance_record:", str(e))
        print(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT", "PATCH"])
def update_attendance_record(request, attendance_id):
    """API endpoint to update an attendance record"""
    try:
        record = get_object_or_404(Attendance, id=attendance_id)
        data = json.loads(request.body)
        
        # Update status if provided
        if 'status' in data:
            record.status = data['status']
        
        # Update date if provided
        if 'date' in data:
            # Check if another record exists for this student on the new date (excluding current record)
            if Attendance.objects.filter(student=record.student, date=data['date']).exclude(id=attendance_id).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': f'Another attendance record exists for {record.student.first_name} {record.student.last_name} on {data["date"]}'
                }, status=400)
            record.date = data['date']
        
        # Update time_in if provided
        if 'time_in' in data:
            if data['time_in']:
                try:
                    from datetime import datetime
                    record.time_in = datetime.strptime(data['time_in'], '%H:%M:%S').time()
                except ValueError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid time_in format. Use HH:MM:SS'
                    }, status=400)
            else:
                record.time_in = None
        
        # Update time_out if provided
        if 'time_out' in data:
            if data['time_out']:
                try:
                    from datetime import datetime
                    record.time_out = datetime.strptime(data['time_out'], '%H:%M:%S').time()
                except ValueError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid time_out format. Use HH:MM:SS'
                    }, status=400)
            else:
                record.time_out = None
        
        # Update notes if provided
        if 'notes' in data:
            record.notes = data.get('notes', '')
        
        # Save the updated record
        record.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Attendance record updated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def delete_attendance_record(request, attendance_id):
    """API endpoint to delete an attendance record"""
    try:
        record = get_object_or_404(Attendance, id=attendance_id)
        student_name = f"{record.student.first_name} {record.student.last_name}"
        record_date = record.date.strftime('%Y-%m-%d')
        
        record.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Attendance record for {student_name} on {record_date} deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_GET
def get_students_for_attendance(request):
    """API endpoint to get students for attendance form"""
    try:
        # Get filters
        section_id = request.GET.get('section', None)
        grade_id = request.GET.get('grade', None)
        
        # Base queryset - only active students
        students = Student.objects.filter(status='ACTIVE').select_related('grade', 'section')
        
        # Apply filters if provided
        if section_id:
            students = students.filter(section_id=section_id)
        elif grade_id:
            students = students.filter(grade_id=grade_id)
        
        # Order by name
        students = students.order_by('last_name', 'first_name')
        
        # Prepare data for response
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'lrn': student.lrn,
                'name': f"{student.first_name} {student.last_name}",
                'grade': student.grade.name if student.grade else '',
                'section': student.section.name if student.section else '',
                'grade_id': student.grade.id if student.grade else None,
                'section_id': student.section.id if student.section else None
            })
        
        return JsonResponse({
            'status': 'success',
            'students': students_data,
            'total': len(students_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    


# ==========================
#  OTHER MANAGEMENT VIEWS
# ==========================

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
        import uuid
        import traceback
        
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
        # Validate the path to prevent directory traversal
        if '..' in path or path.startswith('/'):
            return HttpResponseNotFound("Not found")
        
        full_path = os.path.join(PROFILE_PICS_DIR, path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            with open(full_path, 'rb') as f:
                return HttpResponse(f.read(), content_type='image/jpeg')  # Adjust content type if needed
        else:
            return HttpResponseNotFound("Image not found")
    except Exception as e:
        return HttpResponseNotFound(f"Error: {str(e)}")

@login_required
def serve_profile_pic_default(request):
    """Serve a default profile picture when none is specified"""
    # You can either redirect to a static default image or serve a placeholder
    default_image_path = os.path.join(settings.STATIC_ROOT, 'images', 'default_profile.png')
    
    if os.path.exists(default_image_path):
        with open(default_image_path, 'rb') as f:
            return HttpResponse(f.read(), content_type='image/png')
    else:
        # If default image doesn't exist, return a 404 or an empty response
        return HttpResponse(status=204)  # 204 No Content
