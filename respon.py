import os
from config import DevelopmentConfig, ProductionConfig
from dotenv import load_dotenv, find_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO, send, emit

app = Flask(__name__)
config = ProductionConfig() if os.environ.get('FLASK_ENV') == 'production' else DevelopmentConfig()
app.config.from_object(config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)

from app import route, models
from app.controller import logFile

if os.environ.get('FLASK_ENV') == 'production':
	logFile.rename()

route.initiateManifest()
route.initiateEkspor()

if __name__ == '__main__':
	socketio.run(app)