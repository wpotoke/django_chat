base_url = `${window.location.hostname}:${window.location.port}`
const websocket = new WebSocket(`ws://${base_url}`)
function add_event_to_all_buttons() {
    /*Добавим прослушиватель событий, который отправляет сообщение о событии на все кнопки*/
    const keys = document.querySelectorAll('.group_option');
    keys.forEach(item => {
            item.addEventListener('click', send_event_message)
        }
    )
}

function send_event_message(event) {
    /*Отправим uuid и значение кнопки, которая была нажата*/
    const {target} = event;
    group = target.value.split(" ")
    group_uuid = group[1]
    action = group[0] //Leave or Join or Open
    if (action == "open_group") {
        window.location.replace(`http://${base_url}/groups/${group_uuid}/`)
    } else {
        let data = {
            "type": action,
            "data": group_uuid,
        }
        websocket.send(JSON.stringify(data))
    }
}

add_event_to_all_buttons()
websocket.onopen = function (event) {
    console.log("Connection Open")
}

websocket.onmessage = function (event) {
    /*Вызывается, когда сервер веб-сокета отправляет сообщение клиентскому веб-сокету*/
    message = JSON.parse(event.data)
    let type = message.type
    let data = message.data
    switch (type) {
        case "leave_group":
            leave_group_handler(data)
            break;
        case "join_group":
            join_group_handler(data)
            break;
    }
}

function leave_group_handler(uuid) {
    /*Удалит кнопки "Покинуть" и "Открыть" и создаст новую кнопку "Присоединиться"*/
    var leave_button = document.getElementById(`leave-${uuid}`)
    var open_button = document.getElementById(`open-${uuid}`)
    leave_button.remove()
    open_button.remove()
    var button = `<button id="join-${uuid}" class="group_option" value="join_group ${uuid}">Join</button>`
    var dev_body = document.getElementById(uuid)
    dev_body.innerHTML += button
    add_event_to_all_buttons()
}

function join_group_handler(uuid) {
    /*Удалит кнопку "Присоединиться" и добавит кнопку "Уйти" и "Открыть"*/
    var leave_button = document.getElementById(`join-${uuid}`)
    leave_button.remove()
    var button = `<button id="leave-${uuid}" class="group_option" value="leave_group ${uuid}">Leave</button>`
    var open_button = `<button id="open-${uuid}" class="group_option" value="open_group ${uuid}">Open</button>`
    var dev_body = document.getElementById(uuid)
    dev_body.innerHTML += button
    dev_body.innerHTML += open_button
    add_event_to_all_buttons()
}