/**
 * Lightning-Fast Real-time Messaging with Firebase Firestore
 * Uses Firestore's real-time listeners - NO POLLING!
 * 
 * IMPORTANT: firebaseConfig is injected by Django template from settings.FIREBASE_WEB_CONFIG
 * Do NOT declare it here - it will cause "already declared" errors
 */

class FirebaseRealtimeMessaging {
    constructor() {
        this.db = null;
        this.currentConversationId = null;
        this.currentConversation = null;
        this.conversations = [];
        this.conversationMode = 'private';
        this.selectedParticipants = [];
        
        // Unsubscribe functions for real-time listeners
        this.unsubscribeConversations = null;
        this.unsubscribeMessages = null;
        this.unsubscribeUnreadCount = null;
        
        this.init();
    }

    async init() {
        try {
            // Initialize Firebase
            if (!firebase.apps.length) {
                firebase.initializeApp(firebaseConfig);
            }
            this.db = firebase.firestore();
            
            // Setup real-time listeners
            this.setupConversationsListener();
            this.setupUnreadCountListener();
            
            // Bind event listeners
            this.bindEvents();
            
            console.log('✓ Firebase real-time messaging initialized');
        } catch (error) {
            console.error('Error initializing Firebase:', error);
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

    /**
     * Setup real-time listener for conversations list
     * Updates automatically when conversations change!
     */
    setupConversationsListener() {
        const { userId } = this.getCurrentUserInfo();
        if (!userId) return;

        // Unsubscribe from previous listener if exists
        if (this.unsubscribeConversations) {
            this.unsubscribeConversations();
        }

        // Real-time listener - fires immediately and on every change
        this.unsubscribeConversations = this.db
            .collection('conversations')
            .where('participant_ids', 'array-contains', userId)
            .orderBy('last_message_time', 'desc')
            .onSnapshot((snapshot) => {
                this.conversations = [];
                
                snapshot.forEach((doc) => {
                    const conv = doc.data();
                    conv.id = doc.id;
                    
                    // Calculate unread count
                    conv.unread_count = this.calculateUnreadCount(conv, userId);
                    
                    this.conversations.push(conv);
                });
                
                // Render conversations instantly
                this.renderConversations();
                this.updateUnreadBadge();
            }, (error) => {
                console.error('Conversations listener error:', error);
            });
    }

    /**
     * Setup real-time listener for messages in current conversation
     * Updates instantly when new messages arrive!
     */
    setupMessagesListener(conversationId) {
        // Unsubscribe from previous messages listener
        if (this.unsubscribeMessages) {
            this.unsubscribeMessages();
        }

        // Real-time listener for messages
        this.unsubscribeMessages = this.db
            .collection('conversations')
            .doc(conversationId)
            .collection('messages')
            .orderBy('timestamp', 'asc')
            .onSnapshot((snapshot) => {
                const messagesContainer = document.getElementById('messagesContainer');
                if (!messagesContainer) return;

                // Clear existing messages
                messagesContainer.innerHTML = '';
                
                const { userId } = this.getCurrentUserInfo();
                const messages = [];
                
                snapshot.forEach((doc) => {
                    const msg = doc.data();
                    msg.id = doc.id;
                    messages.push(msg);
                });
                
                // Render all messages
                messages.forEach(msg => {
                    this.appendMessage(msg, userId);
                });
                
                // Auto-scroll to bottom
                this.scrollToBottom();
                
                // Mark messages as read
                this.markConversationAsRead(conversationId);
            }, (error) => {
                console.error('Messages listener error:', error);
            });
    }

    /**
     * Setup real-time listener for total unread count
     */
    setupUnreadCountListener() {
        const { userId } = this.getCurrentUserInfo();
        if (!userId) return;

        if (this.unsubscribeUnreadCount) {
            this.unsubscribeUnreadCount();
        }

        this.unsubscribeUnreadCount = this.db
            .collection('conversations')
            .where('participant_ids', 'array-contains', userId)
            .onSnapshot((snapshot) => {
                let totalUnread = 0;
                
                snapshot.forEach((doc) => {
                    const conv = doc.data();
                    totalUnread += this.calculateUnreadCount(conv, userId);
                });
                
                this.updateUnreadBadge(totalUnread);
            });
    }

    calculateUnreadCount(conversation, userId) {
        const readStatus = conversation.read_status || {};
        const userReadStatus = readStatus[userId] || {};
        const lastReadTime = userReadStatus.last_read_time;
        
        if (!lastReadTime) {
            return conversation.message_count || 0;
        }
        
        // This is approximate - for exact count, we'd need to query messages
        return 0;
    }

    async openConversation(conversationId) {
        try {
            // Get conversation data
            const convDoc = await this.db.collection('conversations').doc(conversationId).get();
            if (!convDoc.exists) {
                console.error('Conversation not found');
                return;
            }

            this.currentConversationId = conversationId;
            this.currentConversation = convDoc.data();
            this.currentConversation.id = conversationId;

            // Show chat area
            document.getElementById('emptyState')?.classList.add('hidden');
            document.getElementById('chatArea')?.classList.remove('hidden');

            // Render header
            this.renderChatHeader();

            // Setup real-time messages listener
            this.setupMessagesListener(conversationId);

            // Update active conversation in sidebar
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.remove('active');
            });
            const activeItem = document.querySelector(`[data-conversation-id="${conversationId}"]`);
            if (activeItem) {
                activeItem.classList.add('active');
            }

        } catch (error) {
            console.error('Error opening conversation:', error);
        }
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const messageText = messageInput?.value.trim();
        
        if (!messageText || !this.currentConversationId) return;

        const { userId, userName } = this.getCurrentUserInfo();
        if (!userId) return;

        try {
            const timestamp = firebase.firestore.FieldValue.serverTimestamp();
            
            // Add message to Firestore
            await this.db
                .collection('conversations')
                .doc(this.currentConversationId)
                .collection('messages')
                .add({
                    sender_id: userId,
                    sender_name: userName,
                    message: messageText,
                    timestamp: timestamp,
                    read_by: [userId]
                });

            // Update conversation's last message
            await this.db
                .collection('conversations')
                .doc(this.currentConversationId)
                .update({
                    last_message: messageText,
                    last_message_time: timestamp,
                    last_message_sender: userName,
                    last_message_sender_id: userId
                });

            // Clear input
            messageInput.value = '';
            messageInput.style.height = 'auto';

        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message. Please try again.');
        }
    }

