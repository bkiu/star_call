import uuid

from flask_sqlalchemy import SQLAlchemy
from naming import get_random_ship_name

db = SQLAlchemy()


class Planet(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.String(200))

    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player = db.relationship('Player', backref=db.backref('player', lazy=True))
    resources = db.Column(db.Integer)

    def __init__(self, name, resources, x=0, y=0, z=0):
        self.name = name
        self.resources = resources


class Player(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)

    username = db.Column(db.String(50), nullable=False)
    star_tokens = db.Column(db.Integer)
    token = db.Column(db.String(50), nullable=False)

    def __init__(self, username, star_tokens=5000, token=uuid.uuid4()):
        self.username = username
        self.star_tokens = star_tokens
        self.token=token


class Ship(db.Model):
    CORVETTE, DESTROYER, TITAN = 'CORVETTE', 'DESTROYER', 'TITAN'

    HEALTH = {CORVETTE: 500, DESTROYER: 750, TITAN: 1000}
    SHIELD = {CORVETTE: 500, DESTROYER: 750, TITAN: 1000}
    TURRETS = {CORVETTE: 5, DESTROYER: 9, TITAN: 15}
    AMMO = {CORVETTE: 2000, DESTROYER: 5000, TITAN: 10000}
    COST = {CORVETTE: 5000, DESTROYER: 10000, TITAN: 15000}
    BUILD_TIMES = {CORVETTE: 50, DESTROYER: 100, TITAN: 200}

    id = db.Column(db.Integer, unique=True, primary_key=True)

    name = db.Column(db.String(50))
    type = db.Column(db.String(50))
    size = db.Column(db.Integer)
    cost = db.Column(db.Integer)
    ammo = db.Column(db.Integer)

    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player = db.relationship('Player', backref=db.backref('ships', lazy=True))

    weapon_id = db.Column(db.Integer, db.ForeignKey('weapon.id'))
    weapon = db.relationship('Weapon', backref=db.backref('ships', lazy=True))

    shield = db.Column(db.Integer)
    health = db.Column(db.Integer)
    speed = db.Column(db.Integer)
    build_time = db.Column(db.Integer)

    def __init__(self, player, type, weapon):
        self.shield = self.SHIELD[type]
        self.health = self.HEALTH[type]
        self.ammo = self.AMMO[type]
        self.cost = self.COST[type]
        self.name = get_random_ship_name()
        self.type = type
        self.player = player
        self.player_id = player.id
        self.weapon = weapon
        self.weapon_id = weapon.id
        self.build_time = self.BUILD_TIMES[type]
        self.speed = 1

    def fire_weapons(self):
        used_ammo = self.weapon.ammo * self.TURRETS[self.type]
        self.ammo -= used_ammo

    def get_damage_dealt(self):
        accuracy_percent = self.weapon.accuracy / 100
        potential_damage = self.weapon.damage * self.TURRETS[self.type]
        return int(potential_damage * accuracy_percent)

    def reset_ammo(self):
        cost = self.AMMO[self.type] - self.ammo
        self.player.star_tokens -= cost
        self.ammo = self.AMMO[self.type]

    def reset_shields(self):
        self.shield = self.SHIELD[self.type]


class Weapon(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)

    name = db.Column(db.String(50), unique=True)
    cost = db.Column(db.Integer)
    ammo = db.Column(db.Integer)
    damage = db.Column(db.Integer)
    accuracy = db.Column(db.Integer)
    speed = db.Column(db.Integer)
    range = db.Column(db.Integer)

    def __init__(self, name, cost, ammo, damage, accuracy, speed, range):
        self.name = name
        self.cost = cost
        self.ammo = ammo
        self.damage = damage
        self.accuracy = accuracy
        self.speed = speed
        self.range = range
