from logging import debug
from flask import Flask, render_template, redirect, url_for
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = "asdj9a09skd9s09dja0sojda0ps9dja9sdoa"
sio = SocketIO(app)

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
    return render_template("panel.html")


if __name__ == '__main__':
    sio.run(app, debug=True)