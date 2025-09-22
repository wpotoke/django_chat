let chatSocket = null;
const chatLog = document.getElementById('chat-log');
const messageInput = document.getElementById('chat-message-input');
const submitButton = document.getElementById('chat-message-submit');
const replyInfo = document.getElementById('reply-info');
const replyUsername = document.getElementById('reply-username');
const replyToId = document.getElementById('reply-to-id');
const cancelReply = document.getElementById('cancel-reply');

// Определяем тип чата из URL
function getChatType() {
    const path = window.location.pathname;
    if (path.includes('/groups/')) return 'group';
    if (path.includes('/chats/')) return 'chat';
    return null;
}

// Инициализация чата
document.addEventListener('DOMContentLoaded', function() {
    scrollToBottom();
    setupEventListeners();
    connectWebSocket();
});

function scrollToBottom() {
    chatLog.scrollTop = chatLog.scrollHeight;
}

function setupEventListeners() {
    // Обработка клика на кнопку ответа
    chatLog.addEventListener('click', function(e) {
        const replyBtn = e.target.closest('.reply-btn');
        if (!replyBtn) return;
        
        replyToId.value = replyBtn.dataset.replyTo;
        replyUsername.textContent = replyBtn.dataset.username;
        replyInfo.style.display = 'block';
        messageInput.focus();
    });

    // Отмена ответа
    cancelReply.addEventListener('click', function() {
        replyToId.value = '';
        replyInfo.style.display = 'none';
    });

    // Отправка по Enter
    messageInput.addEventListener('keyup', function(e) {
        if (e.key === 'Enter') sendMessage();
    });

    // Отправка по клику
    submitButton.addEventListener('click', sendMessage);
}

function connectWebSocket() {
    const chatType = getChatType();
    if (!chatType) {
        console.error('Не удалось определить тип чата');
        return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const path = window.location.pathname;
    const uuid = path.split('/')[2]; // Получаем UUID из URL
    
    // Формируем путь в соответствии с вашими routing.py
    const wsPath = `${chatType}s/${uuid}/`;
    
    chatSocket = new WebSocket(`${protocol}${window.location.host}/ws/${wsPath}`);

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const messageElement = createMessageElement(data);
        
        messageElement.style.opacity = '0';
        chatLog.appendChild(messageElement);
        setTimeout(function() {
            messageElement.style.transition = 'opacity 0.3s ease';
            messageElement.style.opacity = '1';
        }, 10);
        
        scrollToBottom();
    };

    chatSocket.onclose = function(e) {
        console.log('WebSocket disconnected. Reconnecting...');
        setTimeout(connectWebSocket, 2000);
    };

    chatSocket.onerror = function(err) {
        console.error('WebSocket error:', err);
    };
}

function createMessageElement(data) {
    const element = document.createElement('div');
    
    if (data.event_type) {
        element.className = 'system-message';
        element.textContent = data.message;
        return element;
    }

    element.className = 'message';
    if (data.is_own) element.classList.add('own-message');
    element.dataset.messageId = data.id;

    const time = new Date(data.timestamp).toLocaleTimeString('ru-RU', {
        hour: '2-digit', 
        minute: '2-digit'
    });

    element.innerHTML = `
        <div class="message-user">
            <a href="${data.profile_url}">
                <img src="${data.avatar}" class="message-avatar" alt="${data.username}">
                <span class="message-author">${data.username}</span>
            </a>
        </div>
        <div class="message-content">
            ${data.reply_to ? `
            <div class="reply-preview">
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
        console.error("Не могу отправить сообщение - WebSocket не подключен");
    }
}
