# Пример 6: управление по мрежата
# 1. В един терминал стартирайте контролера:
#        python -m robosim.server default.json
# 2. В друг терминал изпълнете този файл:
#        python primer_06_server.py
from robosim.client import RemoteRobot

robot = RemoteRobot("127.0.0.1", 5000)
print("Позиция:", robot.position)
robot.move_to(400, -150)
print("Хванат детайл:", robot.grip())
robot.move_to(0, 450)
robot.release()
robot.home()
print("Време на симулацията:", robot.time, "s")
robot.close()
