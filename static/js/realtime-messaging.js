/**
 * Real-time Messaging with Firebase Firestore
 * Handles private and group conversations with real-time updates
 */

class RealtimeMessaging {
    constructor() {
        this.currentConversationId = null;
        this.currentConversation = null;
        this.unreadCount = 0;
        this.conversations = [];
        this.conversationMode = 'private'; // 'private' or 'group'
        this.selectedParticipants = [];
        
        // Firebase real-time listeners (replaces polling)
        this.db = null;
        this.unsubscribeConversations = null;
        this.unsubscribeMessages = null;
        this.unsubscribeUnreadCount = null;
        
        this.init();
    }

    init() {
        // Initialize Firebase
        if (typeof firebase !== 'undefined' && typeof firebaseConfig !== 'undefined') {
            try {
                if (!firebase.apps.length) {
                    firebase.initializeApp(firebaseConfig);
                }
                this.db = firebase.firestore();
                console.log('✓ Firebase initialized for real-time messaging');
                
                // ALWAYS load from Django API first (existing data)
                this.loadConversations();
                this.loadUnreadCount();
                
                // Then setup Firebase listeners for real-time updates
                this.setupConversationsListener();
                this.setupUnreadCountListener();
            } catch (error) {
                console.error('Firebase initialization error:', error);
                // Fallback to API polling if Firebase fails
                this.loadConversations();
                this.loadUnreadCount();
            }
        } else {
            // Fallback to API if Firebase not available
            this.loadConversations();
            this.loadUnreadCount();
        }
        
        // Bind event listeners
        this.bindEvents();
    }

    getCurrentUserInfo() {
        // Get user info from the messaging container
        const container = document.querySelector('[data-user-id]');
        if (container) {
            return {
                userId: String(container.dataset.userId || ''),
                userName: String(container.dataset.userName || '')
            };
        }
        return { userId: '', userName: '' };
    }

    bindEvents() {
        // Send message button
        const sendBtn = document.getElementById('sendMessageBtn');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }

