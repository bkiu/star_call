def battle_damage(ship_set, target):
    damage_dealt = sum([ship.get_damage_dealth() for ship in ship_set])

    if damage_dealt <= target.shield:
        target.shield -= damage_dealt
    else:
        target.health -= damage_dealt - target.shield
        target.shield = 0
    target.save()
