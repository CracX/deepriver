// CONSTANTS
const listServer = $("#cb-server")
const chatLog = $("#cb-chat")
const chatInput = $("#i-chat-message")
const chatBtnSend = $("#btn-send")
const serverTitle = $("#cbs-root")
const serverList = $("#cbs-list")

// ENUMS

const MessageType = {
    SERVER: 0,
    USER: 1,
    CLIENT: 2
}

const ServerMessageType = {
    DEFAULT: 0,
    SUCCESS: 1,
    WARNING: 2
}

// FUCNTIONS

const postServerMessage = (type, message) =>{
    let messageType = type
    let serverMessageClass = messageType == ServerMessageType.DEFAULT ? "" : messageType == ServerMessageType.SUCCESS ? "success" : "warning"
    chatLog.append(`
        <p class="msg-server ${serverMessageClass}">[SERVER]: ${message}</p>
    `)
}

const postChatMessage = (user, message) =>{
    chatLog.append(`
        <p class="msg-user"><span>${user}:</span> ${message}</p>
    `)
}

const postClientMessage = (message) =>{
    $(chatLog).append(`
        <p class="msg-client">${message}</p>
    `)
}

// SOCKETS & EVENTS

const socket = io();

socket.on('msg_receive', (data) => {

    switch(data.type){
        case MessageType.CLIENT:
            postClientMessage(data.message)
            break
        case MessageType.SERVER:
            postServerMessage(data.message_type, data.message)
            break
        case MessageType.USER:
            postChatMessage(data.user, data.message)
            break
        default:
            break
    }
})

socket.on('update_server_data', (data) =>{
    console.log(data)
    serverTitle.text("/"+data.room_name)
    serverList.html('')

    data.users.forEach(user => {
        serverList.append(`
        <li class="cbs-user" data-type="user">
        <img src="/static/icons/user.png">
        ${user}
        </li>
        `)
    });

    data.servers.forEach(server => {
        serverList.append(`
        <li class="cbs-server" data-type="server${server.locked ? '-locked' : ''}">
        <img src="/static/icons/server${server.locked ? '_locked' : ''}.png">
        ${server.name}
        </li>
        `)
    });
})

$('.cbs-server').on('click', (data)=>{
    if ($(data.currentTarget).data('type') == "server"){
        chatInput.val(`/room join${$(data.currentTarget).text()}`)
        chatBtnSend.trigger('click')
        return
    }else{
        chatInput.val(`/room join${$(data.currentTarget).text()} <password>`)
        chatInput.focus()
    }
})

chatBtnSend.click(()=>{
    const message = chatInput.val()
    chatInput.val('')

    if (message == "" || message == null){
        return
    }

    if (message == "/clear"){
        chatLog.html('')
        return
    }

    socket.emit('msg_send', message)
})

$(chatInput).on('keypress', function (e) {
    if(e.which === 13){
        chatBtnSend.trigger("click")
    }
});