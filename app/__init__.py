from flask import Flask
from flask import session as server_session
from flask_restful import Api
from flask_session import Session
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
import pyrebase
import os


app = Flask(__name__)
api = Api(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
app.config.from_object(__name__)
try:
    with open("secret_key", "rb") as read_file:
        app.config["SECRET_KEY"] = read_file.read()
except:
    from gen_secret import generate_secret_key
    generate_secret_key()
    with open("secret_key", "rb") as read_file:
        app.config["SECRET_KEY"] = read_file.read()
app.config["SESSION_TYPE"] = "filesystem"

Session(app)
bootstrap = Bootstrap(app)

firebaseConfig = {
    "apiKey": "AIzaSyAOt2oJnOJHOLgyFHApNINzAqrtS2B0lcY",
    "authDomain": "projectmanagementapi.firebaseapp.com",
    "databaseURL": "https://projectmanagementapi.firebaseio.com",
    "projectId": "projectmanagementapi",
    "storageBucket": "projectmanagementapi.appspot.com",
    "messagingSenderId": "432840428373",
    "appId": "1:432840428373:web:d4aa71e700009b3bed3ddc",
    "measurementId": "G-FX9PKEDNE6"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

from app import routes