base_url = `${window.location.host}${window.location.pathname}`
const chatSocket = new WebSocket(`ws://${base_url}`);
chatSocket.onopen = function (e) {
    console.log("conneсted")
}
chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    console.log(data)
    document.querySelector('#chat-log').value += (data.message + '\n');
    const status = data.status
    user = data.user
    if (status == "Left") {
        document.getElementById(`members-${user}`).remove()
    } else if (status == "Join") {
        var members_list = document.getElementById('members')
        var members_item = document.createElement("li")
        members_item.innerHTML = user
        members_item.setAttribute("id", `members-${user}`)
        console.log(members_item)
        members_list.appendChild(members_item)
    }
    scrollToBottom();
};
chatSocket.onclose = function (e) {
    console.error('Chat socket closed unexpectedly');
    console.log('Socket closed. Reconnecting...');
    setTimeout(() => {
        connectWebSocket();  // Переподключение через 2 сек
    }, 2000);
};
document.querySelector('#chat-message-input').focus();
document.querySelector('#chat-message-input').onkeyup = function (e) {
    if (e.keyCode === 13) {  // enter, return
        document.querySelector('#chat-message-submit').click();
    }
};
document.querySelector('#chat-message-submit').onclick = function (e) {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    chatSocket.send(JSON.stringify({
        'type': "text_message",
        'author': '{request}',
        'message': message
    }));
    messageInputDom.value = '';
};
