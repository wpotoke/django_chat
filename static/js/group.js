let chatSocket = null;
const chatLog = document.getElementById('chat-log');
const messageInput = document.getElementById('chat-message-input');
const submitButton = document.getElementById('chat-message-submit');


function scrollToBottom() {
    const chatLog = document.getElementById('chat-log');
    chatLog.scrollTop = chatLog.scrollHeight;
}

// Вызовите при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    scrollToBottom();
});


function createMessageElement(data) {
    const element = document.createElement('div');
    
    if (data.status === 'Join' || data.status === 'Left') {
        element.className = 'system-message';
        const action = data.status === 'Join' ? 'присоединился' : 'покинул';
        element.textContent = `${data.username} ${action} чат`;
    } else {
        element.className = 'message';
        
        if (data.is_own) {
            element.classList.add('own-message');
        }

        const time = new Date(data.timestamp).toLocaleTimeString([], {
            hour: '2-digit', 
            minute: '2-digit'
        });

        // Создаем элементы вручную вместо innerHTML
        const messageUser = document.createElement('div');
        messageUser.className = 'message-user';
        
        const profileLink = document.createElement('a');
        profileLink.href = data.profile_url || '#';
        profileLink.className = 'profile-link';
        
        const avatarImg = document.createElement('img');
        avatarImg.src = data.avatar;
        avatarImg.className = 'message-avatar';
        avatarImg.alt = data.username;
        avatarImg.onerror = function() {
            this.src = '/static/images/default.png';
        };
        
        const authorSpan = document.createElement('span');
        authorSpan.className = 'message-author';
        authorSpan.textContent = data.username;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';
        messageBubble.textContent = data.message;
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        timeSpan.textContent = time;
        
        // Собираем структуру
        profileLink.appendChild(avatarImg);
        profileLink.appendChild(authorSpan);
        messageUser.appendChild(profileLink);
        
        messageContent.appendChild(messageBubble);
        messageContent.appendChild(timeSpan);
        
        element.appendChild(messageUser);
        element.appendChild(messageContent);
    }
    
    return element;
}

function connectWebSocket() {
    if (chatSocket) {
        chatSocket.onclose = null;
        chatSocket.close();
    }
    
    chatSocket = new WebSocket(`ws://${window.location.host}${window.location.pathname}`);
    
    chatSocket.onopen = function(e) {
        console.log("WebSocket connected");
    };

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const messageElement = createMessageElement(data);
        chatLog.appendChild(messageElement);
        scrollToBottom();
        
        if (data.status === 'Join') {
            handleUserJoin(data.username);
        } else if (data.status === 'Left') {
            handleUserLeave(data.username);
        }
    };

    chatSocket.onclose = function(e) {
        console.log("WebSocket disconnected. Reconnecting...");
        setTimeout(connectWebSocket, 2000);
    };

    chatSocket.onerror = function(error) {
        console.error("WebSocket error:", error);
    };
}

function handleUserJoin(user) {
    const membersList = document.getElementById('members');
    if (!membersList) return;
    
    const memberItem = document.createElement('li');
    memberItem.textContent = user;
    memberItem.id = `members-${user}`;
    membersList.appendChild(memberItem);
}

function handleUserLeave(user) {
    const element = document.getElementById(`members-${user}`);
    if (element) element.remove();
}

function scrollToBottom() {
    chatLog.scrollTop = chatLog.scrollHeight;
}

messageInput.focus();
messageInput.addEventListener('keyup', function(e) {
    if (e.key === 'Enter') sendMessage();
});

submitButton.addEventListener('click', sendMessage);

function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    if (chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            type: "text_message",
            message: message
        }));
        messageInput.value = '';
    } else {
        console.error("Cannot send message - WebSocket not connected");
    }
}

// Инициализация
connectWebSocket();