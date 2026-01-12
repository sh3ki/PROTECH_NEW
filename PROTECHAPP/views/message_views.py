"""
Complete Message Views - All API endpoints for messaging system
Supports private and group conversations with read/unread tracking
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from PROTECHAPP.message_service import MessageService
from PROTECHAPP.models import CustomUser
import json

__all__ = [
    'create_conversation',
    'get_conversations',
    'get_conversation',
    'add_participants',
    'send_message',
    'get_messages',
    'mark_as_read',
    'delete_message',
    'get_unread_count',
    'search_users',
    'poll_new_messages',
    'poll_conversations',
]

# ============================================================================
# CONVERSATION ENDPOINTS
# ============================================================================

@login_required
@require_http_methods(["POST"])
def create_conversation(request):
    """
    Create a new conversation (private or group)
    """
    try:
        data = json.loads(request.body)
        participant_ids_raw = data.get('participant_ids', [])
        title = data.get('title', '') or data.get('name', '')
        
        # Convert all participant IDs to integers
        participant_ids = [int(pid) for pid in participant_ids_raw]
        
        # Handle both 'type' and 'is_group' parameters
        conv_type = data.get('type', '')
        is_group = data.get('is_group', conv_type == 'group')
        
        print(f"DEBUG: Creating conversation - participant_ids: {participant_ids}, is_group: {is_group}, title: {title}")
        
        if not participant_ids:
            return JsonResponse({'error': 'No participants provided'}, status=400)
        
        # Add creator to participants if not already included
        if request.user.id not in participant_ids:
            participant_ids.insert(0, request.user.id)
        
        print(f"DEBUG: After adding creator - participant_ids: {participant_ids}")
        
        # Get participant names from database
        participants = CustomUser.objects.filter(id__in=participant_ids)
        participant_names = [f"{p.first_name} {p.last_name}" for p in participants]
        
        print(f"DEBUG: Participant names: {participant_names}")
        
        # Create conversation
        conversation = MessageService.create_conversation(
            creator_id=request.user.id,
            creator_name=f"{request.user.first_name} {request.user.last_name}",
            title=title,
            participant_ids=participant_ids,
            participant_names=participant_names,
            is_group=is_group
        )
        
        print(f"DEBUG: Conversation created: {conversation}")
        
        if conversation:
            # Convert datetime to string
            if 'created_at' in conversation:
                conversation['created_at'] = conversation['created_at'].isoformat()
            if 'last_message_time' in conversation:
                conversation['last_message_time'] = conversation['last_message_time'].isoformat()
                
            return JsonResponse({
                'success': True,
                'conversation_id': conversation.get('id'),
                'conversation': conversation
            })
        else:
            print("DEBUG: Conversation creation returned None")
            return JsonResponse({'error': 'Failed to create conversation'}, status=500)
    
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception in create_conversation: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_conversations(request):
    """
    Get all conversations for the current user
    """
    try:
        conversations = MessageService.get_user_conversations(request.user.id)
        
        # Transform and convert datetime objects to strings
        transformed_conversations = []
        for conv in conversations:
            # Transform Firebase structure to frontend structure
            transformed = {
                'id': conv.get('id'),  # Use 'id' not 'conversation_id'
                'conversation_id': conv.get('id'),  # Keep for backwards compatibility
                'type': 'group' if conv.get('is_group') else 'private',
                'title': conv.get('title', 'Unnamed Chat'),  # Use 'title' for frontend
                'name': conv.get('title', 'Unnamed Chat'),
                'unread_count': conv.get('unread_count', 0),
                'participant_count': len(conv.get('participant_ids', [])),
                'last_message': conv.get('last_message'),  # Direct message text
                'last_message_time': conv.get('last_message_time').isoformat() if conv.get('last_message_time') else None,
                'last_message_obj': {
                    'message': conv.get('last_message'),
                    'timestamp': conv.get('last_message_time').isoformat() if conv.get('last_message_time') else None,
                    'sender_name': conv.get('last_message_sender', ''),
                    'sender_id': conv.get('last_message_sender_id')
                } if conv.get('last_message') else None
            }
            
            # For private chats, add other_user_name and other_user_role
            if not conv.get('is_group'):
                participant_ids = conv.get('participant_ids', [])
                
                # Find the other user (not current user)
                for pid in participant_ids:
                    if str(pid) != str(request.user.id):
                        transformed['other_user_id'] = pid
                        # Get user details from database (ALWAYS use database, not Firestore cache)
                        try:
                            other_user = CustomUser.objects.get(id=int(pid))
                            # Get CURRENT name from database, not cached Firestore name
                            transformed['other_user_name'] = f"{other_user.first_name} {other_user.last_name}"
                            transformed['other_user_role'] = other_user.role
                            transformed['other_user_username'] = other_user.username
                            # Get profile picture path (not URL)
                            if other_user.profile_pic:
                                transformed['other_user_profile_pic'] = str(other_user.profile_pic)
                            else:
                                transformed['other_user_profile_pic'] = None
                        except CustomUser.DoesNotExist:
                            transformed['other_user_name'] = 'Unknown User'
                            transformed['other_user_role'] = ''
                            transformed['other_user_username'] = ''
                            transformed['other_user_profile_pic'] = None
                        break
            
            transformed_conversations.append(transformed)
        
        return JsonResponse({
            'success': True,
            'conversations': transformed_conversations
        })
    
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception in get_conversations: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_conversation(request, conversation_id):
    """
    Get a specific conversation by ID
    """
    try:
        conversation = MessageService.get_conversation(conversation_id, request.user.id)
        
        if not conversation:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        
        # Check if user is a participant
        if str(request.user.id) not in conversation.get('participant_ids', []):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Convert datetime objects
        if 'created_at' in conversation and conversation['created_at']:
            conversation['created_at'] = conversation['created_at'].isoformat()
        if 'last_message_time' in conversation and conversation['last_message_time']:
            conversation['last_message_time'] = conversation['last_message_time'].isoformat()
        
        # For private chats, add other_user info
        if not conversation.get('is_group'):
            participant_ids = conversation.get('participant_ids', [])
            
            # Find the other user (not current user)
            for pid in participant_ids:
                if str(pid) != str(request.user.id):
                    conversation['other_user_id'] = pid
                    # Get user details from database (ALWAYS use database, not Firestore cache)
                    try:
                        other_user = CustomUser.objects.get(id=int(pid))
                        # Get CURRENT name from database, not cached Firestore name
                        conversation['other_user_name'] = f"{other_user.first_name} {other_user.last_name}"
                        conversation['other_user_role'] = other_user.role
                        conversation['other_user_username'] = other_user.username
                        if other_user.profile_pic:
                            conversation['other_user_profile_pic'] = str(other_user.profile_pic)
                        else:
                            conversation['other_user_profile_pic'] = None
                    except CustomUser.DoesNotExist:
                        conversation['other_user_name'] = 'Unknown User'
                        conversation['other_user_role'] = ''
                        conversation['other_user_username'] = ''
                        conversation['other_user_profile_pic'] = None
                    break
        
        return JsonResponse({
            'success': True,
            'conversation': conversation
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def add_participants(request, conversation_id):
    """
    Add participants to a group conversation
    """
    try:
        data = json.loads(request.body)
        participant_ids = data.get('participant_ids', [])
        
        if not participant_ids:
            return JsonResponse({'error': 'No participants provided'}, status=400)
        
        # Get participant names
        participants = CustomUser.objects.filter(id__in=participant_ids)
        participant_names = [f"{p.first_name} {p.last_name}" for p in participants]
        
        success = MessageService.add_participants_to_group(
            conversation_id,
            participant_ids,
            participant_names
        )
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Failed to add participants'}, status=500)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# MESSAGE ENDPOINTS
# ============================================================================

@login_required
@require_http_methods(["POST"])
def send_message(request):
    """
    Send a message to a conversation
    """
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        message_text = data.get('message')
        message_type = data.get('message_type', 'text')
        
        if not conversation_id or not message_text:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Verify user is in conversation
        conversation = MessageService.get_conversation(conversation_id)
        if not conversation:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        
        if str(request.user.id) not in conversation.get('participant_ids', []):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Send message
        result = MessageService.send_message(
            conversation_id=conversation_id,
            sender_id=request.user.id,
            sender_name=f"{request.user.first_name} {request.user.last_name}",
            sender_role=request.user.role,
            message_text=message_text,
            message_type=message_type
        )
        
        if result:
            # Convert datetime
            if 'timestamp' in result:
                result['timestamp'] = result['timestamp'].isoformat()
                
            return JsonResponse({
                'success': True,
                'message': result
            })
        else:
            return JsonResponse({'error': 'Failed to send message'}, status=500)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_messages(request, conversation_id):
    """
    Get messages in a conversation
    """
    try:
        # Verify user is in conversation
        conversation = MessageService.get_conversation(conversation_id)
        if not conversation:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        
        if str(request.user.id) not in conversation.get('participant_ids', []):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Get messages
        limit = int(request.GET.get('limit', 100))
        messages = MessageService.get_conversation_messages(conversation_id, limit)
        
        # Convert datetime objects
        for msg in messages:
            if 'timestamp' in msg and msg['timestamp']:
                msg['timestamp'] = msg['timestamp'].isoformat()
        
        return JsonResponse({
            'success': True,
            'messages': messages
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@login_required
@require_http_methods(["POST"])
def mark_as_read(request, conversation_id):
    """
    Mark all messages in a conversation as read for the current user
    """
    try:
        count = MessageService.mark_messages_as_read(conversation_id, request.user.id)
        
        return JsonResponse({
            'success': True,
            'marked_count': count
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_message(request, message_id):
    """
    Delete a message
    """
    try:
        success = MessageService.delete_message(message_id, request.user.id)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Failed to delete message'}, status=403)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@login_required
@require_http_methods(["GET"])
def get_unread_count(request):
    """
    Get total unread message count for current user
    """
    try:
        count = MessageService.get_unread_count(request.user.id)
        
        return JsonResponse({
            'success': True,
            'unread_count': count
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def search_users(request):
    """
    Search for users to start a conversation with
    """
    try:
        query = request.GET.get('q', '').strip()
        
        # If no query, show all users
        if not query:
            users = CustomUser.objects.exclude(id=request.user.id).order_by('first_name', 'last_name')[:50]
        else:
            # Search users by username, first name, last name, or email
            users = CustomUser.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            ).exclude(id=request.user.id).order_by('first_name', 'last_name')[:50]
        
        user_list = [
            {
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}",
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
            for user in users
        ]
        
        return JsonResponse({
            'success': True,
            'users': user_list
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def poll_new_messages(request, conversation_id):
    """
    Poll for new messages since a specific timestamp (for real-time updates)
    """
    try:
        from datetime import datetime
        
        since_str = request.GET.get('since')
        if not since_str:
            return JsonResponse({'error': 'Missing since parameter'}, status=400)
        
        # Parse the timestamp - expects ISO format
        try:
            # Python 3.7+ datetime.fromisoformat
            since_timestamp = datetime.fromisoformat(since_str.replace('Z', '+00:00'))
        except Exception:
            return JsonResponse({'error': 'Invalid timestamp format'}, status=400)
        
        # Get new messages
        new_messages = MessageService.get_new_messages_since(conversation_id, since_timestamp)
        
        return JsonResponse({
            'success': True,
            'messages': new_messages,
            'has_new_messages': len(new_messages) > 0
        })
    
    except Exception as e:
        import traceback
        print(f"Error in poll_new_messages: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def poll_conversations(request):
    """
    Poll for updated conversations (for real-time conversation list updates)
    """
    try:
        conversations = MessageService.get_user_conversations(request.user.id)
        
        # Convert datetime objects to ISO format
        for conv in conversations:
            if 'created_at' in conv and conv['created_at']:
                conv['created_at'] = conv['created_at'].isoformat()
            if 'last_message_time' in conv and conv['last_message_time']:
                conv['last_message_time'] = conv['last_message_time'].isoformat()
        
        return JsonResponse({
            'success': True,
            'conversations': conversations
        })
    
    except Exception as e:
        import traceback
        print(f"Error in poll_conversations: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)
