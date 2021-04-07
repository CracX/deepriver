from logging import debug
from flask import Flask, render_template, redirect, url_for
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os
load_dotenv()



app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
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

#####################
#                   #
#      SOCKETS      #
#                   #
#####################



if __name__ == '__main__':
    sio.run(app, debug=True)