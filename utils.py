from models import db, Planet, Player, Ship, Weapon
from init import mygalaxy

def create_ship(player, type, weapon, planet, cost=0):
    weapon = Weapon.query.filter_by(name=weapon).first_or_404()
    ship = Ship(player, type, weapon)
    print(ship)
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
