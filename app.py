from flask import Flask, render_template, redirect, url_for, session
from flask.globals import request
from flask.json import jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from dotenv import load_dotenv
import os
from enum import Enum
import datetime
import re
from random import randint
from argon2 import PasswordHasher
from jinja2.utils import escape

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
sio = SocketIO(app)

ROOMS = {}

#####################
#                   #
#  ENUMS & CLASSES  #
#                   #
#####################

class MessageType(Enum):
    SERVER = 0
    USER = 1
    CLIENT = 2

class ServerMessageType(Enum):
    DEFAULT = 0
    SUCCESS = 1
    WARNING = 2


class UserMessage:
    def __init__(self, user, message) -> None:
        self._type = MessageType.USER.value
        self._user = user
        self._message = escape(message)
        self._timestamp = datetime.datetime.timestamp(datetime.datetime.now())
    
    def get(self):
        return {
            'type': self._type,
            'user': self._user,
            'message': self._message,
            'timestamp': self._timestamp
        }

class ServerMessage:
    def __init__(self, message, type=ServerMessageType.DEFAULT) -> None:
        self._type = MessageType.SERVER.value
        self._message_type = type.value
        self._message = message
        self._timestamp = datetime.datetime.timestamp(datetime.datetime.now())
    
    def get(self):
        return {
            'type': self._type,
            'message_type': self._message_type,
            'message': self._message,
            'timestamp': self._timestamp
        }

class ClientMessage:
    def __init__(self, message) -> None:
        self._type = MessageType.CLIENT.value
        self._message = message
        self._timestamp = datetime.datetime.timestamp(datetime.datetime.now())
    
    def get(self):
        return {
            'type': self._type,
            'message': self._message,
            'timestamp': self._timestamp
        }



#####################
#                   #
#      ROUTES       #
#                   #
#####################

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/panel')
def panel():
    if not 'uid' in session:
        return redirect(url_for("index"))
    return render_template("panel.html", user=session['uid'])

@app.route('/api/login', methods=['POST'])
def login():
    session.clear()
    fields = ['username']

    if not request.is_json:
        return jsonify({'success': False, 'message': "Request needs to be in a json format"}), 404

    data = request.get_json()

    for field in fields:
        if field not in data:
            return jsonify({'success': False, 'message': f"Missing field '{field}'"}), 404
    
    username = data['username']
    username_check = username and len(username) >= 3 and len(username) <= 15 and re.match(r'[a-zA-Z0-9\-\_]', username)

    if not username_check:
        return jsonify({'success': False, 'message': "Invalid username. Please, only use symbols 'a-z A-Z 0-9 - _' and no longer than 15 characters, no shorter than 3"}), 404

    username += "#"+str(randint(1111, 9999))

    session['uid'] = username
    session['roomid'] = None
    
    return jsonify({'success': True, 'message': f"Logged in as {username}"})
            

#####################
#                   #
#      SOCKETS      #
#                   #
#####################

@sio.on('connect')
def test_connect():
    emit('msg_receive', ClientMessage("Welcome to the deepriver platform!").get())
    public_rooms = []
    for room_name, room_content in ROOMS.items():
        if ROOMS[room_name]['config']['public'] == True:
            public_rooms.append({'name': room_name, 'locked': False if room_content['password'] == None else True})
    emit('update_server_data', {'room_name': 'root', 'users': [], 'servers': public_rooms})
    return

@sio.on('disconnect')
def test_disconnect():
    if session['roomid'] == None:
        return
    
    ROOMS[session['roomid']]['users'].remove(session['uid'])
    leave_room(session['roomid'])

    if len(ROOMS[session['roomid']]['users']) == 0:
        del(ROOMS[session['roomid']])
    else:
        emit('msg_receive', ServerMessage(f"User {session['uid']} left the room.").get(), room=session['roomid'])
    session['roomid'] = None
    return
    