        // Message input - send on Enter
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            // Auto-expand textarea (2 lines default, max 6 lines)
            messageInput.addEventListener('input', () => {
                messageInput.style.height = 'auto';
                const lineHeight = 24; // approximate line height
                const minHeight = lineHeight * 2; // 2 lines
                const maxHeight = lineHeight * 6; // 6 lines
                const scrollHeight = messageInput.scrollHeight;
                
                if (scrollHeight > maxHeight) {
                    messageInput.style.height = maxHeight + 'px';
                    messageInput.style.overflowY = 'auto';
                } else if (scrollHeight < minHeight) {
                    messageInput.style.height = minHeight + 'px';
                    messageInput.style.overflowY = 'hidden';
                } else {
                    messageInput.style.height = scrollHeight + 'px';
                    messageInput.style.overflowY = 'hidden';
                }
            });
        }

        // New conversation button
        const newConvBtn = document.getElementById('newConversationBtn');
        if (newConvBtn) {
            newConvBtn.addEventListener('click', () => this.showNewConversationModal());
        }

        // Search users input for PRIVATE chat
        const searchUsersInput = document.getElementById('searchUsersInput');
        if (searchUsersInput) {
            let searchTimeout;
            searchUsersInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchUsers(e.target.value);
                }, 300);
            });
        }

        // Search users input for GROUP chat
        const searchGroupUsersInput = document.getElementById('searchGroupUsersInput');
        if (searchGroupUsersInput) {
            let searchTimeout;
            searchGroupUsersInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchGroupUsers(e.target.value);
                }, 300);
            });
        }
        
        // Add Participant search input
        const addParticipantSearchInput = document.getElementById('addParticipantSearchInput');
        if (addParticipantSearchInput) {
            let searchTimeout;
            addParticipantSearchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchAddParticipants(e.target.value);
                }, 300);
            });
        }

        // Conversation mode toggle
        const privateTabBtn = document.getElementById('privateTabBtn');
        const groupTabBtn = document.getElementById('groupTabBtn');
        
        if (privateTabBtn) {
            privateTabBtn.addEventListener('click', () => this.switchConversationMode('private'));
        }
        if (groupTabBtn) {
            groupTabBtn.addEventListener('click', () => this.switchConversationMode('group'));
        }

        // Create group conversation button
        const createGroupBtn = document.getElementById('createGroupBtn');
        if (createGroupBtn) {
            createGroupBtn.addEventListener('click', () => this.createGroupConversation());
        }

        // Group name input
        const groupNameInput = document.getElementById('groupNameInput');
        if (groupNameInput) {
            groupNameInput.addEventListener('input', (e) => {
                this.updateGroupNamePreview(e.target.value);
            });
        }

        // Add participant button
        const addParticipantBtn = document.getElementById('addParticipantBtn');
        if (addParticipantBtn) {
            addParticipantBtn.addEventListener('click', () => this.showAddParticipantModal());
        }

        // Close modal buttons
        document.querySelectorAll('[data-close-modal]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modalId = e.target.dataset.closeModal;
                this.hideModal(modalId);
            });
        });
    }

    switchConversationMode(mode) {
        this.conversationMode = mode;
        this.selectedParticipants = [];
        
        // Update UI
        const privateTab = document.getElementById('privateTabBtn');
        const groupTab = document.getElementById('groupTabBtn');
        const privateContent = document.getElementById('privateContent');
        const groupContent = document.getElementById('groupContent');
        
        if (mode === 'private') {
            // Update tab styling
            if (privateTab) {
                privateTab.style.color = '#7c3aed';
                privateTab.style.borderColor = '#7c3aed';
            }
            if (groupTab) {
                groupTab.style.color = '#6b7280';
                groupTab.style.borderColor = 'transparent';
            }
            
            privateContent?.classList.remove('hidden');
            groupContent?.classList.add('hidden');
            
            // Load all users for private chat
            this.searchUsers('');
        } else {
            // Update tab styling
            if (groupTab) {
                groupTab.style.color = '#7c3aed';
                groupTab.style.borderColor = '#7c3aed';
            }
            if (privateTab) {
                privateTab.style.color = '#6b7280';
                privateTab.style.borderColor = 'transparent';
            }
            
            privateContent?.classList.add('hidden');
            groupContent?.classList.remove('hidden');
            
            // Load all users for group chat
            this.searchGroupUsers('');
        }
        
        // Clear search results from the other tab
        const privateResults = document.getElementById('userSearchResults');
        const groupResults = document.getElementById('groupUserSearchResults');
        if (mode === 'private' && groupResults) {
            groupResults.innerHTML = '';
        } else if (mode === 'group' && privateResults) {
            privateResults.innerHTML = '';
        }
    }

    async loadConversations() {
        try {
            const response = await fetch('/api/messages/conversations/');
            const data = await response.json();
            
            if (data.success) {
                this.conversations = data.conversations;
                this.renderConversations();
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
        }
    }

    renderConversations() {
        const conversationsList = document.getElementById('conversationsList');
        if (!conversationsList) return;

        if (this.conversations.length === 0) {
            conversationsList.innerHTML = `
                <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                    <p>No conversations yet</p>
                    <p class="text-sm mt-2">Click "New Message" to start a conversation</p>
                </div>
            `;
            return;
        }

        conversationsList.innerHTML = this.conversations.map(conv => {
            const lastMessageTime = conv.last_message?.timestamp ? this.formatDateTime(conv.last_message.timestamp) : '';
            const isActive = conv.conversation_id === this.currentConversationId;
            const isGroup = conv.type === 'group';
            
            // Get username from other_user_name or construct it - with safe fallbacks
            const displayName = isGroup ? (conv.name || 'Group Chat') : (conv.other_user_name || 'Unknown User');
            const username = conv.other_user_username || '';
            const role = conv.other_user_role || conv.role || '';
            const lastMessage = conv.last_message?.message || 'No messages yet';
            const lastSenderId = conv.last_message?.sender_id;
            const lastSenderName = conv.last_message?.sender_name || '';
            const userInfo = this.getCurrentUserInfo();
            const currentUserId = userInfo.userId;
            const currentUserName = userInfo.userName;
            
            // Determine message prefix - use user ID comparison for accuracy, fallback to name
            let messagePrefix = '';
            if (lastSenderId) {
                // Use sender_id if available (most reliable)
                const isCurrentUser = String(lastSenderId) === currentUserId;
                const senderFirstName = lastSenderName.split(' ')[0];
                messagePrefix = isCurrentUser ? 'You: ' : `${senderFirstName}: `;
            } else if (lastSenderName) {
                // Fallback to name comparison if sender_id not available
                const isCurrentUser = lastSenderName.trim() === currentUserName.trim();
                const senderFirstName = lastSenderName.split(' ')[0];
                messagePrefix = isCurrentUser ? 'You: ' : `${senderFirstName}: `;
            }
            
            // Safe display name for initials - ensure it's a string
            const safeDisplayName = String(displayName || 'U');
            
            return `
                <div class="conversation-item ${isActive ? 'active' : ''}" 
                     data-conversation-id="${conv.conversation_id}"
                     onclick="messaging.openConversationById('${conv.conversation_id}')">
                    
                    <div class="flex items-start space-x-3 p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-200 dark:border-gray-700">
                        <div class="flex-shrink-0">
                            ${isGroup ? `
                                <div class="w-12 h-12 rounded-full bg-green-500 text-white flex items-center justify-center font-semibold">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                                    </svg>
                                </div>
                            ` : `
                                <div class="flex-shrink-0 h-12 w-12 rounded-full bg-gradient-to-br from-secondary/20 to-tertiary/20 dark:from-tertiary/20 dark:to-secondary/20 flex items-center justify-center">
                                    ${conv.other_user_profile_pic ? `
                                        <img src="/profile-pics/${conv.other_user_profile_pic}/" alt="${safeDisplayName}" class="h-12 w-12 rounded-full object-cover shadow-inner" onerror="this.onerror=null; this.style.display='none';">
                                    ` : ''}
                                    <span class="text-primary dark:text-tertiary font-bold text-xl">
                                        ${safeDisplayName.split(' ').map(n => n.charAt(0).toUpperCase()).join('')}
                                    </span>
                                </div>
                            `}
                        </div>
                        
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center justify-between mb-1">
                                <p class="text-sm font-semibold text-gray-900 dark:text-white truncate">
                                    ${this.escapeHtml(safeDisplayName)}${username ? ` <span class="text-gray-500 font-normal">(@${this.escapeHtml(username)})</span>` : ''}
                                </p>
                                <p class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap ml-2">
                                    ${lastMessageTime}
                                </p>
                            </div>
                            
                            ${role ? `
                                <p class="text-xs text-gray-500 dark:text-gray-400 capitalize mb-1">
                                    ${this.escapeHtml(role)}
                                </p>
                            ` : ''}
                            
                            <div class="flex items-center justify-between">
                                <p class="text-sm text-gray-600 dark:text-gray-300 truncate">
                                    ${messagePrefix}${this.escapeHtml(lastMessage)}
                                </p>
                                ${conv.unread_count > 0 ? `
                                    <span class="ml-2 bg-red-500 text-white text-xs rounded-full px-2 py-1 flex-shrink-0">
                                        ${conv.unread_count}
                                    </span>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    async openConversationById(conversationId) {
        try {
            const response = await fetch(`/api/messages/conversations/${conversationId}/`);
            const data = await response.json();
            
            if (data.success) {
                this.currentConversationId = conversationId;
                this.currentConversation = data.conversation;
                
                // Update active state
                document.querySelectorAll('.conversation-item').forEach(item => {
                    item.classList.remove('active');
                });
                document.querySelector(`[data-conversation-id="${conversationId}"]`)?.classList.add('active');

                // Show chat area
                const chatArea = document.getElementById('chatArea');
                const emptyState = document.getElementById('emptyState');
                
                if (chatArea) chatArea.classList.remove('hidden');
                if (emptyState) emptyState.classList.add('hidden');

                // Update chat header
                this.updateChatHeader(data.conversation);

                // ALWAYS load existing messages from Django API first (PostgreSQL)
                await this.loadMessages(conversationId);

                // THEN setup Firebase listener for new messages (real-time updates)
                if (this.db) {
                    this.setupMessagesListener(conversationId);
                }

                // Mark messages as read
                await this.markConversationAsRead(conversationId);
            }
        } catch (error) {
            console.error('Error opening conversation:', error);
        }
    }

    updateChatHeader(conversation) {
        const chatHeader = document.getElementById('chatHeader');
        if (!chatHeader) return;

        const isGroup = conversation.type === 'group' || conversation.is_group;
        // For private chats, ONLY show the other person's name
        const displayName = isGroup ? (conversation.name || conversation.title || 'Group Chat') : (conversation.other_user_name || 'Unknown');
        const username = conversation.other_user_username || '';
        const profilePic = conversation.other_user_profile_pic;
        
        chatHeader.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    ${isGroup ? `
                        <div class="w-10 h-10 rounded-full bg-green-500 text-white flex items-center justify-center font-semibold">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                            </svg>
                        </div>
                    ` : `
                        <div class="flex-shrink-0 h-10 w-10 rounded-full bg-gradient-to-br from-secondary/20 to-tertiary/20 dark:from-tertiary/20 dark:to-secondary/20 flex items-center justify-center">
                            ${profilePic ? `
                                <img src="/profile-pics/${profilePic}/" alt="${displayName}" class="h-10 w-10 rounded-full object-cover shadow-inner">
                            ` : `
                                <span class="text-primary dark:text-tertiary font-bold text-lg">
                                    ${displayName.split(' ').map(n => n.charAt(0).toUpperCase()).join('')}
                                </span>
                            `}
                        </div>
                    `}
                    <div>
                        <h3 class="font-semibold text-gray-900 dark:text-white">
                            ${this.escapeHtml(displayName)}${username ? ` <span class="text-gray-500 font-normal">(@${this.escapeHtml(username)})</span>` : ''}
                        </h3>
                        ${isGroup ? `
                            <p class="text-xs text-gray-500 dark:text-gray-400">
                                ${conversation.participants?.length || conversation.participant_count || 0} members
                            </p>
                        ` : ''}
                    </div>
                </div>
                
                ${isGroup ? `
                    <button onclick="messaging.showAddParticipantModal()" 
                            class="px-3 py-1 bg-primary text-white rounded hover:bg-primary-dark text-sm">
                        Add Members
                    </button>
                ` : ''}
            </div>
        `;
    }

    async loadMessages(conversationId) {
        try {
            const response = await fetch(`/api/messages/${conversationId}/`);
            const data = await response.json();
            
            if (data.success) {
                this.renderMessages(data.messages);
            }
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    }

    renderMessages(messages) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;

        const userInfo = this.getCurrentUserInfo();
        const currentUserId = userInfo.userId;
        const isGroup = this.currentConversation?.type === 'group';

        messagesContainer.innerHTML = messages.map(msg => {
            const isSent = String(msg.sender_id) === currentUserId;
            const timestamp = this.formatDateTime(msg.timestamp);
            
            return `
                <div class="message ${isSent ? 'sent' : 'received'} mb-4">
                    <div class="flex ${isSent ? 'justify-end' : 'justify-start'}">
                        <div class="max-w-xs lg:max-w-md">
                            ${!isSent && isGroup ? `
                                <p class="text-xs text-gray-500 dark:text-gray-400 mb-1 font-semibold">
                                    ${this.escapeHtml(msg.sender_name)}
                                </p>
                            ` : ''}
                            <div class="${isSent ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'} rounded-lg px-4 py-2">
                                <p class="text-sm whitespace-pre-wrap">${this.escapeHtml(msg.message)}</p>
                            </div>
                            <div class="flex items-center ${isSent ? 'justify-end' : 'justify-start'} gap-2 mt-1">
                                <p class="text-xs text-gray-500 dark:text-gray-400">
                                    ${timestamp}
                                </p>
                                ${isSent ? `
                                    <span class="text-xs font-bold ${msg.read ? 'text-indigo-600' : 'text-gray-400'}">
                                        ${msg.read ? '✓✓' : '✓✓'}
                                    </span>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    appendMessage(msg) {
        // Helper function to append a single new message to the chat
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;

        const userInfo = this.getCurrentUserInfo();
        const currentUserId = userInfo.userId;
        const isGroup = this.currentConversation?.type === 'group';
        const isSent = String(msg.sender_id) === currentUserId;
        const timestamp = this.formatDateTime(msg.timestamp);
        
        const messageHtml = `
            <div class="message ${isSent ? 'sent' : 'received'} mb-4">
                <div class="flex ${isSent ? 'justify-end' : 'justify-start'}">
                    <div class="max-w-xs lg:max-w-md">
                        ${!isSent && isGroup ? `
                            <p class="text-xs text-gray-500 dark:text-gray-400 mb-1 font-semibold">
                                ${this.escapeHtml(msg.sender_name)}
                            </p>
                        ` : ''}
                        <div class="${isSent ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'} rounded-lg px-4 py-2">
                            <p class="text-sm whitespace-pre-wrap">${this.escapeHtml(msg.message)}</p>
                        </div>
                        <div class="flex items-center ${isSent ? 'justify-end' : 'justify-start'} gap-2 mt-1">
                            <p class="text-xs text-gray-500 dark:text-gray-400">
                                ${timestamp}
                            </p>
                            ${isSent ? `
                                <span class="text-xs font-bold ${msg.read ? 'text-indigo-600' : 'text-gray-400'}">
                                    ${msg.read ? '✓✓' : '✓✓'}
                                </span>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        messagesContainer.insertAdjacentHTML('beforeend', messageHtml);
        
        // Scroll to bottom to show new message
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        if (!messageInput || !this.currentConversationId) return;

        const messageText = messageInput.value.trim();
        if (!messageText) return;

        try {
            const response = await fetch('/api/messages/send/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    conversation_id: this.currentConversationId,
                    message: messageText
                })
            });

            const data = await response.json();
            
            if (data.success) {
                messageInput.value = '';
                
                // Reload messages
                await this.loadMessages(this.currentConversationId);
                
                // Reload conversations to update last message
                await this.loadConversations();
            } else {
                alert('Failed to send message: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message');
        }
    }

    async createGroupConversation() {
        const groupNameInput = document.getElementById('groupNameInput');
        if (!groupNameInput) return;

        const groupName = groupNameInput.value.trim();
        if (!groupName) {
            alert('Please enter a group name');
            return;
        }

        if (this.selectedParticipants.length === 0) {
            alert('Please select at least one participant');
            return;
        }

        try {
            const response = await fetch('/api/messages/conversations/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    type: 'group',
                    name: groupName,
                    participant_ids: this.selectedParticipants.map(p => p.id)
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.hideNewConversationModal();
                this.selectedParticipants = [];
                groupNameInput.value = '';
                
                // Reload conversations
                await this.loadConversations();
                
                // Open the new conversation
                await this.openConversationById(data.conversation_id);
            } else {
                alert('Failed to create group: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error creating group:', error);
            alert('Failed to create group');
        }
    }

    async addParticipantsToGroup(participantIds) {
        if (!this.currentConversationId || participantIds.length === 0) return;

        try {
            const response = await fetch(`/api/messages/conversations/${this.currentConversationId}/add-participants/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    participant_ids: participantIds
                })
            });

            const data = await response.json();
            
            if (data.success) {
                alert('Participants added successfully');
                this.hideModal('addParticipantModal');
                
                // Reload conversation
                await this.openConversationById(this.currentConversationId);
            } else {
                alert('Failed to add participants: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error adding participants:', error);
            alert('Failed to add participants');
        }
    }

    async markConversationAsRead(conversationId) {
        try {
            const response = await fetch(`/api/messages/${conversationId}/`);
            const data = await response.json();
            
            if (data.success) {
                const userInfo = this.getCurrentUserInfo();
                const currentUserId = userInfo.userId;
                const unreadMessages = data.messages.filter(msg => 
                    !msg.read && msg.sender_id !== currentUserId
                );
                
                if (unreadMessages.length > 0) {
                    await fetch(`/api/messages/${conversationId}/mark-read/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCookie('csrftoken')
                        }
                    });
                    
                    this.loadUnreadCount();
                    this.loadConversations();
                }
            }
        } catch (error) {
            console.error('Error marking messages as read:', error);
        }
    }

    async loadUnreadCount() {
        try {
            const response = await fetch('/api/messages/unread-count/');
            const data = await response.json();
            
            if (data.success) {
                this.unreadCount = data.unread_count;
                this.updateUnreadBadge();
            }
        } catch (error) {
            console.error('Error loading unread count:', error);
        }
    }

    updateUnreadBadge() {
        const badge = document.getElementById('unreadMessagesBadge');
        if (badge) {
            if (this.unreadCount > 0) {
                badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }
    }

    async searchUsers(query) {
        // Show all users when empty, or search when there's text
        try {
            const response = await fetch(`/api/messages/search-users/?q=${encodeURIComponent(query || '')}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderUserSearchResults(data.users, 'userSearchResults');
            }
        } catch (error) {
            console.error('Error searching users:', error);
        }
    }

    async searchGroupUsers(query) {
        // Show all users when empty, or search when there's text
        try {
            const response = await fetch(`/api/messages/search-users/?q=${encodeURIComponent(query || '')}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderUserSearchResults(data.users, 'groupUserSearchResults');
            }
        } catch (error) {
            console.error('Error searching users:', error);
        }
    }

    async searchAddParticipants(query) {
        // Show all users when empty, or search when there's text
        try {
            const response = await fetch(`/api/messages/search-users/?q=${encodeURIComponent(query || '')}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderUserSearchResults(data.users, 'addParticipantResults');
            }
        } catch (error) {
            console.error('Error searching users:', error);
        }
    }

    async searchAddParticipants(query) {
        // Show all users when empty, or search when there's text
        try {
            const response = await fetch(`/api/messages/search-users/?q=${encodeURIComponent(query || '')}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderUserSearchResults(data.users, 'addParticipantResults');
            }
        } catch (error) {
            console.error('Error searching users:', error);
        }
    }

    renderUserSearchResults(users, containerId = 'userSearchResults') {
        const resultsContainer = document.getElementById(containerId);
        if (!resultsContainer) return;

        if (users.length === 0) {
            resultsContainer.innerHTML = '<p class="text-gray-500 dark:text-gray-400 text-sm p-4">No users found</p>';
            return;
        }

        const currentUserId = document.body.dataset.userId;

        resultsContainer.innerHTML = users
            .filter(user => user.id !== currentUserId)
            .map(user => {
                const isSelected = this.selectedParticipants.some(p => p.id === user.id);
                
                return `
                    <div class="p-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-200 dark:border-gray-700 ${isSelected ? 'bg-blue-50 dark:bg-blue-900' : ''}"
                         onclick="messaging.toggleParticipantSelection('${user.id}', '${this.escapeHtml(user.name)}', '${user.role}', '${this.escapeHtml(user.email)}', '${this.escapeHtml(user.username || '')}')">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-3">
                                <div class="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-semibold">
                                    ${user.name.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                    <p class="font-semibold text-gray-900 dark:text-white">${this.escapeHtml(user.name)}</p>
                                    <p class="text-xs text-gray-500 dark:text-gray-400">@${this.escapeHtml(user.username || 'N/A')} • ${this.escapeHtml(user.role)}</p>
                                </div>
                            </div>
                            ${isSelected ? `
                                <svg class="w-6 h-6 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                </svg>
                            ` : ''}
                        </div>
                    </div>
                `;
            }).join('');
    }

    toggleParticipantSelection(userId, userName, userRole, userEmail, username = '') {
        const index = this.selectedParticipants.findIndex(p => p.id === userId);
        
        if (index > -1) {
            this.selectedParticipants.splice(index, 1);
        } else {
            if (this.conversationMode === 'private') {
                // For private chats, only one participant
                this.selectedParticipants = [{
                    id: userId,
                    name: userName,
                    role: userRole,
                    email: userEmail,
                    username: username
                }];
                this.startPrivateConversation(userId, userName, userRole);
                return; // Don't re-render for private chat since we're starting conversation
            } else {
                // For group chats, multiple participants
                this.selectedParticipants.push({
                    id: userId,
                    name: userName,
                    role: userRole,
                    email: userEmail,
                    username: username
                });
                this.updateSelectedParticipantsDisplay();
            }
        }
        
        // Re-render to update checkmarks based on current mode
        if (this.conversationMode === 'private') {
            const searchInput = document.getElementById('searchUsersInput');
            if (searchInput && searchInput.value) {
                this.searchUsers(searchInput.value);
            }
        } else {
            const searchInput = document.getElementById('searchGroupUsersInput');
            if (searchInput && searchInput.value) {
                this.searchGroupUsers(searchInput.value);
            }
        }
    }

    updateSelectedParticipantsDisplay() {
        const container = document.getElementById('selectedParticipants');
        if (!container) return;

        if (this.selectedParticipants.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-sm">No participants selected</p>';
            return;
        }

        container.innerHTML = `
            <div class="flex flex-wrap gap-2">
                ${this.selectedParticipants.map(p => `
                    <span class="inline-flex items-center bg-blue-100 text-blue-800 text-xs px-3 py-1 rounded-full">
                        ${p.name}
                        <button onclick="messaging.removeParticipant('${p.id}')" class="ml-2 text-blue-600 hover:text-blue-800">
                            ×
                        </button>
                    </span>
                `).join('')}
            </div>
        `;
    }

    removeParticipant(userId) {
        this.selectedParticipants = this.selectedParticipants.filter(p => p.id !== userId);
        this.updateSelectedParticipantsDisplay();
        this.searchUsers(document.getElementById('searchUsersInput').value);
    }

    async startPrivateConversation(userId, userName, userRole) {
        try {
            const response = await fetch('/api/messages/conversations/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    type: 'private',
                    participant_ids: [userId]
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.hideNewConversationModal();
                this.selectedParticipants = [];
                
                // Reload conversations
                await this.loadConversations();
                
                // Open the conversation
                await this.openConversationById(data.conversation_id);
            } else {
                alert('Failed to create conversation: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error starting conversation:', error);
            alert('Failed to start conversation');
        }
    }

    showNewConversationModal() {
        console.log('showNewConversationModal called');
        const modal = document.getElementById('newConversationModal');
        console.log('Modal element:', modal);
        if (modal) {
            modal.classList.remove('hidden');
            console.log('Modal classes after remove hidden:', modal.className);
            this.switchConversationMode('private');
            
            // Load all users initially for private chat
            this.searchUsers('');
        } else {
            console.error('Modal element not found!');
        }
    }

    hideNewConversationModal() {
        const modal = document.getElementById('newConversationModal');
        if (modal) {
            modal.classList.add('hidden');
            const privateSearch = document.getElementById('searchUsersInput');
            const groupSearch = document.getElementById('searchGroupUsersInput');
            const groupNameInput = document.getElementById('groupNameInput');
            
            if (privateSearch) privateSearch.value = '';
            if (groupSearch) groupSearch.value = '';
            if (groupNameInput) groupNameInput.value = '';
            
            const privateResults = document.getElementById('userSearchResults');
            const groupResults = document.getElementById('groupUserSearchResults');
            if (privateResults) privateResults.innerHTML = '';
            if (groupResults) groupResults.innerHTML = '';
            
            this.selectedParticipants = [];
            this.updateSelectedParticipantsDisplay();
        }
    }

    showAddParticipantModal() {
        const modal = document.getElementById('addParticipantModal');
        if (modal) {
            modal.classList.remove('hidden');
            // Load all users by default
            this.searchAddParticipants('');
        }
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    updateGroupNamePreview(name) {
        const preview = document.getElementById('groupNamePreview');
        if (preview) {
            preview.textContent = name || 'Untitled Group';
        }
    }

    // Firebase Real-time Listeners (replaces polling)
    setupConversationsListener() {
        if (!this.db) return;
        
        const userInfo = this.getCurrentUserInfo();
        const userId = parseInt(userInfo.userId);
        
        if (!userId) return;
        
        // Real-time listener for conversations - ONLY updates when Firestore changes
        this.unsubscribeConversations = this.db.collection('conversations')
            .where('participant_ids', 'array-contains', userId)
            .orderBy('last_message_time', 'desc')
            .onSnapshot((snapshot) => {
                // Only update if there are Firestore conversations
                if (!snapshot.empty) {
                    const firestoreConvs = snapshot.docs.map(doc => {
                        const data = doc.data();
                        return {
                            conversation_id: doc.id,
                            type: data.type || 'private',
                            name: data.name || null,
                            participant_ids: data.participant_ids || [],
                            participants: data.participants || [],
                            last_message: data.last_message || null,
                            other_user_name: data.other_user_name || '',
                            other_user_username: data.other_user_username || '',
                            other_user_role: data.other_user_role || '',
                            role: data.role || ''
                        };
                    });
                    
                    // Merge with existing conversations from Django API
                    const existingIds = this.conversations.map(c => c.conversation_id);
                    const newConvs = firestoreConvs.filter(c => !existingIds.includes(c.conversation_id));
                    
                    if (newConvs.length > 0) {
                        this.conversations = [...newConvs, ...this.conversations];
                        this.renderConversations();
                    }
                }
                
                // If viewing a conversation, refresh messages too
                if (this.currentConversationId) {
                    this.setupMessagesListener(this.currentConversationId);
                }
            }, (error) => {
                console.warn('Firestore listener (optional):', error.message);
                // Don't fallback - API data already loaded
            });
    }
    
    setupMessagesListener(conversationId) {
        if (!this.db) return;
        
        // Unsubscribe previous messages listener
        if (this.unsubscribeMessages) {
            this.unsubscribeMessages();
        }
        
        // Real-time listener for NEW messages only - instant updates!
        // This listener monitors Firestore for new messages and appends them
        this.unsubscribeMessages = this.db.collection('conversations')
            .doc(conversationId)
            .collection('messages')
            .orderBy('timestamp', 'asc')
            .onSnapshot((snapshot) => {
                // Only process new messages added to Firestore
                snapshot.docChanges().forEach(change => {
                    if (change.type === 'added') {
                        const doc = change.doc;
                        const data = doc.data();
                        const newMessage = {
                            message_id: doc.id,
                            sender_id: data.sender_id,
                            sender_name: data.sender_name,
                            message: data.message,
                            timestamp: data.timestamp?.toDate?.() || new Date(data.timestamp),
                            read_by: data.read_by || []
                        };
                        
                        // Append new message to existing messages
                        this.appendMessage(newMessage);
                    }
                });
            }, (error) => {
                console.warn('Firestore messages listener (optional):', error.message);
                // Don't fallback - API data already loaded
            });
    }
    
    setupUnreadCountListener() {
        if (!this.db) return;
        
        const userInfo = this.getCurrentUserInfo();
        const userId = parseInt(userInfo.userId);
        
        if (!userId) return;
        
        // Real-time listener for unread count - instant updates!
        this.unsubscribeUnreadCount = this.db.collection('conversations')
            .where('participant_ids', 'array-contains', userId)
            .onSnapshot((snapshot) => {
                let unreadCount = 0;
                snapshot.docs.forEach(doc => {
                    const data = doc.data();
                    const lastMessage = data.last_message;
                    if (lastMessage && lastMessage.sender_id !== userId) {
                        const readBy = lastMessage.read_by || [];
                        if (!readBy.includes(userId)) {
                            unreadCount++;
                        }
                    }
                });
                this.unreadCount = unreadCount;
                this.updateUnreadBadge();
            }, (error) => {
                console.error('Unread count listener error:', error);
                // Fallback to API
                this.loadUnreadCount();
            });
    }

    startMessagePolling() {
        // NO LONGER NEEDED - using Firebase real-time listeners
        // Kept for backwards compatibility if Firebase fails
    }

    startUnreadPolling() {
        // NO LONGER NEEDED - using Firebase real-time listeners  
        // Kept for backwards compatibility if Firebase fails
    }

    stopPolling() {
        if (this.messagePollingInterval) {
            clearInterval(this.messagePollingInterval);
        }
        if (this.unreadPollingInterval) {
            clearInterval(this.unreadPollingInterval);
        }
    }

    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        // Less than 1 minute
        if (diff < 60000) {
            return 'Just now';
        }
        
        // Less than 1 hour
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes}m ago`;
        }
        
        // Less than 24 hours
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours}h ago`;
        }
        
        // Less than 7 days
        if (diff < 604800000) {
            const days = Math.floor(diff / 86400000);
            return `${days}d ago`;
        }
        
        // Format as date
        return date.toLocaleDateString();
    }

    formatDateTime(timestamp) {
        if (!timestamp) return '';
        
        const date = new Date(timestamp);
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const year = date.getFullYear();
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        
        return `${month}/${day}/${year} ${hours}:${minutes}:${seconds}`;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    cleanup() {
        // Unsubscribe from all Firebase listeners
        if (this.unsubscribeConversations) {
            this.unsubscribeConversations();
        }
        if (this.unsubscribeMessages) {
            this.unsubscribeMessages();
        }
        if (this.unsubscribeUnreadCount) {
            this.unsubscribeUnreadCount();
        }
    }
}

// Initialize messaging when DOM is ready
let messaging;
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Initializing RealtimeMessaging');
    messaging = new RealtimeMessaging();
    console.log('RealtimeMessaging initialized:', messaging);
});

// Cleanup listeners when leaving page
window.addEventListener('beforeunload', function() {
    if (messaging && messaging.cleanup) {
        messaging.cleanup();
    }
});
