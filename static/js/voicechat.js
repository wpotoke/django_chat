let peer = null;
let currentCall = null;
let localStream = null;
let callSocket = null;
let currentChatId = null;

// Инициализация звонков
function initCallSystem() {
    // Получаем ID текущего чата
    currentChatId = getChatId();
    if (!currentChatId) {
        console.error('Chat ID not found');
        return;
    }

    // Инициализируем PeerJS
    peer = new Peer({
        host: '0.peerjs.com',
        port: 443,
        path: '/',
        debug: 3
    });

    peer.on('open', (id) => {
        console.log('My Peer ID:', id);
        connectCallSocket(id);
    });

    peer.on('error', (err) => {
        console.error('PeerJS error:', err);
    });

    // Обработка входящих звонков
    peer.on('call', async (call) => {
        try {
            showCallModal();
            
            document.getElementById('accept-call').onclick = async () => {
                try {
                    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                    currentCall = call;
                    call.answer(localStream);
                    
                    call.on('stream', (remoteStream) => {
                        startCallUI(remoteStream);
                    });
                    
                    call.on('close', endCall);
                    call.on('error', (err) => {
                        console.error('Call error:', err);
                        endCall();
                    });
                    
                    hideCallModal();
                } catch (err) {
                    console.error('Ошибка доступа к медиаустройствам:', err);
                    hideCallModal();
                }
            };
            
            document.getElementById('reject-call').onclick = () => {
                call.close();
                hideCallModal();
            };
        } catch (err) {
            console.error('Error handling incoming call:', err);
            hideCallModal();
        }
    });

    // Обработчики для кнопки звонка в панели управления
    document.getElementById('start-call')?.addEventListener('click', startGroupCall);
    
    // Обработчики для кнопок звонка рядом с пользователями
    document.querySelectorAll('.call-member-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const userId = e.currentTarget.getAttribute('data-user-id');
            startPrivateCall(userId);
        });
    });
    
    // Завершение звонка
    document.getElementById('end-call')?.addEventListener('click', endCall);
}

// Подключение к CallConsumer WebSocket
function connectCallSocket(peerId) {
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const path = window.location.pathname;
    const uuid = path.split('/')[2];
    
    callSocket = new WebSocket(`${protocol}${window.location.host}/ws/call/${uuid}/`);

    callSocket.onopen = () => {
        console.log('Call WebSocket connected');
        // Отправляем наш peer ID на сервер
        callSocket.send(JSON.stringify({
            type: 'register',
            peer_id: peerId
        }));
    };

    callSocket.onmessage = (e) => {
        try {
            const data = JSON.parse(e.data);
            switch(data.type) {
                case 'peer_id':
                    // Получили peer ID собеседника
                    if (data.peer_id && currentCall === null) {
                        startPeerCall(data.peer_id);
                    }
                    break;
                case 'call_request':
                    // Входящий звонок (можно добавить уведомление)
                    break;
                default:
                    console.log('Unknown call message:', data);
            }
        } catch (err) {
            console.error('Error parsing call message:', err);
        }
    };

    callSocket.onclose = () => {
        console.log('Call WebSocket disconnected');
    };
}

// Начать групповой звонок
async function startGroupCall() {
    try {
        // Здесь нужно реализовать логику группового звонка
        console.log('Starting group call...');
        // Пока просто запрашиваем медиаустройства
        localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        // Показать локальное видео
        const localVideo = document.getElementById('local-video');
        if (localVideo) localVideo.srcObject = localStream;
    } catch (err) {
        console.error('Ошибка при начале группового звонка:', err);
    }
}

// Начать приватный звонок
async function startPrivateCall(userId) {
    try {
        // Получаем peer ID собеседника через API
        const response = await fetch(`/api/get_peer_id/${currentChatId}/${userId}/`);
        const data = await response.json();
        
        if (data.peer_id) {
            await startPeerCall(data.peer_id);
        } else {
            alert('Пользователь недоступен для звонка');
        }
    } catch (err) {
        console.error('Ошибка при начале приватного звонка:', err);
    }
}

// Начать звонок через PeerJS
async function startPeerCall(remotePeerId) {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        currentCall = peer.call(remotePeerId, localStream);
        
        currentCall.on('stream', (remoteStream) => {
            startCallUI(remoteStream);
        });
        
        currentCall.on('close', endCall);
        currentCall.on('error', (err) => {
            console.error('Call error:', err);
            endCall();
        });
        
    } catch (err) {
        console.error('Ошибка при начале звонка:', err);
        endCall();
    }
}

// Завершить звонок
function endCall() {
    if (currentCall) {
        currentCall.close();
        currentCall = null;
    }
    
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
        localStream = null;
    }
    
    stopCallUI();
}

// UI для звонка
function startCallUI(remoteStream) {
    document.getElementById('start-call')?.style.display = 'none';
    document.getElementById('end-call')?.style.display = 'inline-block';
    
    const videoContainer = document.getElementById('video-call-container');
    if (videoContainer) videoContainer.style.display = 'block';
    
    const remoteVideo = document.getElementById('remote-video');
    const localVideo = document.getElementById('local-video');
    
    if (remoteVideo) remoteVideo.srcObject = remoteStream;
    if (localVideo && localStream) localVideo.srcObject = localStream;
}

function stopCallUI() {
    document.getElementById('start-call')?.style.display = 'inline-block';
    document.getElementById('end-call')?.style.display = 'none';
    
    const videoContainer = document.getElementById('video-call-container');
    if (videoContainer) videoContainer.style.display = 'none';
    
    const remoteVideo = document.getElementById('remote-video');
    const localVideo = document.getElementById('local-video');
    
    if (remoteVideo) remoteVideo.srcObject = null;
    if (localVideo) localVideo.srcObject = null;
}

function showCallModal() {
    const modal = document.getElementById('call-modal');
    if (modal) modal.style.display = 'flex';
}

function hideCallModal() {
    const modal = document.getElementById('call-modal');
    if (modal) modal.style.display = 'none';
}

// Получение ID текущего чата
function getChatId() {
    const path = window.location.pathname.split('/');
    return path.length > 2 ? path[2] : null;
}

// ========== Инициализация всего ==========
document.addEventListener('DOMContentLoaded', function() {
    initCallSystem();
});