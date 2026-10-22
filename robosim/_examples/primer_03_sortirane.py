# Пример 3: сортиране на кубчета по цвят
from robosim import Robot

robot = Robot("sorting.json")
scene = robot.scene
robot.speed(100)

placed = {"red": 0, "green": 0, "blue": 0}   # брой оставени във всяка зона

for cube in list(scene.cubes):
    zone = scene.zone(cube.color)
    robot.move_to(cube.x, cube.y)
    robot.grip()
    # подреждаме в редица в зоната, за да не са едно върху друго
    offset = (placed[cube.color] - 1) * 45
    if zone.w > zone.h:
        robot.move_to(zone.x + offset, zone.y)
    else:
        robot.move_to(zone.x, zone.y + offset)
    robot.release()
    placed[cube.color] += 1

robot.home()
robot.report()
