let chatSocket = null;
const chatLog = document.getElementById('chat-log');
const messageInput = document.getElementById('chat-message-input');
const submitButton = document.getElementById('chat-message-submit');
const replyInfo = document.getElementById('reply-info');
const replyUsername = document.getElementById('reply-username');
const replyToId = document.getElementById('reply-to-id');
const cancelReply = document.getElementById('cancel-reply');

function initializeChat() {
    scrollToBottom();
    setupEventListeners();
    connectWebSocket();
}

function scrollToBottom() {
    chatLog.scrollTop = chatLog.scrollHeight;
}

function setupEventListeners() {
    // Обработка клика на кнопку ответа
    chatLog.addEventListener('click', (e) => {
        const replyBtn = e.target.closest('.reply-btn');
        if (!replyBtn) return;
        
        const messageId = replyBtn.dataset.replyTo;
        const username = replyBtn.dataset.username;
        
        if (!messageId) {
            console.error('Reply button has no message ID');
            return;
        }
        
        replyToId.value = messageId;
        replyUsername.textContent = username;
        replyInfo.style.display = 'block';
        messageInput.focus();
    });

    // Отмена ответа
    cancelReply.addEventListener('click', () => {
        replyToId.value = '';
        replyInfo.style.display = 'none';
    });

    // Отправка по Enter
    messageInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Отправка по клику
    submitButton.addEventListener('click', sendMessage);
}

function createMessageElement(data) {
    const element = document.createElement('div');
    
    if (data.status) {
        element.className = 'system-message';
        const action = data.status === 'Join' ? 'присоединился' : 'покинул';
        element.textContent = `${data.username} ${action} чат`;
        return element;
    }

    element.className = 'message';
    if (data.is_own) element.classList.add('own-message');
    element.dataset.messageId = data.id;

    const time = new Date(data.timestamp).toLocaleTimeString([], {
        hour: '2-digit', 
        minute: '2-digit'
    });

    element.innerHTML = `
        <div class="message-user">
            <a href="${data.profile_url}" class="profile-link">
                <img src="${data.avatar}" class="message-avatar" alt="${data.username}">
                <span class="message-author">${data.username}</span>
            </a>
        </div>
        <div class="message-content">
            ${data.reply_to ? `
            <div class="reply-preview">
                <img src="${data.reply_to.avatar}" class="reply-avatar">
                <span class="reply-to">Ответ ${data.reply_to.username}:</span>
                <div class="reply-content">${data.reply_to.content}</div>
            </div>
            ` : ''}
            <div class="message-bubble">${data.content}</div>
            <div class="message-footer">
                <span class="message-time">${time}</span>
                ${!data.is_own ? `
                <button class="reply-btn" 
                        data-reply-to="${data.id}" 
                        data-username="${data.username}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                </button>
                ` : ''}
            </div>
        </div>
    `;

    return element;
}

function connectWebSocket() {
    if (chatSocket) {
        chatSocket.onclose = null;
        chatSocket.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    chatSocket = new WebSocket(`${protocol}${window.location.host}${window.location.pathname}`);
    
    chatSocket.onopen = () => console.log("WebSocket connected");

    chatSocket.onmessage = (e) => {
        try {
            const data = JSON.parse(e.data);
            const messageElement = createMessageElement(data);
            
            // Плавное добавление нового сообщения
            messageElement.style.opacity = '0';
            chatLog.appendChild(messageElement);
            setTimeout(() => {
                messageElement.style.transition = 'opacity 0.3s ease';
                messageElement.style.opacity = '1';
            }, 10);
            
            scrollToBottom();
        } catch (error) {
            console.error('Error processing message:', error);
        }
    };

    chatSocket.onclose = () => {
        console.log("WebSocket disconnected. Reconnecting...");
        setTimeout(connectWebSocket, 2000);
    };

    chatSocket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
}

function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || !chatSocket) return;
    
    const messageData = {
        type: "text_message",
        message: message,
        reply_to: replyToId.value || null
    };
    
    if (chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify(messageData));
        messageInput.value = '';
        if (replyToId.value) {
            replyToId.value = '';
            replyInfo.style.display = 'none';
        }
        messageInput.focus();
    } else {
        console.error("Cannot send message - WebSocket not connected");
    }
}

document.addEventListener('DOMContentLoaded', initializeChat);