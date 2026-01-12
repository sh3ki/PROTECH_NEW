"""
Message Service - PostgreSQL-based messaging implementation
NO FIREBASE - All operations use Django ORM with PostgreSQL
"""

from django.db.models import Q, Max, Prefetch, Count, F
from django.utils import timezone
from PROTECHAPP.models import Chat, Message, ChatParticipant, MessageNotification, CustomUser
from datetime import datetime


class MessageService:
    """
    Complete messaging service using PostgreSQL only
    Handles private and group conversations with read/unread tracking
    """

    @staticmethod
    def create_conversation(creator_id, creator_name, title, participant_ids, participant_names, is_group=False):
        """
        Create a new conversation or return existing one
        For private chats, checks if conversation already exists
        For group chats, always creates a new one
        """
        try:
            # For private chats, check if conversation already exists
            if not is_group:
                # Ensure we have exactly 2 participants for private chat
                if len(participant_ids) < 2:
                    participant_ids.append(creator_id)
                participant_ids = list(set(participant_ids))  # Remove duplicates
                
                if len(participant_ids) == 2:
                    # Find existing private conversation between these exact two users
                    # First filter by both user IDs
                    chats_with_first = Chat.objects.filter(
                        is_group=False,
                        participants__user_id=participant_ids[0]
                    )
                    chats_with_both = chats_with_first.filter(
                        participants__user_id=participant_ids[1]
                    ).annotate(
                        participant_count=Count('participants')
                    ).filter(
                        participant_count=2  # Exactly 2 participants
                    ).first()
                    
                    if chats_with_both:
                        print(f"DEBUG: Found existing chat {chats_with_both.id} between users {participant_ids}")
                        return MessageService._format_conversation(chats_with_both, creator_id)
            
            # Generate title if not provided
            if not title:
                if is_group:
                    title = f"Group Chat - {creator_name}"
                else:
                    # For private chat, use the other participant's name
                    other_name = participant_names[0] if participant_names[0] != creator_name else (participant_names[1] if len(participant_names) > 1 else creator_name)
                    title = other_name
            
            # Create new conversation
            chat = Chat.objects.create(
                name=title,
                is_group=is_group,
                created_by_id=creator_id
            )
            
            # Add participants
            for participant_id in participant_ids:
                ChatParticipant.objects.create(
                    chat=chat,
                    user_id=participant_id
                )
            
            return MessageService._format_conversation(chat)
            
        except Exception as e:
            print(f"Error creating conversation: {str(e)}")
            raise

    @staticmethod
    def get_user_conversations(user_id):
        """
        Get all conversations for a user with unread counts
        Returns list of conversations ordered by last message time
        """
        try:
            # Get all chats where user is a participant
            # Sort by last message time (most recent first) like Facebook Messenger
            # Chats with messages come first, then by created_at for new chats
            user_chats = Chat.objects.filter(
                participants__user_id=user_id
            ).prefetch_related(
                'participants__user',
                Prefetch('messages', queryset=Message.objects.order_by('-sent_at'))
            ).annotate(
                last_message_time=Max('messages__sent_at')
            ).order_by(
                F('last_message_time').desc(nulls_last=True),  # Most recent messages first
                '-created_at'  # Then by creation time for new chats
            )
            
            conversations = []
            for chat in user_chats:
                conversations.append(MessageService._format_conversation(chat, user_id))
            
            return conversations
            
        except Exception as e:
            print(f"Error getting user conversations: {str(e)}")
            return []

    @staticmethod
    def get_conversation(conversation_id, user_id=None):
        """
        Get a specific conversation by ID
        """
        try:
            chat = Chat.objects.prefetch_related(
                'participants__user',
                Prefetch('messages', queryset=Message.objects.order_by('-sent_at'))
            ).get(id=conversation_id)
            
            return MessageService._format_conversation(chat, user_id)
            
        except Chat.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error getting conversation: {str(e)}")
            return None

    @staticmethod
    def send_message(conversation_id, sender_id, sender_name, message_text):
        """
        Send a message in a conversation
        Creates message and notifications for all participants except sender
        """
        try:
            # Get the chat
            chat = Chat.objects.get(id=conversation_id)
            
            # Create the message
            message = Message.objects.create(
                chat=chat,
                sender_id=sender_id,
                message=message_text
            )
            
            # Create notifications for all participants except sender
            participants = ChatParticipant.objects.filter(chat=chat).exclude(user_id=sender_id)
            
            for participant in participants:
                MessageNotification.objects.create(
                    message=message,
                    user_id=participant.user_id,
                    chat=chat,
                    is_read=False
                )
            
            # Format and return message with sender_name
            formatted_msg = MessageService._format_message(message)
            formatted_msg['sender_name'] = sender_name  # Add sender_name to response
            return formatted_msg
            
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            raise

    @staticmethod
    def get_conversation_messages(conversation_id, limit=50, offset=0):
        """
        Get messages for a conversation with pagination
        """
        try:
            messages = Message.objects.filter(
                chat_id=conversation_id
            ).select_related('sender').order_by('sent_at')[offset:offset+limit]
            
            return [MessageService._format_message(msg) for msg in messages]
            
        except Exception as e:
            print(f"Error getting messages: {str(e)}")
            return []

    @staticmethod
    def get_new_messages_since(conversation_id, since_timestamp):
        """
        Get new messages since a specific timestamp
        Used for polling to get real-time updates
        """
        try:
            messages = Message.objects.filter(
                chat_id=conversation_id,
                sent_at__gt=since_timestamp
            ).order_by('sent_at')
            
            return [MessageService._format_message(msg) for msg in messages]
            
        except Exception as e:
            print(f"Error getting new messages: {str(e)}")
            return []

    @staticmethod
    def mark_messages_as_read(conversation_id, user_id):
        """
        Mark all messages in a conversation as read for a specific user
        """
        try:
            # Get all unread message notifications for this user in this conversation
            MessageNotification.objects.filter(
                chat_id=conversation_id,
                user_id=user_id,
                is_read=False
            ).update(is_read=True)
            
            return True
            
        except Exception as e:
            print(f"Error marking messages as read: {str(e)}")
            return False

    @staticmethod
    def get_unread_count(user_id):
        """
        Get total unread message count for a user
        """
        try:
            count = MessageNotification.objects.filter(
                user_id=user_id,
                is_read=False
            ).count()
            
            return count
            
        except Exception as e:
            print(f"Error getting unread count: {str(e)}")
            return 0

    @staticmethod
    def add_participants_to_group(conversation_id, participant_ids):
        """
        Add new participants to a group conversation
        """
        try:
            chat = Chat.objects.get(id=conversation_id)
            
            if not chat.is_group:
                raise ValueError("Cannot add participants to non-group conversations")
            
            # Add participants
            for participant_id in participant_ids:
                # Check if already a participant
                if not ChatParticipant.objects.filter(chat=chat, user_id=participant_id).exists():
                    ChatParticipant.objects.create(
                        chat=chat,
                        user_id=participant_id
                    )
            
            return True
            
        except Exception as e:
            print(f"Error adding participants: {str(e)}")
            raise

    @staticmethod
    def _format_conversation(chat, user_id=None):
        """
        Format a Chat object into a dictionary
        Includes unread count if user_id is provided
        """
        # Get participant names
        participants = chat.participants.select_related('user').all()
        participant_names = [p.user.get_full_name() for p in participants]
        participant_ids = [str(p.user_id) for p in participants]
        
        # Get last message
        last_message_obj = chat.messages.order_by('-sent_at').first()
        last_message = last_message_obj.message if last_message_obj else None
        last_message_time = last_message_obj.sent_at if last_message_obj else chat.created_at
        
        # Get unread count if user_id provided
        unread_count = 0
        if user_id:
            unread_count = MessageNotification.objects.filter(
                chat=chat,
                user_id=user_id,
                is_read=False
            ).count()
        
        return {
            'id': str(chat.id),
            'title': chat.name or 'Unnamed Chat',
            'is_group': chat.is_group,
            'participant_names': participant_names,
            'participant_ids': participant_ids,
            'last_message': last_message,
            'last_message_time': last_message_time,
            'created_at': chat.created_at,
            'unread_count': unread_count
        }

    @staticmethod
    def _format_message(message):
        """
        Format a Message object into a dictionary
        """
        return {
            'id': str(message.id),
            'sender_id': str(message.sender_id),
            'sender_name': message.sender.get_full_name(),
            'message': message.message,
            'sent_at': message.sent_at.isoformat(),
            'chat_id': str(message.chat_id)
        }