    async markConversationAsRead(conversationId) {
        const { userId } = this.getCurrentUserInfo();
        if (!userId) return;

        try {
            await this.db
                .collection('conversations')
                .doc(conversationId)
                .update({
                    [`read_status.${userId}.last_read_time`]: firebase.firestore.FieldValue.serverTimestamp()
                });
        } catch (error) {
            console.error('Error marking conversation as read:', error);
        }
    }

    renderConversations() {
        const conversationsList = document.getElementById('conversationsList');
        if (!conversationsList) return;

        if (this.conversations.length === 0) {
            conversationsList.innerHTML = `
                <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                    <p>No conversations yet</p>
                    <p class="text-sm mt-2">Click "New Message" to start</p>
                </div>
            `;
            return;
        }

        conversationsList.innerHTML = '';
        
        this.conversations.forEach(conv => {
            const isActive = conv.id === this.currentConversationId;
            const unreadBadge = conv.unread_count > 0 
                ? `<span class="bg-red-500 text-white text-xs rounded-full px-2 py-1 ml-2">${conv.unread_count}</span>`
                : '';
            
            const lastMessageTime = this.formatTimestamp(conv.last_message_time);
            const lastMessage = conv.last_message || 'No messages yet';
            const title = conv.title || 'Untitled Conversation';
            
            const conversationHTML = `
                <div class="conversation-item ${isActive ? 'active' : ''} p-4 border-b border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                     data-conversation-id="${conv.id}"
                     onclick="messaging.openConversation('${conv.id}')">
                    <div class="flex items-center justify-between mb-1">
                        <h3 class="font-semibold text-gray-900 dark:text-white flex items-center">
                            ${conv.is_group ? '👥' : '💬'} ${title}
                            ${unreadBadge}
                        </h3>
                        <span class="text-xs text-gray-500 dark:text-gray-400">${lastMessageTime}</span>
                    </div>
                    <p class="text-sm text-gray-600 dark:text-gray-400 truncate">${lastMessage}</p>
                </div>
            `;
            
            conversationsList.insertAdjacentHTML('beforeend', conversationHTML);
        });
    }

