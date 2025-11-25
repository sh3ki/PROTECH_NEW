"""
Complete Message Service - Handles all Firestore message operations
Supports both private (1-on-1) and group conversations with full read/unread tracking
"""
from datetime import datetime
from PROTECH.firebase_config import get_firestore_client, is_firebase_configured

class MessageService:
    """
    Complete messaging service for private and group conversations
    """
    
    MESSAGES_COLLECTION = 'messages'
    CONVERSATIONS_COLLECTION = 'conversations'
    
    # ============================================================================
    # CONVERSATION MANAGEMENT
    # ============================================================================
    
    @staticmethod
    def create_conversation(creator_id, creator_name, title, participant_ids, participant_names, is_group=False):
        """
        Create a new conversation (private or group)
        
        Args:
            creator_id: ID of user creating the conversation
            creator_name: Name of creator
            title: Conversation title (for groups) or None for private
            participant_ids: List of participant user IDs (including creator)
            participant_names: List of participant names
            is_group: True for group chat, False for private
            
        Returns:
            dict: Conversation data with ID
        """
        if not is_firebase_configured():
            return None
        
        try:
            db = get_firestore_client()
            
            # For private chats, create consistent conversation ID
            if not is_group and len(participant_ids) == 2:
                conversation_id = MessageService._create_conversation_id(participant_ids[0], participant_ids[1])
                
                # Check if conversation already exists
                existing_conv = db.collection(MessageService.CONVERSATIONS_COLLECTION).document(conversation_id).get()
                if existing_conv.exists:
                    conv_data = existing_conv.to_dict()
                    conv_data['id'] = conversation_id
                    return conv_data
            else:
                conversation_id = None  # Will be auto-generated for groups
            
            # Create conversation document
            conversation_data = {
                'title': title or f"{participant_names[0]} & {participant_names[1]}" if not is_group else title,
                'is_group': is_group,
                'creator_id': str(creator_id),
                'creator_name': creator_name,
                'participant_ids': [str(pid) for pid in participant_ids],
                'participant_names': participant_names,
                'created_at': datetime.now(),
                'last_message': None,
                'last_message_time': datetime.now(),
                'last_message_sender': None,
                'last_message_sender_id': None
            }
            
            if conversation_id:
                # Use specific ID for private chats
                db.collection(MessageService.CONVERSATIONS_COLLECTION).document(conversation_id).set(conversation_data)
                conversation_data['id'] = conversation_id
            else:
                # Auto-generate ID for group chats
                doc_ref = db.collection(MessageService.CONVERSATIONS_COLLECTION).add(conversation_data)
                conversation_data['id'] = doc_ref[1].id
            
            return conversation_data
            
        except Exception as e:
            return None
    
    @staticmethod
    def get_user_conversations(user_id):
        """
        Get all conversations for a user (both private and group)
        
        Args:
            user_id: ID of the user
            
        Returns:
            list: List of conversations with unread count
        """
        if not is_firebase_configured():
            return []
        
        try:
            db = get_firestore_client()
            
            # Get conversations where user is a participant
            conversations_ref = db.collection(MessageService.CONVERSATIONS_COLLECTION)
            user_id_str = str(user_id)
            query = conversations_ref.where('participant_ids', 'array_contains', user_id_str)
            
            conversations = []
            for doc in query.stream():
                conv = doc.to_dict()
                conv['id'] = doc.id
                
                # Get unread count for this conversation
                conv['unread_count'] = MessageService.get_unread_count_for_conversation(conv['id'], user_id)
                
                conversations.append(conv)
            
            # Sort by last message time
            conversations.sort(key=lambda x: x.get('last_message_time', datetime.min), reverse=True)
            
            return conversations
            
        except Exception as e:
            print(f"Error getting conversations: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_conversation(conversation_id):
        """
        Get a specific conversation by ID
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            dict: Conversation data or None
        """
        if not is_firebase_configured():
            return None
        
        try:
            db = get_firestore_client()
            doc = db.collection(MessageService.CONVERSATIONS_COLLECTION).document(conversation_id).get()
            
            if doc.exists:
                conv = doc.to_dict()
                conv['id'] = doc.id
                return conv
            return None
            
        except Exception as e:
            print(f"Error getting conversation: {e}")
            return None
    
    @staticmethod
    def update_conversation_last_message(conversation_id, message_text, sender_name, sender_id):
        """
        Update conversation's last message info
        
        Args:
            conversation_id: ID of the conversation
            message_text: Last message text
            sender_name: Name of sender
            sender_id: ID of sender
        """
        if not is_firebase_configured():
            return
        
        try:
            db = get_firestore_client()
            db.collection(MessageService.CONVERSATIONS_COLLECTION).document(conversation_id).update({
                'last_message': message_text,
                'last_message_time': datetime.now(),
                'last_message_sender': sender_name,
                'last_message_sender_id': str(sender_id)
            })
        except Exception as e:
            print(f"Error updating conversation: {e}")
    
    @staticmethod
    def add_participants_to_group(conversation_id, participant_ids, participant_names):
        """
        Add participants to a group conversation
        
        Args:
            conversation_id: ID of the conversation
            participant_ids: List of user IDs to add
            participant_names: List of user names to add
            
        Returns:
            bool: Success status
        """
        if not is_firebase_configured():
            return False
        
        try:
            db = get_firestore_client()
            conv_ref = db.collection(MessageService.CONVERSATIONS_COLLECTION).document(conversation_id)
            conv = conv_ref.get()
            
            if not conv.exists:
                return False
            
            conv_data = conv.to_dict()
            
            # Check if it's a group
            if not conv_data.get('is_group', False):
                return False
            
            # Add new participants (avoid duplicates)
            current_ids = set(conv_data.get('participant_ids', []))
            current_names = conv_data.get('participant_names', [])
            
            for pid, pname in zip(participant_ids, participant_names):
                if str(pid) not in current_ids:
                    current_ids.add(str(pid))
                    current_names.append(pname)
            
            conv_ref.update({
                'participant_ids': list(current_ids),
                'participant_names': current_names
            })
            
            return True
            
        except Exception as e:
            print(f"Error adding participants: {e}")
            return False
    
    # ============================================================================
    # MESSAGE MANAGEMENT
    # ============================================================================
    
    @staticmethod
    def send_message(conversation_id, sender_id, sender_name, sender_role, message_text, message_type='text'):
        """
        Send a message to a conversation
        
        Args:
            conversation_id: ID of the conversation
            sender_id: ID of the sender
            sender_name: Name of the sender
            sender_role: Role of the sender
            message_text: The message content
            message_type: Type of message (text, image, file, etc.)
            
        Returns:
            dict: Message data with ID if successful
        """
        if not is_firebase_configured():
            return None
        
        try:
            db = get_firestore_client()
            
            # Get conversation to get participants
            conv = db.collection(MessageService.CONVERSATIONS_COLLECTION).document(conversation_id).get()
            if not conv.exists:
                return None
            
            conv_data = conv.to_dict()
            participant_ids = conv_data.get('participant_ids', [])
            
            # Create message document
            message_data = {
                'conversation_id': conversation_id,
                'sender_id': str(sender_id),
                'sender_name': sender_name,
                'sender_role': sender_role,
                'message': message_text,
                'message_type': message_type,
                'timestamp': datetime.now(),
                'read_by': [str(sender_id)],  # Sender has read their own message
                'delivered_to': [],
                'is_deleted': False
            }
            
            # Add message to Firestore
            doc_ref = db.collection(MessageService.MESSAGES_COLLECTION).add(message_data)
            message_data['id'] = doc_ref[1].id
            
            # Update conversation's last message
            MessageService.update_conversation_last_message(conversation_id, message_text, sender_name, sender_id)
            
            return message_data
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    @staticmethod
    def get_conversation_messages(conversation_id, limit=100):
        """
        Get messages in a conversation
        
        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of messages to retrieve
            
        Returns:
            list: List of messages with 'read' field indicating if all participants read the message
        """
        if not is_firebase_configured():
            return []
        
        try:
            db = get_firestore_client()
            
            # Get conversation to know participant count
            conversation = MessageService.get_conversation(conversation_id)
            if not conversation:
                return []
            
            participant_ids = conversation.get('participant_ids', [])
            
            messages_ref = db.collection(MessageService.MESSAGES_COLLECTION)
            query = messages_ref.where('conversation_id', '==', conversation_id).where('is_deleted', '==', False).order_by('timestamp').limit(limit)
            
            messages = []
            for doc in query.stream():
                msg = doc.to_dict()
                msg['id'] = doc.id
                
                # Determine if message is fully read by all participants (except sender)
                read_by = msg.get('read_by', [])
                sender_id = str(msg.get('sender_id', ''))
                
                # Count how many participants should have read it (all except sender)
                expected_readers = [str(pid) for pid in participant_ids if str(pid) != sender_id]
                actual_readers = [str(uid) for uid in read_by]
                
                # Check if all expected readers have read it
                msg['read'] = all(reader in actual_readers for reader in expected_readers) if expected_readers else False
                
                messages.append(msg)
            
            return messages
            
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    @staticmethod
    def mark_messages_as_read(conversation_id, user_id):
        """
        Mark all messages in a conversation as read by a user
        
        Args:
            conversation_id: ID of the conversation
            user_id: ID of the user marking as read
            
        Returns:
            int: Number of messages marked as read
        """
        if not is_firebase_configured():
            return 0
        
        try:
            db = get_firestore_client()
            
            # Get unread messages in this conversation
            messages_ref = db.collection(MessageService.MESSAGES_COLLECTION)
            query = messages_ref.where('conversation_id', '==', conversation_id).where('is_deleted', '==', False)
            
            count = 0
            for doc in query.stream():
                msg_data = doc.to_dict()
                read_by = msg_data.get('read_by', [])
                
                # If user hasn't read this message and isn't the sender
                if str(user_id) not in read_by and msg_data.get('sender_id') != str(user_id):
                    read_by.append(str(user_id))
                    doc.reference.update({'read_by': read_by})
                    count += 1
            
            return count
            
        except Exception as e:
            print(f"Error marking messages as read: {e}")
            return 0
    
    @staticmethod
    def delete_message(message_id, user_id):
        """
        Soft delete a message (only sender can delete)
        
        Args:
            message_id: ID of the message
            user_id: ID of the user attempting to delete
            
        Returns:
            bool: Success status
        """
        if not is_firebase_configured():
            return False
        
        try:
            db = get_firestore_client()
            doc_ref = db.collection(MessageService.MESSAGES_COLLECTION).document(message_id)
            doc = doc_ref.get()
            
            if doc.exists:
                msg_data = doc.to_dict()
                
                # Only sender can delete
                if msg_data.get('sender_id') == str(user_id):
                    doc_ref.update({'is_deleted': True})
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting message: {e}")
            return False
    
    # ============================================================================
    # UNREAD TRACKING
    # ============================================================================
    
    @staticmethod
    def get_unread_count_for_conversation(conversation_id, user_id):
        """
        Get count of unread messages in a conversation for a user
        
        Args:
            conversation_id: ID of the conversation
            user_id: ID of the user
            
        Returns:
            int: Number of unread messages
        """
        if not is_firebase_configured():
            return 0
        
        try:
            db = get_firestore_client()
            
            messages_ref = db.collection(MessageService.MESSAGES_COLLECTION)
            query = messages_ref.where('conversation_id', '==', conversation_id).where('is_deleted', '==', False)
            
            unread_count = 0
            for doc in query.stream():
                msg_data = doc.to_dict()
                read_by = msg_data.get('read_by', [])
                sender_id = msg_data.get('sender_id')
                
                # Count if user hasn't read it and isn't the sender
                if str(user_id) not in read_by and sender_id != str(user_id):
                    unread_count += 1
            
            return unread_count
            
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0
    
    @staticmethod
    def get_total_unread_count(user_id):
        """
        Get total count of unread messages across all conversations
        
        Args:
            user_id: ID of the user
            
        Returns:
            int: Total number of unread messages
        """
        if not is_firebase_configured():
            return 0
        
        try:
            conversations = MessageService.get_user_conversations(user_id)
            total_unread = sum(conv.get('unread_count', 0) for conv in conversations)
            return total_unread
            
        except Exception as e:
            print(f"Error getting total unread count: {e}")
            return 0
    
    # ============================================================================
    # UTILITIES
    # ============================================================================
    
    @staticmethod
    def _create_conversation_id(user1_id, user2_id):
        """
        Create a consistent conversation ID from two user IDs (for private chats)
        
        Args:
            user1_id: First user ID
            user2_id: Second user ID
            
        Returns:
            str: Conversation ID
        """
        ids = sorted([str(user1_id), str(user2_id)])
        return f"private_{ids[0]}_{ids[1]}"