@sio.on('msg_send')
def socket_msg_send(message):
    if not message or len(message) < 1:
        return
    if not message[0] == '/':
        if session['roomid'] == None:
            emit('msg_receive', ClientMessage("You are not connected to any room!").get())
            return
        emit('msg_receive', UserMessage(session['uid'], message).get(), room=session['roomid'])
        return
    
    if re.match(r'^/room create [a-zA-Z0-9\-\_]', message):
        splitted = message.split(' ')
        room_name = splitted[2]
        if len(splitted) == 4:
            room_password = PasswordHasher().hash(splitted[3])
        else:
            room_password = None

        if room_name in ROOMS:
            emit('msg_receive', ClientMessage("Room with such name already exists!").get())
            return
        
        if not session['roomid'] == None:
            emit('msg_receive', ClientMessage("You are already in a room!").get())
            return
        
        ROOMS.update({
            room_name: {'password': room_password, 'users': [session['uid']], 'config':{
                'public': False
            }}
        })
        session['roomid'] = room_name

        join_room(room_name)
        emit('update_server_data', {'room_name': room_name, 'users': ROOMS[room_name]['users'], 'servers': []})
        emit('msg_receive', ServerMessage(f"User {session['uid']} joined the room.").get(), room=room_name)
        return
    
    if re.match(r'^/room join [a-zA-Z0-9\-\_]', message):
        splitted = message.split(' ')
        room_name = splitted[2]
        if len(splitted) == 4:
            room_password = splitted[3]
        else:
            room_password = None

        if not room_name in ROOMS:
            emit('msg_receive', ClientMessage("Room with this name does not exist!").get())
            return
        
        if session['uid'] in ROOMS[room_name]['users']:
            emit('msg_receive', ClientMessage("You are connected to this room!").get())
            return
        
        if not session['roomid'] == None:
            emit('msg_receive', ClientMessage("You are already in a room!").get())
            return

        if not ROOMS[room_name]['password'] == None and room_password == None:
            emit('msg_receive', ClientMessage("This room requires a password!").get())
            return
        
        if not ROOMS[room_name]['password'] == None:
            try:
                PasswordHasher().verify(ROOMS[room_name]['password'], room_password)
            except:
                emit('msg_receive', ClientMessage("Invalid password!").get())
                return

        ROOMS[room_name]['users'].append(session['uid'])
        join_room(room_name)
        session['roomid'] = room_name
        emit('msg_receive', ServerMessage(f"User {session['uid']} joined the room.").get(), room=room_name)
        emit('update_server_data', {'room_name': room_name, 'users': ROOMS[room_name]['users'], 'servers': []}, room=room_name)
        return

    if re.match(r'^/room leave', message):
        if session['roomid'] == None:
            emit('msg_receive', ClientMessage("You are not connected to any room!").get())
            return
        
        ROOMS[session['roomid']]['users'].remove(session['uid'])
        
        
        leave_room(session['roomid'])
        emit('msg_receive', ClientMessage("Disconnected.").get())

        if len(ROOMS[session['roomid']]['users']) == 0:
            del(ROOMS[session['roomid']])
        else:
            emit('update_server_data', {'room_name': session['roomid'], 'users': ROOMS[session['roomid']]['users'], 'servers': []}, room=session['roomid'])
            emit('msg_receive', ServerMessage(f"User {session['uid']} left the room.").get(), room=session['roomid'])
        session['roomid'] = None

        public_rooms = []
        for room_name, room_content in ROOMS.items():
            if ROOMS[room_name]['config']['public'] == True:
                public_rooms.append({'name': room_name, 'locked': False if room_content['password'] == None else True})
        emit('update_server_data', {'room_name': 'root', 'users': [], 'servers': public_rooms})
        return

    if re.match(r'^/public', message):
        if session['roomid'] == None:
            emit('msg_receive', ClientMessage("You are not connected to any room!").get())
            return
        
        ROOMS[session['roomid']]['config']['public'] = not ROOMS[session['roomid']]['config']['public']
        emit('msg_receive', ServerMessage(f"Public mode set to {ROOMS[session['roomid']]['config']['public']} by {session['uid']}", ServerMessageType.WARNING).get(), room=session['roomid'])
        return

    emit('msg_receive', ClientMessage(f"Invalid command: {message}").get())
    

    

if __name__ == '__main__':
    sio.run(app, debug=True)