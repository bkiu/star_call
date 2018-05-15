from models import db
from universe import Galaxy
from flask import Flask
import uuid
import config
from redis import Redis

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
db.init_app(app)

redis_store = Redis()
mygalaxy = Galaxy(app, 'foo8')
