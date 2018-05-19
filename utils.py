from models import db, Planet, Player, Ship, Weapon
from init import mygalaxy
from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

def create_ship(player, type, weapon, planet, cost=0):
    weapon = Weapon.query.filter_by(name=weapon).first_or_404()
    ship = Ship(player, type, weapon)
    if cost:
        if ship.cost < player.star_tokens:
            player.star_tokens -= ship.cost
            mygalaxy.execute_on_delay("create_ship", [ship.id, planet.id], 30, "Build ship")
        else:
            return "Not enough credits", 402
            del ship
    db.session.add(ship)
    db.session.commit()
    if cost:
        mygalaxy.execute_on_delay("create_ship", [ship.id, planet.id], 30, "Build ship")
    else:
        mygalaxy.add_ship(ship.id, mygalaxy.get_planet_location(planet.id))
    return ship


def crossdomain(origin=None, methods=None, headers=["Authorization", "Content-type"],
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator
