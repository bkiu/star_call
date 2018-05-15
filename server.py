from flask_security import auth_token_required
from flask import (
    abort,
    redirect,
    render_template,
    request,
    jsonify,
)
import random

from models import Planet, Player, Ship, Weapon
from auth import create_player_token, requires_auth, get_player
from serializer import serial_planet, serial_ship
from init import app, db, mygalaxy
from utils import create_ship

SHIP_TYPES = ['CORVETTE', 'DESTROYER', 'TITAN']

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["GET", "POST"])
def start():
    if request.method == "POST":
        player = create_player_token(request.form.get("username"))
        if player:
            # Choose a starting planet for the player
            for planet in mygalaxy.planets:
                planet = Planet.query.filter_by(id=planet).first_or_404()
                if planet.player == None:
                    myplanet = planet
                    myplanet.player = player
                    myplanet.player_id = player.id
                    db.session.commit()
                    break

            ship = create_ship(player, "CORVETTE", "Laser", myplanet)
    return render_template("start.html", player=player)


@app.route("/ship/<string:id>/", methods=["GET", "POST"])
@requires_auth
def ship(id):
    player = get_player()
    if request.method == "GET":
        ship = Ship.query.filter_by(id=id).first()
        if ship.player != player:
            coordinate = mygalaxy.get_ship_location(ship.id)
            location = mygalaxy.get_location(coordinate)
            for myship in location.get("ships", ""):
                myship = Ship.query.filter_by(id=myship).first()
                if myship.player == player:
                    return jsonify(serial_ship(ship))
            return "Nope", 403

    elif request.method == "POST":
        pass
    return jsonify(serial_ship(ship))


@app.route("/player/", methods=["GET", "POST"])
@requires_auth
def player():
    player = get_player()
    return jsonify({ "username": player.username, "star_tokens": player.star_tokens })



@app.route("/player/planets", methods=["GET", "POST"])
@requires_auth
def player_planets():
    player = get_player()
    planets = Planet.query.filter_by(player=player).all()
    player_planets = []
    for planet in planets:
        player_planets.append(serial_planet(planet))
    return jsonify(player_planets)


@app.route("/player/ships", methods=["GET", "POST"])
@requires_auth
def player_ships():
    player = get_player()
    ships = Ship.query.filter_by(player=player).all()
    player_ships = []
    for ship in ships:
        player_ships.append(serial_ship(ship))
    return jsonify(player_ships)


@app.route("/radar/<string:id>", methods=["GET", "POST"])
@requires_auth
def radar_ship(id):
    player = get_player()
    ship = Ship.query.filter_by(player=player, id=id).first()

    useful_locations = []
    ship_locations = {}
    map = []
    coordinate = mygalaxy.get_ship_location(ship.id)
    ship_locations[ship.id] = ship
    map.extend(mygalaxy.get_coordinate_radius(coordinate, 2))

    for item in set(map):
        location = mygalaxy.get_location(item)
        if location:
            location["location"] = item
            for count, ship in enumerate(location.get("ships", "")):
                ship = Ship.query.filter_by(id=ship).first()
                location["ships"][count] = { "ship": ship.id, "ship name": ship.name, "owner": ship.player.username  }
            if location.get("planet", ""):
                planet = location["planet"]
                planet = Planet.query.filter_by(id=planet).first()
                location["planet"] = { "planet": planet.id, "planet name": planet.name }
                if planet.player:
                    location["planet"]["owner"] = planet.player.username
            useful_locations.append(location)
    return jsonify(useful_locations)


