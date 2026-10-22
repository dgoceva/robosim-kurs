# Пример 8: рисуване на квадрат и окръжност
import math
from robosim import Robot

robot = Robot("drawing.json")

# квадрат със страна 200 mm и център (400, 0)
robot.move_to(300, -100)
robot.pen_down("blue")
robot.move_line(500, -100)
robot.move_line(500, 100)
robot.move_line(300, 100)
robot.move_line(300, -100)
robot.pen_up()

# окръжност с радиус 80 mm, апроксимирана с 36 отсечки
cx, cy, r = 400, 0, 80
robot.move_to(cx + r, cy)
robot.pen_down("red")
for i in range(1, 37):
    a = math.radians(i * 10)
    robot.move_line(cx + r * math.cos(a), cy + r * math.sin(a))
robot.pen_up()
robot.home()
