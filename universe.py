import json
import itertools
import random

from exceptions import *
from models import db, Planet, Player, Ship
from navigate import make_path_2d, distance_formula
from redis import Redis


class Galaxy:
    def __init__(self, app, key, size=100):
        self.app = app
        self.key = key
        self.size = size
        self.redis = Redis()
        self.nouns = []
        with open('nouns.txt', 'r') as fp:
            for line in fp:
                self.nouns.append(line.strip().title())

        self.suffixes = []
        with open('suffixes.txt', 'r') as fp:
            for line in fp:
                self.suffixes.append(line.strip().title())

        # Maps planet id to a dict with information about the planets
        # and ships has keys coords
        self.planets = {}

        self.planets_key = "star_call:{}:planets".format(self.key)
        planets_info = self.redis.get(self.planets_key)
        if planets_info:
            planets = json.loads(planets_info.decode('utf-8'))
            for p_id,p_info in planets.items():
                self.planets[int(p_id)] = p_info
        else:
            self.initialize_planets()

    def get_random_name(self):
        noun = random.choice(self.nouns)
        noun2 = random.choice(self.nouns)
        return "{} {}".format(noun, noun2)

    # Ratio is number of sectors per planet
    def initialize_planets(self, ratio=50):
        self.initialize_planets_2d(ratio)

    def initialize_planets_2d(self, ratio):
        num_planets = self.size**2 / ratio
        planet_locations = set([])
        planets = []

        while len(planets) < num_planets:
            coords = (random.randrange(0,self.size),
                      random.randrange(0,self.size))
            coords_str = "{},{}".format(*coords)
            if coords_str in planet_locations:
                continue

            planet = Planet(self.get_random_name(), random.randrange(10, 1000),
                            coords[0], coords[1])
            planets.append({ 'obj': planet, 'location': coords })

        with self.app.app_context():
            for planet in planets:
                db.session.add(planet['obj'])
            db.session.commit()

            for planet in planets:
                location_dict = {
                    'planet': planet['obj'].id,
                    'ships': [],
                }
                key = self._build_coordinate_key(planet['location'])
                self.redis.set(key, json.dumps(location_dict))
            self.planets = { p['obj'].id:{'location': p['location'] } for p in planets}
        self.redis.set(self.planets_key, json.dumps(self.planets))

    def _initialize_location(self, coords):
        key = self._build_coordinate_key(coords)
        blank = {
            'planet': '',
            'ships': []
        }
        self.redis.set(key, json.dumps(blank))

    def _build_coordinate_key(self, coords):
        return "star_call:{}:{}".format(self.key, ",".join([str(x) for x in coords]))

    def _build_ship_key(self, ship_id):
        return "star_call:{}:ship:{}".format(self.key, ship_id)

    def _build_travelling_ships_key(self):
        return "star_call:{}:travelling_ships".format(self.key)

    def _build_battle_rounds_key(self):
        return "star_call:{}:battle_rounds".format(self.key)

    def _build_execution_queue_key(self):
        return "star_call:{}:execution_queue".format(self.key)

    def get_location(self, coords, empty_ok=False):
        key = self._build_coordinate_key(coords)
        info = self.redis.get(key)
        if not info:
            return None

        info = json.loads(info.decode('utf-8'))
        if not info['planet'] and not info['ships'] and not empty_ok:
            return None

        return info

    def save_location(self, coords, info):
        key = self._build_coordinate_key(coords)
        self.redis.set(key, json.dumps(info))

    # Returns a list of tuples within the radius of the given coords
    def get_coordinate_radius(self, coords, radius):
        # This is a list of lists of all the coordinates we need to
        # check for this axis
        clist = []
        for c in coords:
            clist.append([c + x for x in range(-1*radius, radius+1)])

        return list(itertools.product(*clist))

    def save_ship_location(self, ship_id, coords):
        key = self._build_ship_key(ship_id)
        info = {
            'location': coords
        }
        self.redis.set(key, json.dumps(info))

    def add_ship(self, ship_id, coords):
        ship_id = int(ship_id)
        info = self.get_location(coords)
        if info and ship_id in info['ships']:
            return

        if not info:
            info = {
                'planet': '',
                'ships': [ship_id]
            }
        else:
            info['ships'].append(ship_id)

        self.save_location(coords, info)
        self.save_ship_location(ship_id, coords)

    def get_ship_location(self, ship_id):
        ship_id = int(ship_id)
        key = self._build_ship_key(ship_id)
        ship_info = self.redis.get(key)
        if not ship_info:
            raise ShipNotFoundError
        ship_info = json.loads(ship_info.decode('utf-8'))
        return ship_info['location']

    def get_planet_location(self, planet_id):
        planet_data = self.planets.get(planet_id)
        if not planet_data:
            raise PlanetNotFoundError

        print(planet_data['location'])
        return planet_data['location']

    def start_ship_journey(self, ship_id, dest):
        dest[0], dest[1] = int(dest[0]), int(dest[1])
        if dest[0] < 0 or dest[1] < 0 or dest[0] > self.size or dest[1] > self.size:
            raise EdgeOfTheUniverseError

        ship_id = int(ship_id)
        ships = self.get_travelling_ships()
        for s in ships:
            if s['ship_id'] == ship_id:
                return

        start = self.get_ship_location(ship_id)
        path = make_path_2d(start, dest)
        path.pop(0)

        ships.append({
            'ship_id': ship_id,
            'path': path
        })
        self.set_travelling_ships(ships)

    def get_travelling_ships(self):
        ships_key = self._build_travelling_ships_key()
        ships_info = self.redis.get(ships_key)
        if ships_info:
            return json.loads(ships_info.decode('utf-8'))
        return []

    def set_travelling_ships(self, traveling_ships):
        ships_key = self._build_travelling_ships_key()
        self.redis.set(ships_key, json.dumps(traveling_ships))

    def ship_travel_step(self):
        travelling_ships = self.get_travelling_ships()
        new_travelling_ships = []
        for t in travelling_ships:
            if not t['path']:
                continue

            next = t['path'].pop(0)
            print("Moving ship {} to".format(t['ship_id']), next)
            self.move_ship(t['ship_id'], next)
            if len(t['path']) == 0:
                continue

            new_travelling_ships.append(t)

        self.set_travelling_ships(new_travelling_ships)

    def move_ship(self, ship_id, dest):
        if dest[0] < 0 or dest[1] < 0 or dest[0] > self.size or dest[1] > self.size:
            raise EdgeOfTheUniverseError

        ship_id = int(ship_id)
        start_coords = self.get_ship_location(ship_id)
        if not start_coords:
            raise ShipNotFoundError

        # Updating the universe coordinate info
        start_info = self.get_location(start_coords)
        if ship_id in start_info['ships']:
            start_info['ships'].remove(ship_id)
            self.save_location(start_coords, start_info)

        dest_info = self.get_location(dest, empty_ok=True)
        if not dest_info:
            self._initialize_location(dest)
            dest_info = self.get_location(dest, empty_ok=True)

        if ship_id not in dest_info['ships']:
            dest_info['ships'].append(ship_id)
            self.save_location(dest, dest_info)

        # Updating the ship-specific info
        self.save_ship_location(ship_id, dest)

    def get_battle_rounds(self):
        key = self._build_battle_rounds_key()
        rounds_info = self.redis.get(key)
        if rounds_info:
            return json.loads(rounds_info.decode('utf-8'))
        return []

    def set_battle_rounds(self, rounds_info):
        key = self._build_battle_rounds_key()
        self.redis.set(key, json.dumps(rounds_info))

    def fire_round(self, ship_id, target_id):
        battle_rounds = self.get_battle_rounds()

        # Check for existing firing during this tick
        for round in battle_rounds:
            # Can't fire 2x in a round
            if round['ship_id'] == ship_id:
                raise FiringLimitError

        loc1 = self.get_ship_location(ship_id)
        loc2 = self.get_ship_location(target_id)
        d = distance_formula(loc1, loc2)

        # Create a battle round
        with self.app.app_context():
            ship1 = db.session.query(Ship).filter_by(id=ship_id).first()
            if ship1.weapon.range < d:
                raise WeaponRangeError

            if ship1.ammo == 0:
                raise WeaponOutOfAmmoError

            round = {
                'ship_id': ship_id,
                'damage': ship1.weapon.damage,
                'target': target_id,
            }
            battle_rounds.append(round)

        self.set_battle_rounds(battle_rounds)

    def execute_battle_rounds(self):
        battle_rounds = self.get_battle_rounds()
        self.set_battle_rounds([])
        if not battle_rounds:
            return

        with self.app.app_context():
            for round in battle_rounds:
                ship1 = db.session.query(Ship).filter_by(id=round['ship_id']).first()
                target = db.session.query(Ship).filter_by(id=round['target']).first()
                if target.shield <= 0:
                    target.health -= round['damage']
                else:
                    if target.shield < round['damage']:
                        target.health = target.health - round['damage'] + target.shield
                        target.shield = 0
                    else:
                        target.shield -= round['damage']

                print("Ship {} fired on Ship {}, which now has health ({}/{})".format(
                        ship1.id, target.id, target.shield, target.health))

                if target.health <= 0:
                    # ship dies :(
                    db.session.delete(target)
                    coords = self.get_ship_location(target.id)
                    location_data = self.get_location(coords)
                    if target.id in location_data['ships']:
                        location_data['ships'].remove(target.id)
                    self.save_location(coords, location_data)

                    ship_key = self._build_ship_key(target.id)
                    self.redis.delete(ship_key)
                    print("Ship {} has been killed x.x".format(target.id))

                else:
                    db.session.add(target)

                if ship1.weapon.name.upper() != 'LASER':
                    ship1.ammo -= ship1.weapon.ammo
                db.session.add(ship1)

            db.session.commit()

    def get_execution_queue(self):
        key = self._build_execution_queue_key()
        rounds_info = self.redis.get(key)
        if rounds_info:
            return json.loads(rounds_info.decode('utf-8'))
        return []

    def set_execution_queue(self, rounds_info):
        key = self._build_execution_queue_key()
        self.redis.set(key, json.dumps(rounds_info))

    def execute_on_delay(self, fn_string, args, timeout, comment=''):
        execution_queue = self.get_execution_queue()
        execution_queue.append({
            'fn_string': fn_string,
            'args': args,
            'timeout': timeout,
            'active': True,
            'comment': comment,
        })
        print("Received command:", comment)
        self.set_execution_queue(execution_queue)

    def execute_step(self):
        execution_queue = self.get_execution_queue()
        for cmd in execution_queue:
            cmd['timeout'] -= 1
            if cmd['timeout'] <= 0:
                print("Executing",cmd['comment'])
                self.execute_from_queue(cmd['fn_string'], cmd['args'])
                cmd['active'] = False
        execution_queue = [x for x in execution_queue if x['active']]
        self.set_execution_queue(execution_queue)

    def execute_from_queue(self, fn_string, args):
        if fn_string == 'capture':
            player_id, planet_id = args
            with self.app.app_context():
                player = db.session.query(Player).filter_by(id=player_id).first()
                planet = db.session.query(Planet).filter_by(id=planet_id).first()
                planet.player_id = player.id
                planet.player = player
                db.session.add(planet)
                db.session.commit()

            print("Planet {} has been captured by player {}".format(planet_id, player_id))

        elif fn_string == 'create_ship':
            ship_id,planet_id = args
            if not ship_id:
                return
            coords = self.planets.get(planet_id, {}).get('location')
            if not coords:
                raise PlanetNotFoundError

            self.add_ship(ship_id, coords)
            print("Added ship {}".format(ship_id))

