# Пример 7: обучение чрез показване
# Мишка: ляв бутон върху масата - роботът отива там; десен бутон - запис на точката.
# Бутоните под масата: q1 +/-, q2 +/- (фино нагласяне), „Хващач“, „Запис“, „Край“.
# Може и с клавиатурата, след щракване върху прозореца: стрелки, g, интервал, Enter.
# След „Край“ роботът повтаря записаните точки.
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
