# Пример 6: управление по мрежата
# Виртуалният контролер и програмата, която му изпраща команди, са в един файл:
# run_client стартира контролера (с прозореца) и пуска функцията program,
# която се свързва с него по TCP като с истински робот.
from robosim import Robot
from robosim.server import run_client
from robosim.client import RemoteRobot


def program(port):
    robot = RemoteRobot("127.0.0.1", port)       # връзка с контролера
    print("Позиция:", robot.position)
    robot.move_to(400, -150)
    print("Хванат детайл:", robot.grip())
    robot.move_to(0, 450)
    robot.release()
    robot.home()
    print("Време на симулацията:", robot.time, "s")
    robot.close()


run_client(Robot("default.json"), program, port=5000, verbose=True)

# Вариант с два терминала (както при реален робот):
#   1. в първия терминал:  python -m robosim.server default.json
#   2. във втория терминал пуснете програма, която използва RemoteRobot("127.0.0.1", 5000)
