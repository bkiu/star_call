from server import db, app
import models
with app.app_context():
    db.create_all()
    laser =  models.Weapon("Laser", 0, 0, 50, 1, 1, 2)
    missles = models.Weapon("Missles", 0, 3, 80, 1, 2, 1)
    plasma = models.Weapon("Plasma", 0, 1, 100, 1, 3, 1)
    db.session.add(laser)
    db.session.add(missles)
    db.session.add(plasma)
    db.session.commit()

