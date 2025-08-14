// Определение типа чата
export function getChatType() {
    const path = window.location.pathname;
    if (path.includes('/groups/')) return 'group';
    if (path.includes('/chats/')) return 'chat';
    return null;
}

// Получение UUID чата из URL
export function getChatUuid() {
    return window.location.pathname.split('/')[2];
}

// Прокрутка чата вниз
export function scrollToBottom(element) {
    if (element) element.scrollTop = element.scrollHeight;
}