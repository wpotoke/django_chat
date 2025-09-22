const base_url = `${window.location.hostname}:${window.location.port}`;
const websocket = new WebSocket(`ws://${base_url}/ws/chat_list/`);

function add_event_to_all_buttons() {
    const buttons = document.querySelectorAll('.group_option');
    buttons.forEach(button => {
        button.addEventListener('click', send_event_message);
    });
}

function send_event_message(event) {
    const { target } = event;
    const [action, group_uuid] = target.value.split(" ");
    
    if (action === "open_group") {
        window.location.href = `http://${base_url}/groups/${group_uuid}/`;
    } else {
        const data = {
            "type": action,
            "data": group_uuid,
        };
        websocket.send(JSON.stringify(data));
    }
}

function leave_group_handler(uuid) {
    const actionsDiv = document.getElementById(`actions-${uuid}`);
    actionsDiv.innerHTML = `
        <button class="chat-option chat-join group_option" value="join_group ${uuid}">
            Join
        </button>
    `;
    add_event_to_all_buttons();
}

function join_group_handler(uuid) {
    const actionsDiv = document.getElementById(`actions-${uuid}`);
    actionsDiv.innerHTML = `
        <button class="chat-option chat-leave group_option" value="leave_group ${uuid}">
            Leave
        </button>
        <a href="/groups/${uuid}/" class="chat-option chat-open">
            Open
        </a>
    `;
    add_event_to_all_buttons();
}

websocket.onopen = function(event) {
    console.log("WebSocket connection established");
    add_event_to_all_buttons();
};

websocket.onmessage = function(event) {
    const message = JSON.parse(event.data);
    const { type, data } = message;
    
    switch (type) {
        case "leave_group":
            leave_group_handler(data);
            break;
        case "join_group":
            join_group_handler(data);
            break;
    }
};

websocket.onerror = function(error) {
    console.error("WebSocket error:", error);
};

websocket.onclose = function(event) {
    console.log("WebSocket connection closed");
};

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', function() {
    add_event_to_all_buttons();
});