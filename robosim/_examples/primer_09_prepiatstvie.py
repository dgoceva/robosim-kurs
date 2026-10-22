# Пример 9: заобикаляне на препятствие
# При ставно движение (move_to) хващачът описва дъга и може да закачи
# колоната. С линейни движения (move_line) пътят е предвидим.
from robosim import Robot, RobotError

robot = Robot("obstacles.json")
scene = robot.scene
cube = scene.cube("c1")
target = scene.zone("цел")

robot.move_line(cube.x, cube.y)
robot.grip()

try:
    robot.move_line(target.x, target.y)     # направо през колоната
except RobotError as err:
    print("Грешка:", err)

# заобикаляне: назад, надолу покрай колоната, напред
robot.move_line(cube.x, cube.y)
robot.move_line(420, cube.y)
robot.move_line(420, target.y)
robot.move_line(target.x, target.y)
robot.release()
robot.move_line(420, target.y)
robot.report()
