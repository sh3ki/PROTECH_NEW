/**
 * Real-time Messaging with PostgreSQL Polling
 * Handles private and group conversations with real-time updates
 * NO FIREBASE - Uses periodic AJAX polling for real-time experience
 */

class RealtimeMessaging {
    constructor() {
        this.currentConversationId = null;
        this.currentConversation = null;
        this.unreadCount = 0;
        this.conversations = [];
        this.conversationMode = 'private'; // 'private' or 'group'
        this.selectedParticipants = [];
        
        // Polling intervals
        this.conversationsInterval = null;
        this.messagesInterval = null;
        this.unreadCountInterval = null;
        
        // Last message timestamp for efficient polling
        this.lastMessageTimestamp = null;
        
        this.init();
    }

    init() {
        console.log('✓ PostgreSQL-based messaging initialized');
        
        // Load initial data
        this.loadConversations();
        this.loadUnreadCount();
        
        // Start polling for real-time updates
        this.startPolling();
        
        // Bind event listeners
        this.bindEvents();
    }

    startPolling() {
        // Poll conversations every 2 seconds
        this.conversationsInterval = setInterval(() => {
            this.loadConversations();
        }, 2000);
        
        // Poll unread count every 3 seconds
        this.unreadCountInterval = setInterval(() => {
            this.loadUnreadCount();
        }, 3000);
        
        // Poll for new messages every 1 second if a conversation is open
        this.messagesInterval = setInterval(() => {
            if (this.currentConversationId && this.lastMessageTimestamp) {
                this.pollNewMessages();
            }
        }, 1000);
    }

    stopPolling() {
        if (this.conversationsInterval) {
            clearInterval(this.conversationsInterval);
        }
        if (this.messagesInterval) {
            clearInterval(this.messagesInterval);
        }
        if (this.unreadCountInterval) {
            clearInterval(this.unreadCountInterval);
        }
    }

