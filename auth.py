import redis
import random
from models import Player
from functools import wraps
from flask import request
from models import db

def create_player_token(username):
    player = Player(username)
    db.session.add(player)
    db.session.commit()
    return player


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        print(auth)
        if auth and check_auth(auth):
            return f(*args, **kwargs)
        else:
            return "No", 403
        return f(*args, **kwargs)
    return decorated


def check_auth(token):
    username = token.get("username", "")
    password = token.get("password", "")
    player = Player.query.filter_by(username=username, token=password).first_or_404()
    if player:
        return True
    else:
        return False


def get_player():
    username = request.authorization.get("username", "")
    password = request.authorization.get("password", "")
    player = Player.query.filter_by(username=username, token=password).first_or_404()
    return player
