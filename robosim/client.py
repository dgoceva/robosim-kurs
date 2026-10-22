"""Клиент за виртуалния контролер (вижте server.py).

Пример:
    from robosim.client import RemoteRobot
    robot = RemoteRobot("127.0.0.1", 5000)
    robot.move_to(400, 200)
    print(robot.position)
"""
import socket

from .scene import RobotError


class RemoteRobot:
    """Робот, управляван по мрежата. Методите са същите като при Robot."""

    def __init__(self, host="127.0.0.1", port=5000, timeout=120):
        try:
            self._sock = socket.create_connection((host, port), timeout=timeout)
        except OSError as err:
            raise RobotError(f"Няма връзка с контролера на {host}:{port}. Стартиран ли е сървърът? ({err})")
        self._f = self._sock.makefile("rw", encoding="utf-8", newline="\n")

    def command(self, text):
        """Изпраща текстова команда и връща отговора без OK."""
        self._f.write(text.strip() + "\n")
        self._f.flush()
        answer = self._f.readline().strip()
        if not answer:
            raise RobotError("Контролерът прекъсна връзката")
        if answer.startswith("ERR"):
            raise RobotError(answer[4:])
        return answer[3:]

    def move_joints(self, q1, q2):
        self.command(f"MOVEJ {q1} {q2}")

    def move_to(self, x, y):
        self.command(f"MOVE {x} {y}")

    def move_line(self, x, y):
        self.command(f"LINE {x} {y}")

    def home(self):
        self.command("HOME")

    def grip(self):
        return self.command("GRIP") == "1"

    def release(self):
        self.command("RELEASE")

    def speed(self, percent):
        self.command(f"SPEED {percent}")

    def wait(self, seconds):
        self.command(f"WAIT {seconds}")

    def sensor(self, name):
        return self.command(f"SENSOR {name}") == "1"

    def conveyor(self, running):
        self.command(f"CONVEYOR {1 if running else 0}")

    def color_at(self, x, y):
        c = self.command(f"COLOR {x} {y}")
        return None if c == "NONE" else c

    @property
    def position(self):
        x, y = self.command("POS").split()
        return float(x), float(y)

    @property
    def joints(self):
        q1, q2 = self.command("JOINTS").split()
        return float(q1), float(q2)

    @property
    def time(self):
        return float(self.command("TIME"))

    def close(self):
        self._sock.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
