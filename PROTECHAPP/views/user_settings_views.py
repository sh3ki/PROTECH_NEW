"""
User Settings Views
Handles profile management, password changes, and account deletion for all user types.
"""

import os
import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db import transaction
from PIL import Image
from PROTECHAPP.models import CustomUser

logger = logging.getLogger(__name__)

# Create private_profile_pics directory if it doesn't exist (same as admin_views.py)
PROFILE_PICS_DIR = os.path.join(settings.BASE_DIR, 'private_profile_pics')
os.makedirs(PROFILE_PICS_DIR, exist_ok=True)


@login_required
@require_http_methods(["POST"])
def update_profile_picture(request):
    """
    Upload and update user profile picture.
    Validates file size (max 5MB) and image format.
    """
    try:
        if 'profile_picture' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file uploaded'
            }, status=400)
        
        profile_picture = request.FILES['profile_picture']
        
        # Validate file size (5MB max)
        if profile_picture.size > 5 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'message': 'File size must be less than 5MB'
            }, status=400)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if profile_picture.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'message': 'Invalid file type. Only JPEG, PNG, GIF, and WebP images are allowed'
            }, status=400)
        
        # Generate unique filename
        import uuid
        file_extension = os.path.splitext(profile_picture.name)[1]
        filename = f"{uuid.uuid4()}_{profile_picture.name}"
        
        # Delete old profile picture if exists
        if request.user.profile_pic:
            old_pic_path = os.path.join(PROFILE_PICS_DIR, request.user.profile_pic)
            if os.path.exists(old_pic_path):
                try:
                    os.remove(old_pic_path)
                except Exception as e:
                    logger.warning(f"Could not delete old profile picture: {e}")
        
        # Save the file to private_profile_pics directory
        fs = FileSystemStorage(location=PROFILE_PICS_DIR)
        saved_filename = fs.save(filename, profile_picture)
        
        # Optimize image (resize if too large)
        file_path = os.path.join(PROFILE_PICS_DIR, saved_filename)
        try:
            with Image.open(file_path) as img:
                # Convert RGBA to RGB if needed
                if img.mode == 'RGBA':
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3])
                    img = rgb_img
                
                # Resize if image is too large (max 800x800)
                max_size = (800, 800)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    img.save(file_path, optimize=True, quality=85)
        except Exception as e:
            logger.error(f"Error optimizing image: {e}")
        
        # Update user profile - store just the filename (not the full path)
        request.user.profile_pic = saved_filename
        request.user.save()
        
        logger.info(f"Profile picture updated for user {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Profile picture updated successfully',
            'profile_pic_url': f'/profile-pics/{saved_filename}/'
        })
        
    except Exception as e:
        logger.error(f"Error updating profile picture: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while updating profile picture'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def remove_profile_picture(request):
    """
    Remove user profile picture and revert to default avatar.
    """
    try:
        # Delete the profile picture file if it exists
        if request.user.profile_pic:
            pic_path = os.path.join(PROFILE_PICS_DIR, request.user.profile_pic)
            if os.path.exists(pic_path):
                try:
                    os.remove(pic_path)
                    logger.info(f"Deleted profile picture file: {pic_path}")
                except Exception as e:
                    logger.warning(f"Could not delete profile picture file: {e}")
        
        # Update user profile
        request.user.profile_pic = None
        request.user.save()
        
        logger.info(f"Profile picture removed for user {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Profile picture removed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error removing profile picture: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while removing profile picture'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def update_profile(request):
    """
    Update user profile information (name, username, email).
    Validates uniqueness of username and email.
    """
    try:
        data = json.loads(request.body)
        
        first_name = data.get('first_name', '').strip()
        middle_name = data.get('middle_name', '').strip()
        last_name = data.get('last_name', '').strip()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        
        # Validation
        if not all([first_name, last_name, username, email]):
            return JsonResponse({
                'success': False,
                'message': 'Please fill in all required fields (First Name, Last Name, Username, Email)'
            }, status=400)
        
        # Validate email format
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return JsonResponse({
                'success': False,
                'message': 'Please enter a valid email address'
            }, status=400)
        
        # Check if username is taken by another user
        if username != request.user.username:
            if CustomUser.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Username is already taken'
                }, status=400)
        
        # Check if email is taken by another user
        if email.lower() != request.user.email.lower():
            if CustomUser.objects.filter(email__iexact=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Email address is already registered'
                }, status=400)
        
        # Update user profile
        request.user.first_name = first_name
        request.user.middle_name = middle_name
        request.user.last_name = last_name
        request.user.username = username
        request.user.email = email
        request.user.save()
        
        logger.info(f"Profile updated for user {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while updating profile'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def change_password(request):
    """
    Change user password with current password verification.
    """
    try:
        data = json.loads(request.body)
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validation
        if not all([current_password, new_password, confirm_password]):
            return JsonResponse({
                'success': False,
                'message': 'Please fill in all password fields'
            }, status=400)
        
        # Verify current password
        if not authenticate(username=request.user.username, password=current_password):
            return JsonResponse({
                'success': False,
                'message': 'Current password is incorrect'
            }, status=400)
        
        # Validate new password length
        if len(new_password) < 8:
            return JsonResponse({
                'success': False,
                'message': 'New password must be at least 8 characters long'
            }, status=400)
        
        # Check if passwords match
        if new_password != confirm_password:
            return JsonResponse({
                'success': False,
                'message': 'New passwords do not match'
            }, status=400)
        
        # Check if new password is same as current
        if current_password == new_password:
            return JsonResponse({
                'success': False,
                'message': 'New password must be different from current password'
            }, status=400)
        
        # Update password
        request.user.set_password(new_password)
        request.user.is_new = False  # Mark user as no longer new after password change
        request.user.save()
        
        # Keep user logged in after password change
        update_session_auth_hash(request, request.user)
        
        logger.info(f"Password changed for user {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Password updated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while changing password'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def delete_account(request):
    """
    Permanently delete user account.
    This is irreversible and will remove all user data.
    """
    try:
        user = request.user
        user_id = user.id
        username = user.username
        
        # Delete profile picture if exists
        if user.profile_pic:
            pic_path = os.path.join(PROFILE_PICS_DIR, user.profile_pic)
            if os.path.exists(pic_path):
                try:
                    os.remove(pic_path)
                    logger.info(f"Deleted profile picture for user {username}")
                except Exception as e:
                    logger.warning(f"Could not delete profile picture: {e}")
        
        # Use transaction to ensure atomic deletion
        with transaction.atomic():
            # Log the deletion
            logger.warning(f"Account deleted: User ID {user_id}, Username: {username}")
            
            # Delete the user account
            # Note: Related records (attendance, messages, etc.) will be handled by CASCADE/SET_NULL
            user.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Account deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while deleting account'
        }, status=500)