    renderChatHeader() {
        const chatHeader = document.getElementById('chatHeader');
        if (!chatHeader || !this.currentConversation) return;

        const title = this.currentConversation.title || 'Conversation';
        const participants = this.currentConversation.participant_names?.join(', ') || '';
        
        chatHeader.innerHTML = `
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
                        ${this.currentConversation.is_group ? '👥' : '💬'} ${title}
                    </h2>
                    <p class="text-sm text-gray-500 dark:text-gray-400">${participants}</p>
                </div>
                ${this.currentConversation.is_group ? `
                    <button onclick="messaging.showModal('addParticipantModal')" 
                            class="bg-primary hover:bg-primary/90 text-white px-3 py-1 rounded text-sm">
                        + Add Members
                    </button>
                ` : ''}
            </div>
        `;
    }

    appendMessage(message, currentUserId) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;

        const isSentByMe = String(message.sender_id) === String(currentUserId);
        const timestamp = this.formatTimestamp(message.timestamp);
        
        const messageHTML = `
            <div class="message flex ${isSentByMe ? 'justify-end' : 'justify-start'}">
                <div class="max-w-[70%] ${isSentByMe ? 'bg-primary text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'} rounded-lg px-4 py-2">
                    ${!isSentByMe ? `<p class="text-xs font-semibold mb-1 opacity-75">${message.sender_name}</p>` : ''}
                    <p class="break-words">${this.escapeHtml(message.message)}</p>
                    <p class="text-xs mt-1 opacity-75">${timestamp}</p>
                </div>
            </div>
        `;
        
        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('messagesContainer');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        
        let date;
        if (timestamp.toDate) {
            date = timestamp.toDate();
        } else if (timestamp instanceof Date) {
            date = timestamp;
        } else {
            date = new Date(timestamp);
        }
        
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

