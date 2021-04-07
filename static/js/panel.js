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

// SOCKET EVENTS

const socket = io();

socket.on('connect', () => {
    socket.emit('motd', null)
})

socket.on('msg_receive', (data) => {
    console.log(data)
})