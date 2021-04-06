from logging import debug
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = "asdj9a09skd9s09dja0sojda0ps9dja9sdoa"
sio = SocketIO(app)

if __name__ == '__main__':
    sio.run(app, debug=True)