# Пример 4: взимане на детайли от конвейер със сензор
from robosim import Robot

robot = Robot("conveyor.json")
scene = robot.scene
sensor = scene.sensors[0]
placed = {"red": 0, "green": 0, "blue": 0}   # брой оставени във всяка зона

robot.move_to(sensor.x, sensor.y)        # чакаме над сензора

for i in range(6):
    while not robot.sensor("S1"):        # докато няма детайл
        robot.wait(0.1)
    scene.conveyor.running = False       # спираме конвейера
    cube = scene.top_cube_at(sensor.x, sensor.y)
    robot.move_to(cube.x, cube.y)
    robot.grip()
    scene.conveyor.running = True        # пускаме конвейера отново
    zone = scene.zone(cube.color)
    offset = (placed[cube.color] - 1) * 45   # -45, 0, 45: три места в зоната
    robot.move_to(zone.x + offset, zone.y)
    robot.release()
    placed[cube.color] += 1
    robot.move_to(sensor.x, sensor.y)

robot.report()
