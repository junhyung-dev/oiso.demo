const API_BASE = 'http://localhost:8000/api/v1';

// DOM Elements
const sessionListEl = document.getElementById('session-list');
const chatMessagesEl = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const currentSessionTitle = document.getElementById('current-session-title');
const chatForm = document.getElementById('chat-form');

let currentSessionId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // We don't have a GET /sessions endpoint out of the box in the provided API, 
    // but the user only requested to test chat. So we will start by creating one.
    // If the user refreshes, they'll lose sidebar history unless we manually save it or a GET endpoint exists.
    // We will simulate the sidebar by storing sessions in localStorage for demo purposes.
    
    loadSessionsFromStorage();
    
    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value.trim().length > 0) {
            sendBtn.removeAttribute('disabled');
        } else {
            sendBtn.setAttribute('disabled', 'true');
        }
    });

    // Submit on Enter (without shift)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!this.disabled && this.value.trim()) {
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
    });
});

// Create New Session
newChatBtn.addEventListener('click', async () => {
    try {
        newChatBtn.disabled = true;
        
        const response = await fetch(`${API_BASE}/chat/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: "New Chat Session" })
        });
        
        if (!response.ok) throw new Error('Failed to create session');
        
        const session = await response.json();
        saveSessionToStorage(session);
        renderSessionItem(session);
        selectSession(session.id, session.title || "New Chat Session");
        
    } catch (error) {
        console.error(error);
        alert('Error creating chat session. Is the backend running?');
    } finally {
        newChatBtn.disabled = false;
    }
});

// Select a session
async function selectSession(id, title) {
    currentSessionId = id;
    currentSessionTitle.textContent = title;
    
    // UI updates
    document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
    const activeEl = document.querySelector(`[data-id="${id}"]`);
    if(activeEl) activeEl.classList.add('active');
    
    // Enable input
    messageInput.removeAttribute('disabled');
    messageInput.focus();
    
    // Load messages
    await loadMessages(id);
}

// Load Messages
async function loadMessages(sessionId) {
    chatMessagesEl.innerHTML = ''; // Clear current
    
    try {
        const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}/messages`);
        if (!response.ok) {
            // Note: 404 might just mean no messages or session not found
            throw new Error('Failed to load messages');
        }
        
        const messages = await response.json();
        
        if (messages.length === 0) {
            chatMessagesEl.innerHTML = `
                <div class="empty-state">
                    <div class="greeting-icon">✨</div>
                    <h2>Start the conversation</h2>
                    <p>Send a message to begin.</p>
                </div>
            `;
            return;
        }
        
        messages.forEach(msg => {
            const roleClass = msg.role === 'assistant' ? 'ai' : msg.role;
            appendMessage(roleClass, msg.content, false);
        });
        
        scrollToBottom();
        
    } catch (error) {
        console.error(error);
        appendMessage('system', 'Error loading message history.', false);
    }
}

// Send Message
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentSessionId) {
        alert("Please create or select a chat session first.");
        return;
    }
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    messageInput.disabled = true;
    sendBtn.disabled = true;
    
    // Optimistic UI update
    // Remove empty state if present
    const emptyState = document.querySelector('.empty-state');
    if (emptyState) emptyState.remove();
    
    appendMessage('user', message);
    
    // Add loading indicator
    const loadingId = appendMessage('ai', '<div class="typing-indicator"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>', true);
    
    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message
            })
        });
        
        if (!response.ok) throw new Error('API request failed');
        
        const data = await response.json();
        
        // Replace loading indicator with real answer
        updateMessage(loadingId, data.answer);
        
    } catch (error) {
        console.error(error);
        updateMessage(loadingId, '❌ Sorry, an error occurred while connecting to the server.');
    } finally {
        messageInput.disabled = false;
        messageInput.focus();
    }
});

let msgCounter = 0;
function appendMessage(role, content, isRawHTML = false) {
    msgCounter++;
    const messageId = 'msg-' + Date.now() + '-' + msgCounter;
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.id = messageId;
    
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    
    if (isRawHTML) {
        bubble.innerHTML = content;
    } else {
        // Use Marked.js for markdown rendering, assuming it's loaded
        bubble.innerHTML = marked.parse(content);
    }
    
    div.appendChild(bubble);
    chatMessagesEl.appendChild(div);
    scrollToBottom();
    
    return messageId;
}

function updateMessage(messageId, content) {
    const el = document.getElementById(messageId);
    if (el) {
        const bubble = el.querySelector('.bubble');
        bubble.innerHTML = marked.parse(content);
        scrollToBottom();
    }
}

function scrollToBottom() {
    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
}

// LocalStorage helpers for Session Management (since no GET /sessions endpoint)
function saveSessionToStorage(session) {
    let sessions = JSON.parse(localStorage.getItem('chat_sessions') || '[]');
    sessions.unshift(session);
    localStorage.setItem('chat_sessions', JSON.stringify(sessions));
}

function loadSessionsFromStorage() {
    let sessions = JSON.parse(localStorage.getItem('chat_sessions') || '[]');
    sessionListEl.innerHTML = '';
    sessions.forEach(session => {
        renderSessionItem(session);
    });
}

function renderSessionItem(session) {
    const li = document.createElement('li');
    li.className = 'session-item';
    li.dataset.id = session.id;
    li.textContent = session.title || `Session #${session.id}`;
    li.onclick = () => selectSession(session.id, li.textContent);
    sessionListEl.prepend(li); // Add to top
}
