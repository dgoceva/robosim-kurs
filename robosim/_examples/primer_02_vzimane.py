# Пример 2: взимане и оставяне на детайл
from robosim import Robot

robot = Robot("default.json")
scene = robot.scene

cube = scene.cube("c1")              # детайлът с име c1
zone = scene.zone("A")               # зоната за оставяне

robot.move_to(cube.x, cube.y)
robot.grip()                         # затваря хващача
robot.move_to(zone.x, zone.y)
robot.release()                      # отваря хващача
robot.home()

print("Детайли в зона A:", scene.cubes_in("A"))
