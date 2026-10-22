# Пример 1: основни движения
from robosim import Robot

robot = Robot("default.json")

robot.move_joints(45, 30)        # ставно движение, ъглите са в градуси
robot.move_to(400, -150)         # до точка (x, y) в mm
robot.move_line(400, 150)        # по права линия
robot.home()                     # обратно в началната позиция

print("Позиция:", robot.position)
print("Ъгли:", robot.joints)
robot.report()