@app.route("/radar", methods=["GET", "POST"])
@requires_auth
def radar():
    player = get_player()
    ships = Ship.query.filter_by(player=player).all()
    planets = Planet.query.filter_by(player=player).all()
    map = []
    useful_locations = []
    ship_locations = {}
    planet_locations = {}

    for ship in ships:
        coordinate = mygalaxy.get_ship_location(ship.id)
        ship_locations[ship.id] = ship
        map.extend(mygalaxy.get_coordinate_radius(coordinate, 2))
    for planet in planets:
        coordinate = mygalaxy.get_planet_location(planet.id)
        planet_locations[planet.id] = planet
        map.extend(mygalaxy.get_coordinate_radius(coordinate, 3))

    for item in set(map):
        location = mygalaxy.get_location(item)
        if location:
            location["location"] = item
            for count, ship in enumerate(location.get("ships", "")):
                ship = Ship.query.filter_by(id=ship).first()
                location["ships"][count] = { "ship": ship.id, "ship name": ship.name, "owner": ship.player.username  }
            if location.get("planet", ""):
                planet = location["planet"]
                planet = Planet.query.filter_by(id=planet).first()
                location["planet"] = { "planet": planet.id, "planet name": planet.name }
                if planet.player:
                    location["planet"]["owner"] = planet.player.username
            useful_locations.append(location)
    return jsonify(useful_locations)


@app.route("/ship/<string:id>/move", methods=["GET", "POST"])
@requires_auth
def move_ship(id):
    if request.method == "POST":
        player = get_player()
        ship = Ship.query.filter_by(player=player, id=id).first()
        if ship.player == player:
            dest = request.get_json().get("dest", "")
            if not dest:
                return jsonify({ "status": "Failed", "message": "dest is required" })
            mygalaxy.start_ship_journey(ship.id, dest)
            return jsonify({ "status": "Successful", "destion": dest, "ship": ship.id })
    return jsonify({ "status": "Failure" })


@app.route("/ship/<string:id>/capture", methods=["GET", "POST"])
@requires_auth
def capture_planet(id):
    if request.method == "POST":
        player = get_player()
        ship = Ship.query.filter_by(player=player, id=id).first()
        if ship.player == player:
            planet = request.get_json().get("planet", "")
            planet = Planet.query.filter_by(id=planet).first()

            ship_loc = mygalaxy.get_ship_location(ship.id)
            planet_loc = mygalaxy.get_planet_location(planet.id)
            if ship_loc != planet_loc:
                return "Your not allowed", 403

            mygalaxy.execute_on_delay("capture", [player.id, planet.id], 15, "Capture planet {}".format(planet.name))
    return jsonify(serial_planet(planet))



@app.route("/ship/<string:id>/fire", methods=["GET", "POST"])
@requires_auth
def fire(id):
    player = get_player()
    ship = Ship.query.filter_by(player=player, id=id).first()
    if request.method == "POST":
        target = request.get_json().get("target", "")
        mygalaxy.fire_round(ship.id, target)
        return jsonify({"result": "Success" })

    return "Cannot complete action", 400


@app.route("/planet/<string:id>", methods=["GET", "POST"])
@requires_auth
def planet(id):
    player = get_player()
    planet = Planet.query.filter_by(id=id).first()
    if planet.player == player:
        return jsonify(serial_planet(planet))

    coordinate = mygalaxy.get_planet_location(planet.id)
    location = mygalaxy.get_location(coordinate)
    for ship in location.get("ships", ""):
        ship_obj = Ship.query.filter_by(player=player, id=ship).first()
        if ship_obj:
            return jsonify(serial_planet(planet))
    return "You need a ship to see that", 424


@app.route("/planet/<string:id>/build", methods=["GET", "POST"])
@requires_auth
def ship_build(id):
    player = get_player()
    planet = Planet.query.filter_by(id=id).first()
    if request.method == "POST":
        if planet.player == player:
            ship_type= request.get_json()
            weapon = ship_type.get("weapon", "")

            type = ship_type.get("class", "")
            if weapon and type.upper() in SHIP_TYPES:
                ship = create_ship(player, type, weapon, planet, cost=True)
                return jsonify({ "status": "Building", "time": 30 })
    return "Cannot complete action", 400


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')

