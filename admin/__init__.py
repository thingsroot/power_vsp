from flask import Flask
from flask_cors import *

app = Flask(__name__)
CORS(app, supports_credentials=True)

def start_admin(vspc_manager, vspc_service):
    app.vspc_manager = vspc_manager
    app.vspc_service = vspc_service
    app.run(host="127.0.0.1", port=5080)


import admin.views