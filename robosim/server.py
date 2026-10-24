"""Виртуален контролер: роботът се управлява с текстови команди по TCP.

Стартиране (от папката на симулатора):
    python -m robosim.server default.json
    python -m robosim.server default.json --port 5000

Протокол: по една команда на ред, отговорът е един ред.
    MOVEJ q1 q2      ставно движение               -> OK
    MOVE x y         движение до точка             -> OK
    LINE x y         линейно движение              -> OK
    HOME             начална позиция               -> OK
    GRIP             затваря хващача               -> OK 1 (хванат детайл) или OK 0
    RELEASE          отваря хващача                -> OK
    SPEED p          скорост в проценти            -> OK
    WAIT s           изчакване в секунди           -> OK
    POS              позиция на хващача            -> OK x y
    JOINTS           ъгли на ставите               -> OK q1 q2
    SENSOR име       състояние на сензор           -> OK 1 или OK 0
    TIME             време на симулацията          -> OK t
    CONVEYOR 0|1     спира или пуска конвейера     -> OK
    COLOR x y        цвят на детайла в точката     -> OK red или OK NONE
    PING             проверка на връзката          -> OK
При грешка отговорът е: ERR описание
"""
import argparse
import queue
import socket
import threading

from .robot import Robot
from .scene import Scene, RobotError


def execute(robot, line):
    """Изпълнява една текстова команда и връща отговора."""
    parts = line.strip().split()
    if not parts:
        return "ERR празна команда"
    cmd, args = parts[0].upper(), parts[1:]

    def nums(n):
        if len(args) != n:
            raise RobotError(f"{cmd} очаква {n} число(а)")
        try:
            return [float(a) for a in args]
        except ValueError:
            raise RobotError(f"{cmd}: аргументите трябва да са числа")
    try:
        if cmd == "MOVEJ":
            robot.move_joints(*nums(2))
        elif cmd == "MOVE":
            robot.move_to(*nums(2))
        elif cmd == "LINE":
            robot.move_line(*nums(2))
        elif cmd == "HOME":
            robot.home()
        elif cmd == "GRIP":
            return "OK 1" if robot.grip() else "OK 0"
        elif cmd == "RELEASE":
            robot.release()
        elif cmd == "SPEED":
            robot.speed(*nums(1))
        elif cmd == "WAIT":
            robot.wait(*nums(1))
        elif cmd == "POS":
            x, y = robot.position
            return f"OK {x:.2f} {y:.2f}"
        elif cmd == "JOINTS":
            q1, q2 = robot.joints
            return f"OK {q1:.2f} {q2:.2f}"
        elif cmd == "SENSOR":
            if len(args) != 1:
                raise RobotError("SENSOR очаква име на сензор")
            return "OK 1" if robot.sensor(args[0]) else "OK 0"
        elif cmd == "TIME":
            return f"OK {robot.time:.2f}"
        elif cmd == "CONVEYOR":
            if robot.scene.conveyor is None:
                raise RobotError("в сцената няма конвейер")
            robot.scene.conveyor.running = bool(nums(1)[0])
        elif cmd == "COLOR":
            cube = robot.scene.top_cube_at(*nums(2))
            return f"OK {cube.color if cube else 'NONE'}"
        elif cmd == "PING":
            pass
        else:
            return f"ERR непозната команда {cmd}"
        return "OK"
    except RobotError as err:
        return f"ERR {err}"


def _client_thread(conn, addr, requests, verbose=True):
    with conn:
        f = conn.makefile("rw", encoding="utf-8", newline="\n")
        for line in f:
            if not line.strip():
                continue
            reply = queue.Queue()
            requests.put((line, reply))
            f.write(reply.get() + "\n")
            f.flush()
    if verbose:
        print(f"Клиентът {addr[0]}:{addr[1]} се изключи")


def serve(robot, host="127.0.0.1", port=5000, verbose=True, until=None, on_ready=None):
    """Стартира сървъра. Командите се изпълняват една по една.

    until: функция; сървърът спира, когато върне True (по подразбиране работи безкрайно).
    on_ready: функция, която се извиква, след като сървърът започне да слуша.
    """
    requests = queue.Queue()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen()

    def accept():
        while True:
            conn, addr = srv.accept()
            if verbose:
                print(f"Свързан клиент {addr[0]}:{addr[1]}")
            threading.Thread(target=_client_thread, args=(conn, addr, requests, verbose), daemon=True).start()
    threading.Thread(target=accept, daemon=True).start()
    if verbose:
        end = " Затворете прозореца за край." if until is None else ""
        print(f"Виртуалният контролер слуша на {host}:{port}.{end}")
    if on_ready is not None:
        on_ready()
    while until is None or not until():
        try:
            line, reply = requests.get(timeout=0.05)
        except queue.Empty:
            robot.wait(0.05) if robot.scene.conveyor else (robot.scene.view.update(0.05) if robot.show else None)
            continue
        answer = execute(robot, line)
        if verbose:
            print(f"  {line.strip():<24} -> {answer}")
        reply.put(answer)
    srv.close()


def run_client(robot, program, port=5000, host="127.0.0.1", verbose=False):
    """Контролерът и програмата-клиент в един файл, без втори терминал.

    Контролерът работи в главната нишка (там се обновява прозорецът),
    а program(port) се изпълнява в отделна нишка и се свързва с него.
    Връща се, когато program завърши.
    """
    errors = []

    def worker():
        try:
            program(port)
        except Exception as err:          # грешката се показва след края
            errors.append(err)

    client = threading.Thread(target=worker, daemon=True)
    serve(robot, host, port, verbose, until=lambda: not client.is_alive(), on_ready=client.start)
    if errors:
        raise errors[0]


def serve_background(robot, host="127.0.0.1", port=5000, verbose=False):
    """Стартира сървъра в отделна нишка и веднага се връща.

    Удобно за примери без прозорец (show=False). Ако роботът е с прозорец,
    използвайте run_client: графиката не може да се обновява от отделна нишка.
    """
    if robot.show:
        print("Забележка: при serve_background прозорецът не се обновява. "
              "За анимация използвайте run_client (вижте примера primer_06_server.py).")
        robot.show = False
    t = threading.Thread(target=serve, args=(robot, host, port, verbose), daemon=True)
    t.start()
    import time
    for _ in range(100):                      # изчакване, докато сървърът слуша
        try:
            socket.create_connection((host, port), timeout=0.1).close()
            break
        except OSError:
            time.sleep(0.02)
    return t


def main():
    p = argparse.ArgumentParser(description="Виртуален контролер на учебния робот")
    p.add_argument("scene", nargs="?", default="default.json", help="JSON файл със сцена")
    p.add_argument("--host", default="127.0.0.1", help="адрес (0.0.0.0 за достъп от други компютри)")
    p.add_argument("--port", type=int, default=5000)
    a = p.parse_args()
    robot = Robot(Scene.load(a.scene))
    serve(robot, a.host, a.port)


if __name__ == "__main__":
    main()