    getCurrentUserInfo() {
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
            
            // Auto-expand textarea
            messageInput.addEventListener('input', () => {
                messageInput.style.height = 'auto';
                const lineHeight = 24;
                const minHeight = lineHeight * 2;
                const maxHeight = lineHeight * 6;
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

        // Search users inputs
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
            privateTabBtn.addEventListener('click', () => this.switchMode('private'));
        }
        
        if (groupTabBtn) {
            groupTabBtn.addEventListener('click', () => this.switchMode('group'));
        }

        // Create group button
        const createGroupBtn = document.getElementById('createGroupBtn');
        if (createGroupBtn) {
            createGroupBtn.addEventListener('click', () => this.createGroupConversation());
        }

        // Add participants button
        const addParticipantsBtn = document.getElementById('addParticipantsBtn');
        if (addParticipantsBtn) {
            addParticipantsBtn.addEventListener('click', () => this.showModal('addParticipantModal'));
        }
    }

    // ============================================================================
    // CONVERSATIONS API
    // ============================================================================

    async loadConversations() {
        try {
            const response = await fetch('/api/messages/conversations/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) throw new Error('Failed to load conversations');
            
            const data = await response.json();
            
            if (data.success) {
                this.conversations = data.conversations;
                this.renderConversations();
                
                // Update unread badge in conversations list
                this.updateUnreadBadges();
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
        }
    }

    async loadConversation(conversationId) {
        this.currentConversationId = conversationId;
        this.lastMessageTimestamp = null;
        
        try {
            // Load conversation details
            const response = await fetch(`/api/messages/conversations/${conversationId}/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) throw new Error('Failed to load conversation');
            
            const data = await response.json();
            
            if (data.success) {
                this.currentConversation = data.conversation;
                this.renderConversationHeader();
            }
            
            // Load messages
            await this.loadMessages(conversationId);
            
            // Mark as read
            await this.markAsRead(conversationId);
            
        } catch (error) {
            console.error('Error loading conversation:', error);
        }
    }

    async loadMessages(conversationId) {
        try {
            const response = await fetch(`/api/messages/${conversationId}/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) throw new Error('Failed to load messages');
            
            const data = await response.json();
            
            if (data.success) {
                this.renderMessages(data.messages);
                
                // Update last message timestamp for polling
                if (data.messages.length > 0) {
                    const lastMsg = data.messages[data.messages.length - 1];
                    this.lastMessageTimestamp = lastMsg.sent_at;
                }
            }
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    }

    async pollNewMessages() {
        if (!this.currentConversationId || !this.lastMessageTimestamp) return;
        
        try {
            const response = await fetch(`/api/messages/conversations/${this.currentConversationId}/poll/?since=${encodeURIComponent(this.lastMessageTimestamp)}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) return;
            
            const data = await response.json();
            
            if (data.success && data.has_new_messages) {
                // Append new messages to the chat
                this.appendMessages(data.messages);
                
                // Update last timestamp
                if (data.messages.length > 0) {
                    const lastMsg = data.messages[data.messages.length - 1];
                    this.lastMessageTimestamp = lastMsg.sent_at;
                }
                
                // Mark as read
                await this.markAsRead(this.currentConversationId);
            }
        } catch (error) {
            console.error('Error polling new messages:', error);
        }
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        if (!messageInput || !this.currentConversationId) return;
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        const userInfo = this.getCurrentUserInfo();
        
        try {
            const response = await fetch('/api/messages/send/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    conversation_id: this.currentConversationId,
                    message: message,
                    sender_id: userInfo.userId,
                    sender_name: userInfo.userName
                })
            });
            
            if (!response.ok) throw new Error('Failed to send message');
            
            const data = await response.json();
            
            if (data.success) {
                // Clear input
                messageInput.value = '';
                messageInput.style.height = 'auto';
                
                // Reload messages immediately to show the sent message
                await this.loadMessages(this.currentConversationId);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message. Please try again.');
        }
    }

    async markAsRead(conversationId) {
        try {
            await fetch(`/api/messages/${conversationId}/mark-read/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            // Reload unread count
            await this.loadUnreadCount();
        } catch (error) {
            console.error('Error marking as read:', error);
        }
    }

    async loadUnreadCount() {
        try {
            const response = await fetch('/api/messages/unread-count/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) return;
            
            const data = await response.json();
            
            if (data.success) {
                this.unreadCount = data.unread_count;
                this.updateUnreadBadge();
            }
        } catch (error) {
            console.error('Error loading unread count:', error);
        }
    }

    // ============================================================================
    // USER SEARCH & NEW CONVERSATIONS
    // ============================================================================

    async searchUsers(query) {
        try {
            const response = await fetch(`/api/messages/search-users/?q=${encodeURIComponent(query)}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) throw new Error('Failed to search users');
            
            const data = await response.json();
            
            if (data.success) {
                this.renderUserSearchResults(data.users);
            }
        } catch (error) {
            console.error('Error searching users:', error);
        }
    }

    async searchGroupUsers(query) {
        try {
            const response = await fetch(`/api/messages/search-users/?q=${encodeURIComponent(query)}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) throw new Error('Failed to search users');
            
            const data = await response.json();
            
            if (data.success) {
                this.renderGroupUserSearchResults(data.users);
            }
        } catch (error) {
            console.error('Error searching users:', error);
        }
    }

    async searchAddParticipants(query) {
        try {
            const response = await fetch(`/api/messages/search-users/?q=${encodeURIComponent(query)}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) throw new Error('Failed to search users');
            
            const data = await response.json();
            
            if (data.success) {
                this.renderAddParticipantResults(data.users);
            }
        } catch (error) {
            console.error('Error searching users:', error);
        }
    }

    async createPrivateConversation(userId, userName) {
        const userInfo = this.getCurrentUserInfo();
        
        try {
            const response = await fetch('/api/messages/conversations/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    participant_ids: [userInfo.userId, userId],
                    is_group: false,
                    type: 'private'
                })
            });
            
            if (!response.ok) throw new Error('Failed to create conversation');
            
            const data = await response.json();
            
            if (data.success) {
                this.hideNewConversationModal();
                await this.loadConversations();
                this.loadConversation(data.conversation_id);
            }
        } catch (error) {
            console.error('Error creating conversation:', error);
            alert('Failed to create conversation. Please try again.');
        }
    }

    async createGroupConversation() {
        const groupNameInput = document.getElementById('groupNameInput');
        const groupName = groupNameInput ? groupNameInput.value.trim() : '';
        
        if (!groupName) {
            alert('Please enter a group name');
            return;
        }
        
        if (this.selectedParticipants.length === 0) {
            alert('Please select at least one participant');
            return;
        }
        
        const userInfo = this.getCurrentUserInfo();
        const participantIds = [userInfo.userId, ...this.selectedParticipants.map(p => p.id)];
        
        try {
            const response = await fetch('/api/messages/conversations/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    title: groupName,
                    participant_ids: participantIds,
                    is_group: true,
                    type: 'group'
                })
            });
            
            if (!response.ok) throw new Error('Failed to create group');
            
            const data = await response.json();
            
            if (data.success) {
                this.hideNewConversationModal();
                this.selectedParticipants = [];
                await this.loadConversations();
                this.loadConversation(data.conversation_id);
            }
        } catch (error) {
            console.error('Error creating group:', error);
            alert('Failed to create group. Please try again.');
        }
    }

    async addParticipantToGroup(userId, userName) {
        if (!this.currentConversationId) return;
        
        try {
            const response = await fetch(`/api/messages/conversations/${this.currentConversationId}/add-participants/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    participant_ids: [userId]
                })
            });
            
            if (!response.ok) throw new Error('Failed to add participant');
            
            const data = await response.json();
            
            if (data.success) {
                this.hideModal('addParticipantModal');
                alert(`${userName} has been added to the group`);
                await this.loadConversation(this.currentConversationId);
            }
        } catch (error) {
            console.error('Error adding participant:', error);
            alert('Failed to add participant. Please try again.');
        }
    }

    // ============================================================================
    // RENDER METHODS
    // ============================================================================

    renderConversations() {
        const container = document.getElementById('conversationsList');
        if (!container) return;
        
        if (this.conversations.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <p>No conversations yet</p>
                    <p class="text-sm">Start a new conversation to begin messaging</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.conversations.map(conv => {
            const isActive = this.currentConversationId === conv.id;
            const unreadBadge = conv.unread_count > 0 ? `
                <div class="bg-red-500 text-white text-xs rounded-full px-2 py-0.5 ml-2">
                    ${conv.unread_count}
                </div>
            ` : '';
            
            return `
                <div class="conversation-item ${isActive ? 'active' : ''}" onclick="window.messaging.loadConversation('${conv.id}')" style="cursor: pointer;">
                    <div class="flex items-start">
                        <div class="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                            <span class="text-primary font-semibold text-lg">${(conv.title || 'Chat').charAt(0).toUpperCase()}</span>
                        </div>
                        <div class="ml-3 flex-1 min-w-0">
                            <div class="flex items-center justify-between">
                                <h4 class="font-semibold text-gray-900 dark:text-white truncate">${conv.title || 'Unnamed Chat'}</h4>
                                ${unreadBadge}
                            </div>
                            <p class="text-sm text-gray-600 dark:text-gray-400 truncate">
                                ${conv.last_message || 'No messages yet'}
                            </p>
                            <p class="text-xs text-gray-500 dark:text-gray-500 mt-1">
                                ${this.formatTimestamp(conv.last_message_time)}
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderConversationHeader() {
        const header = document.getElementById('conversationHeader');
        if (!header || !this.currentConversation) return;
        
        const participants = this.currentConversation.participant_names || [];
        const participantText = participants.length > 2 
            ? `${participants.length} members` 
            : participants.join(', ');
        
        header.innerHTML = `
            <div class="flex items-center justify-between">
                <div>
                    <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
                        ${this.currentConversation.title}
                    </h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        ${participantText}
                    </p>
                </div>
                ${this.currentConversation.is_group ? `
                    <button id="addParticipantsBtn" class="text-primary hover:text-primary/80 font-medium">
                        + Add Members
                    </button>
                ` : ''}
            </div>
        `;
        
        // Re-bind event if group chat
        if (this.currentConversation.is_group) {
            const addBtn = document.getElementById('addParticipantsBtn');
            if (addBtn) {
                addBtn.addEventListener('click', () => this.showModal('addParticipantModal'));
            }
        }
    }

    renderMessages(messages) {
        const container = document.getElementById('messagesContainer');
        if (!container) return;
        
        if (messages.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <p>No messages yet</p>
                    <p class="text-sm">Start the conversation by sending a message</p>
                </div>
            `;
            return;
        }
        
        const userInfo = this.getCurrentUserInfo();
        
        container.innerHTML = messages.map(msg => {
            const isSent = msg.sender_id === userInfo.userId;
            return this.createMessageElement(msg, isSent);
        }).join('');
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    appendMessages(messages) {
        const container = document.getElementById('messagesContainer');
        if (!container || messages.length === 0) return;
        
        const userInfo = this.getCurrentUserInfo();
        const wasAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 50;
        
        messages.forEach(msg => {
            const isSent = msg.sender_id === userInfo.userId;
            const messageHtml = this.createMessageElement(msg, isSent);
            container.insertAdjacentHTML('beforeend', messageHtml);
        });
        
        // Auto-scroll if was at bottom
        if (wasAtBottom) {
            container.scrollTop = container.scrollHeight;
        }
    }

    createMessageElement(msg, isSent) {
        return `
            <div class="message ${isSent ? 'sent' : 'received'}">
                ${!isSent ? `<div class="sender-name">${msg.sender_name}</div>` : ''}
                <div class="message-bubble">
                    ${msg.message}
                </div>
                <div class="message-time">${this.formatTimestamp(msg.sent_at)}</div>
            </div>
        `;
    }

    renderUserSearchResults(users) {
        const container = document.getElementById('userSearchResults');
        if (!container) return;
        
        if (users.length === 0) {
            container.innerHTML = `
                <div class="p-4 text-center text-gray-500">
                    No users found
                </div>
            `;
            return;
        }
        
        container.innerHTML = users.map(user => `
            <div class="user-search-item" onclick="messaging.createPrivateConversation('${user.id}', '${user.name}')">
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                        <span class="text-primary font-semibold">${user.name.charAt(0)}</span>
                    </div>
                    <div class="ml-3">
                        <div class="font-medium text-gray-900 dark:text-white">${user.name}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">${user.role}</div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderGroupUserSearchResults(users) {
        const container = document.getElementById('groupUserSearchResults');
        if (!container) return;
        
        if (users.length === 0) {
            container.innerHTML = `
                <div class="p-4 text-center text-gray-500">
                    No users found
                </div>
            `;
            return;
        }
        
        container.innerHTML = users.map(user => `
            <div class="user-search-item" onclick="messaging.toggleParticipantSelection('${user.id}', '${user.name}')">
                <div class="flex items-center justify-between">
                    <div class="flex items-center">
                        <div class="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                            <span class="text-primary font-semibold">${user.name.charAt(0)}</span>
                        </div>
                        <div class="ml-3">
                            <div class="font-medium text-gray-900 dark:text-white">${user.name}</div>
                            <div class="text-sm text-gray-600 dark:text-gray-400">${user.role}</div>
                        </div>
                    </div>
                    <button class="text-primary hover:text-primary/80">Select</button>
                </div>
            </div>
        `).join('');
    }

    renderAddParticipantResults(users) {
        const container = document.getElementById('addParticipantResults');
        if (!container) return;
        
        if (users.length === 0) {
            container.innerHTML = `
                <div class="p-4 text-center text-gray-500">
                    No users found
                </div>
            `;
            return;
        }
        
        container.innerHTML = users.map(user => `
            <div class="user-search-item" onclick="messaging.addParticipantToGroup('${user.id}', '${user.name}')">
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                        <span class="text-primary font-semibold">${user.name.charAt(0)}</span>
                    </div>
                    <div class="ml-3">
                        <div class="font-medium text-gray-900 dark:text-white">${user.name}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">${user.role}</div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    toggleParticipantSelection(userId, userName) {
        const index = this.selectedParticipants.findIndex(p => p.id === userId);
        
        if (index > -1) {
            this.selectedParticipants.splice(index, 1);
        } else {
            this.selectedParticipants.push({ id: userId, name: userName });
        }
        
        this.renderSelectedParticipants();
    }

    renderSelectedParticipants() {
        const container = document.getElementById('selectedParticipants');
        if (!container) return;
        
        if (this.selectedParticipants.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-sm">No participants selected</p>';
            return;
        }
        
        container.innerHTML = this.selectedParticipants.map(p => `
            <div class="inline-flex items-center bg-primary/10 text-primary px-3 py-1 rounded-full mr-2 mb-2">
                <span class="mr-2">${p.name}</span>
                <button onclick="messaging.toggleParticipantSelection('${p.id}', '${p.name}')" class="hover:text-primary/70">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
            </div>
        `).join('');
    }

    updateUnreadBadge() {
        const badge = document.getElementById('unreadBadge');
        if (!badge) return;
        
        if (this.unreadCount > 0) {
            badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    }

    updateUnreadBadges() {
        // This is called after loading conversations to update individual badges
        this.renderConversations();
    }

    // ============================================================================
    // MODAL & UI HELPERS
    // ============================================================================

    showNewConversationModal() {
        const modal = document.getElementById('newConversationModal');
        if (modal) {
            modal.classList.remove('hidden');
            this.switchMode('private');
        }
    }

    hideNewConversationModal() {
        const modal = document.getElementById('newConversationModal');
        if (modal) {
            modal.classList.add('hidden');
        }
        
        // Clear inputs
        const searchInput = document.getElementById('searchUsersInput');
        const groupNameInput = document.getElementById('groupNameInput');
        const groupSearchInput = document.getElementById('searchGroupUsersInput');
        
        if (searchInput) searchInput.value = '';
        if (groupNameInput) groupNameInput.value = '';
        if (groupSearchInput) groupSearchInput.value = '';
        
        this.selectedParticipants = [];
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    switchMode(mode) {
        this.conversationMode = mode;
        
        const privateTab = document.getElementById('privateTabBtn');
        const groupTab = document.getElementById('groupTabBtn');
        const privateContent = document.getElementById('privateContent');
        const groupContent = document.getElementById('groupContent');
        
        if (mode === 'private') {
            privateTab?.classList.add('text-primary', 'border-primary');
            privateTab?.classList.remove('text-gray-500', 'border-transparent');
            groupTab?.classList.remove('text-primary', 'border-primary');
            groupTab?.classList.add('text-gray-500', 'border-transparent');
            privateContent?.classList.remove('hidden');
            groupContent?.classList.add('hidden');
        } else {
            groupTab?.classList.add('text-primary', 'border-primary');
            groupTab?.classList.remove('text-gray-500', 'border-transparent');
            privateTab?.classList.remove('text-primary', 'border-primary');
            privateTab?.classList.add('text-gray-500', 'border-transparent');
            groupContent?.classList.remove('hidden');
            privateContent?.classList.add('hidden');
        }
    }

    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        
        const diffDays = Math.floor(diffHours / 24);
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }

    getCsrfToken() {
        const name = 'csrftoken';
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
}

// Initialize messaging when page loads
let messaging;
document.addEventListener('DOMContentLoaded', () => {
    messaging = new RealtimeMessaging();
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (messaging) {
        messaging.stopPolling();
    }
});
