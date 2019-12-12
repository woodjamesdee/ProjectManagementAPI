from flask import Flask, render_template, request
from flask_restful import Resource, Api, reqparse
import pyrebase

# Initialize Flask and the API
app = Flask(__name__)
api = Api(app)

@app.route("/")
def index():
    return "Hello World!"

if __name__ == "__main__":
    app.run()