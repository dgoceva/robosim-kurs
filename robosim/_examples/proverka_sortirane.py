# Автоматична проверка на решение на задачата за сортиране (сцена sorting.json)
# Използване:  python proverka_sortirane.py reshenie_petrov.py
# Решението трябва да създава робота с име на променливата robot.
import os
import runpy
import sys

os.environ["ROBOSIM_HEADLESS"] = "1"       # без прозорец, много по-бързо

if len(sys.argv) != 2:
    print("Използване: python proverka_sortirane.py файл_с_решение.py")
    sys.exit(1)

try:
    result = runpy.run_path(sys.argv[1])
except Exception as err:
    print("Решението спря с грешка:", err)
    print("РЕЗУЛТАТ: ГРЕШНО")
    sys.exit(1)

robot = result.get("robot")
if robot is None:
    print("В решението няма променлива robot")
    sys.exit(1)
scene = robot.scene
if len(scene.zones) != 3 or scene.name != "Сортиране по цвят":
    print("Решението не използва сцената sorting.json")
    sys.exit(1)
ok = True
for color in ("red", "green", "blue"):
    cubes = scene.cubes_in(color)
    wrong = [c.name for c in cubes if c.color != color]
    stacked = [c.name for c in cubes if c.level > 0]
    print(f"Зона {color:5}: {len(cubes)} детайла, в грешна зона: {wrong}, един върху друг: {stacked}")
    if len(cubes) != 3 or wrong:
        ok = False
print(f"Време на симулацията: {robot.time:.2f} s, изминат път: {robot.distance:.0f} mm")
print("РЕЗУЛТАТ:", "ВЯРНО" if ok else "ГРЕШНО")
