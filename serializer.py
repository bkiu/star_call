from init import mygalaxy

def serial_planet(planet):
    data = { "name": planet.name, "id": planet.id, "location": mygalaxy.get_planet_location(planet.id), "resources": planet.resources }
    if planet.player:
        data["player"] = planet.player.id
        data["player name"] = planet.player.username
    return data

def serial_ship(ship):
    data = {
        "name": ship.name,
        "location": mygalaxy.get_ship_location(ship.id),
        "player": ship.player.id,
        "player name": ship.player.username,
        "id": ship.id,
        "type": ship.type,
        "weapon": ship.weapon.name,
        "hull": ship.health,
        "shields": ship.shield,
    }
    if ship.player:
        data["player"] = ship.player.id
        data["player name"] = ship.player.username
    return data