    updateUnreadBadge(count) {
        // Update total unread count in sidebar/navigation if exists
        const badge = document.getElementById('unreadMessagesBadge');
        if (badge) {
            if (count && count > 0) {
                badge.textContent = count;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Modal and UI helper methods
    showNewConversationModal() {
        document.getElementById('newConversationModal')?.classList.remove('hidden');
        this.switchToPrivateTab();
    }

    hideNewConversationModal() {
        document.getElementById('newConversationModal')?.classList.add('hidden');
        document.getElementById('searchUsersInput').value = '';
        document.getElementById('userSearchResults').innerHTML = '';
    }

    showModal(modalId) {
        document.getElementById(modalId)?.classList.remove('hidden');
    }

    hideModal(modalId) {
        document.getElementById(modalId)?.classList.add('hidden');
    }

    switchToPrivateTab() {
        this.conversationMode = 'private';
        document.getElementById('privateTabBtn')?.classList.add('border-b-2', 'border-primary', 'text-primary');
        document.getElementById('groupTabBtn')?.classList.remove('border-b-2', 'border-primary', 'text-primary');
        document.getElementById('privateContent')?.classList.remove('hidden');
        document.getElementById('groupContent')?.classList.add('hidden');
    }

    switchToGroupTab() {
        this.conversationMode = 'group';
        document.getElementById('groupTabBtn')?.classList.add('border-b-2', 'border-primary', 'text-primary');
        document.getElementById('privateTabBtn')?.classList.remove('border-b-2', 'border-primary', 'text-primary');
        document.getElementById('groupContent')?.classList.remove('hidden');
        document.getElementById('privateContent')?.classList.add('hidden');
    }

    async searchUsers(query) {
        if (!query || query.length < 2) {
            document.getElementById('userSearchResults').innerHTML = '';
            return;
        }

        try {
            const response = await fetch(`/api/messages/search-users/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            this.renderUserSearchResults(data.users || []);
        } catch (error) {
            console.error('Error searching users:', error);
        }
    }

    renderUserSearchResults(users) {
        const resultsContainer = document.getElementById('userSearchResults');
        if (!resultsContainer) return;

        if (users.length === 0) {
            resultsContainer.innerHTML = '<p class="p-4 text-gray-500 text-center">No users found</p>';
            return;
        }

        resultsContainer.innerHTML = '';
        users.forEach(user => {
            const userHTML = `
                <div class="p-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-200 dark:border-gray-600"
                     onclick="messaging.createPrivateConversation(${user.id}, '${user.name}')">
                    <p class="font-semibold text-gray-900 dark:text-white">${user.name}</p>
                    <p class="text-sm text-gray-500 dark:text-gray-400">${user.role}</p>
                </div>
            `;
            resultsContainer.insertAdjacentHTML('beforeend', userHTML);
        });
    }

    async createPrivateConversation(participantId, participantName) {
        const { userId, userName } = this.getCurrentUserInfo();
        if (!userId) return;

        try {
            // Create conversation ID for private chat
            const convId = [userId, String(participantId)].sort().join('_');
            const conversationId = `private_${convId}`;

            // Check if conversation exists
            const convDoc = await this.db.collection('conversations').doc(conversationId).get();
            
            if (convDoc.exists) {
                // Open existing conversation
                this.openConversation(conversationId);
            } else {
                // Create new conversation
                await this.db.collection('conversations').doc(conversationId).set({
                    title: `${userName} & ${participantName}`,
                    is_group: false,
                    creator_id: userId,
                    creator_name: userName,
                    participant_ids: [userId, String(participantId)],
                    participant_names: [userName, participantName],
                    created_at: firebase.firestore.FieldValue.serverTimestamp(),
                    last_message: null,
                    last_message_time: firebase.firestore.FieldValue.serverTimestamp(),
                    last_message_sender: null,
                    last_message_sender_id: null,
                    read_status: {}
                });

                this.openConversation(conversationId);
            }

            this.hideNewConversationModal();
        } catch (error) {
            console.error('Error creating conversation:', error);
            alert('Failed to create conversation');
        }
    }

    bindEvents() {
        // Send message
        const sendBtn = document.getElementById('sendMessageBtn');
        sendBtn?.addEventListener('click', () => this.sendMessage());

        const messageInput = document.getElementById('messageInput');
        messageInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // New conversation
        const newConvBtn = document.getElementById('newConversationBtn');
        newConvBtn?.addEventListener('click', () => this.showNewConversationModal());

        // Search users
        const searchUsersInput = document.getElementById('searchUsersInput');
        let searchTimeout;
        searchUsersInput?.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => this.searchUsers(e.target.value), 300);
        });

        // Tab switching
        document.getElementById('privateTabBtn')?.addEventListener('click', () => this.switchToPrivateTab());
        document.getElementById('groupTabBtn')?.addEventListener('click', () => this.switchToGroupTab());
    }

    cleanup() {
        // Unsubscribe from all listeners when leaving page
        if (this.unsubscribeConversations) this.unsubscribeConversations();
        if (this.unsubscribeMessages) this.unsubscribeMessages();
        if (this.unsubscribeUnreadCount) this.unsubscribeUnreadCount();
    }
}

// Initialize messaging when DOM is ready
let messaging;
document.addEventListener('DOMContentLoaded', () => {
    messaging = new FirebaseRealtimeMessaging();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (messaging) messaging.cleanup();
});
