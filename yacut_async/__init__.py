from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from settings import Config

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from . import api_views, error_handlers, views
