# Пример 7: обучение чрез показване
# Водете робота с клавиатурата (щракнете първо върху прозореца):
#   стрелки - стави, g - хващач, интервал - запис на точка, Enter - край
from robosim import Robot

robot = Robot("default.json")
points = robot.teach()

print("Възпроизвеждане на", len(points), "точки")
robot.home()
for x, y, closed in points:
    robot.move_to(x, y)
    if closed and not robot.gripper_closed:
        robot.grip()
    elif not closed and robot.gripper_closed:
        robot.release()
