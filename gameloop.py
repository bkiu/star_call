import time

from models import Planet, Player, Ship
from navigate import make_path_2d
from init import app, db
from universe import Galaxy


class Game(object):
    RESOURCE_RATIO_PER_TICK = 0.0001
    SHIELDS_INCREMENT = 5

    def __init__(self, key):
        self.gametime = 0
        self.galaxy = Galaxy(app, key)

    def resource_increment(self):
        with app.app_context():
            players = db.session.query(Player).all()

            for player in players:
                planets = db.session.query(Planet).filter_by(player_id=player.id)
                total_resources = 0
                for planet in planets:
                    total_resources += planet.resources

                increment_amount = int(total_resources * self.RESOURCE_RATIO_PER_TICK)
                if increment_amount == 0:
                    increment_amount += 1
                player.star_tokens += increment_amount
                if self.gametime % 10 == 0:
                    print("Player {} has {} star_tokens".format(player.username, player.star_tokens))
                db.session.add(player)

            db.session.commit()

    def shields_regen(self):
        with app.app_context():
            ships = db.session.query(Ship).all()
            for ship in ships:
                if ship.shield < Ship.SHIELD[ship.type]:
                    ship.shield += self.SHIELDS_INCREMENT
                    db.session.add(ship)
            db.session.commit()

    def loop(self):
        while True:
            self.gametime += 1
            self.galaxy.ship_travel_step()
            self.galaxy.execute_battle_rounds()
            self.galaxy.execute_step()
            self.resource_increment()
            self.shields_regen()
            time.sleep(0.5)

g = Game('foo8')
g.loop()
