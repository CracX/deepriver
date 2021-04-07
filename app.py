from flask import Flask, render_template, redirect, url_for, session
from flask.globals import request
from flask.json import jsonify
from flask_socketio import SocketIO, join_room, leave_room, namespace, send, emit
from dotenv import load_dotenv
import os
from enum import Enum
import datetime
import hashlib
import re
from random import randint

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
sio = SocketIO(app)

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
        self._message = message
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
    return render_template("panel.html")

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
    
    return jsonify({'success': True, 'message': f"Logged in as {username}"})
            

#####################
#                   #
#      SOCKETS      #
#                   #
#####################

@sio.on('connect')
def test_connect():
    emit('msg_receive', ClientMessage("Welcome to the DeepRiver chat service!").get(), namespace='/panel')
    print(f"User {str(hashlib.md5(session['uid'].encode()).hexdigest())[0:10]} connected to the main lobby")

@sio.on('disconnect')
def test_disconnect():
    print(f"User {str(hashlib.md5(session['uid'].encode()).hexdigest())[0:10]} disconnected briefly, reconnecting...?")

@sio.on('motd')
def socket_motd(tmp):
    emit('msg_receive', ClientMessage("Welcome to the deepriver platform!").get())

if __name__ == '__main__':
    sio.run(app, debug=True)