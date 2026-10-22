"""Робот: плосък манипулатор с две звена и хващач (изглед отгоре)."""
import atexit
import math
import os

from . import kinematics as kin
from .scene import Scene, RobotError

DT = 0.04  # s, стъпка на симулацията


def _seg_intersect(p1, p2, p3, p4):
    """Пресичат ли се отсечките p1-p2 и p3-p4."""
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    d1, d2 = cross(p3, p4, p1), cross(p3, p4, p2)
    d3, d4 = cross(p1, p2, p3), cross(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _seg_rect(p1, p2, rect):
    """Пресича ли отсечката правоъгълника (или е вътре в него)."""
    if rect.contains(*p1) or rect.contains(*p2):
        return True
    x0, x1, y0, y1 = rect.bounds
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return any(_seg_intersect(p1, p2, corners[i], corners[(i + 1) % 4]) for i in range(4))


class Robot:
    """Учебен робот.

    Пример:
        from robosim import Robot
        robot = Robot("default.json")
        robot.move_to(400, 200)
        robot.grip()
    """

    def __init__(self, scene=None, name="R1", base=None, links=None, home=None, show=True, sim_speed=1.0, color="#e8780c"):
        if scene is None:
            scene = Scene()
        elif isinstance(scene, str):
            scene = Scene.load(scene)
        self.scene = scene
        cfg = scene.robot_config if not scene.robots else {}
        self.name = name
        self.base = tuple(base if base is not None else cfg.get("base", (0, 0)))
        self.links = list(links if links is not None else cfg.get("links", [350, 300]))
        if len(self.links) != 2:
            raise RobotError("Симулаторът поддържа робот с две звена")
        self.limits = [tuple(l) for l in cfg.get("limits", [[-170, 170], [-150, 150]])]
        self.joint_speed = float(cfg.get("joint_speed", 90))     # градуса/s
        self.linear_speed = float(cfg.get("linear_speed", 250))  # mm/s
        self.grip_time = float(cfg.get("grip_time", 0.3))        # s
        self.home_joints = tuple(home if home is not None else cfg.get("home", (0, 90)))
        self.color = color
        self.elbow = "right"
        self.sim_speed = float(sim_speed)
        self._speed = 1.0
        self._q = tuple(float(a) for a in self.home_joints)
        self.gripper_closed = False
        self.holding = None
        self.distance = 0.0
        self.picks = 0
        self.log = []
        self._pen = None
        self._check_limits(self._q)
        self._check_collision(self._q)
        scene.robots.append(self)
        # ROBOSIM_HEADLESS=1 изпълнява програмата без прозорец (за автоматични проверки)
        self.show = show and not os.environ.get("ROBOSIM_HEADLESS")
        if self.show:
            if scene.view is None:
                from .view import View
                scene.view = View(scene)
                atexit.register(_keep_open, scene.view)
            scene.view.add_robot(self)
            scene.view.update(0.01)
        self._log(f"Роботът е готов. Позиция {self._fmt(self.position)}")

    # ---------- състояние ----------
    @property
    def joints(self):
        """Текущите ъгли на ставите (q1, q2) в градуси."""
        return self._q

    @property
    def points(self):
        """Точките на основата, ставата и края на ръката."""
        return kin.forward(self.links, self._q, self.base)

    @property
    def position(self):
        """Позицията (x, y) на хващача в mm."""
        return self.points[-1]

    @property
    def reach(self):
        """(минимален, максимален) обхват в mm."""
        return kin.reach(self.links)

    @property
    def time(self):
        """Текущото време на симулацията в секунди."""
        return self.scene.time

    # ---------- настройки ----------
    def speed(self, percent):
        """Задава скоростта в проценти от максималната (1 до 100)."""
        if not 1 <= percent <= 100:
            raise RobotError("Скоростта трябва да е между 1 и 100 %")
        self._speed = percent / 100
        self._log(f"Скорост {percent} %")

    def set_elbow(self, elbow):
        """Избира положението на лакътя при move_to: "right" или "left"."""
        if elbow not in ("right", "left"):
            raise RobotError('Лакътят може да е "right" или "left"')
        self.elbow = elbow

    # ---------- движения ----------
    def move_joints(self, q1, q2):
        """Ставно движение: двете стави стигат целевите ъгли едновременно."""
        target = (float(q1), float(q2))
        self._check_limits(target)
        start = self._q
        delta = max(abs(target[0] - start[0]), abs(target[1] - start[1]))
        duration = delta / (self.joint_speed * self._speed)
        self._run(duration, lambda s: (start[0] + (target[0] - start[0]) * s, start[1] + (target[1] - start[1]) * s))
        self._log(f"move_joints({q1:g}, {q2:g})")

    def move_to(self, x, y, elbow=None):
        """Движение до точка (x, y). Ставите се движат едновременно, пътят е крива линия."""
        q = self._solve(x, y, elbow)
        start = self._q
        delta = max(abs(q[0] - start[0]), abs(q[1] - start[1]))
        duration = delta / (self.joint_speed * self._speed)
        self._run(duration, lambda s: (start[0] + (q[0] - start[0]) * s, start[1] + (q[1] - start[1]) * s))
        self._log(f"move_to({x:g}, {y:g})")

    def move_line(self, x, y):
        """Линейно движение: хващачът се движи по права линия до (x, y)."""
        x0, y0 = self.position
        length = math.hypot(x - x0, y - y0)
        if length < 1e-9:
            return
        self._solve(x, y, None)  # проверка на крайната точка
        elbow = "right" if self._q[1] >= 0 else "left"
        duration = length / (self.linear_speed * self._speed)

        def path(s):
            q = kin.inverse(self.links, x0 + (x - x0) * s, y0 + (y - y0) * s, elbow, self.base)
            if q is None:
                raise RobotError(f"Линейният път до {self._fmt((x, y))} минава извън обхвата")
            return self._unwrap(q)
        self._run(duration, path)
        self._log(f"move_line({x:g}, {y:g})")

    def follow(self, joints, dt):
        """Изпълнява траектория: поредица от ъгли (q1, q2) през dt секунди.

        Целият път се проверява преди движението: граници на ставите и
        максимална скорост на ставите. При нарушение нищо не се изпълнява.
        """
        joints = [(float(q[0]), float(q[1])) for q in joints]
        dt = float(dt)
        if dt <= 0:
            raise RobotError("dt трябва да е положително")
        limit = self.joint_speed * self._speed
        prev = self._q
        for i, q in enumerate(joints):
            self._check_limits(q)
            w = max(abs(q[0] - prev[0]), abs(q[1] - prev[1])) / dt
            if w > limit * 1.001:
                raise RobotError(f"Точка {i}: скорост на става {w:.0f}°/s, разрешени {limit:g}°/s")
            prev = q
        draw_every = max(1, int(round(self.sim_speed * DT / dt)))
        for i, q in enumerate(joints, 1):
            self._set(q)
            self.scene.step(dt)
            if self.show and (i % draw_every == 0 or i == len(joints)):
                self.scene.view.update(dt * draw_every / self.sim_speed)
        self._log(f"follow({len(joints)} точки, dt = {dt:g} s)")

    def move_by(self, dx, dy):
        """Линейно движение с отместване (dx, dy) от текущата позиция."""
        x, y = self.position
        self.move_line(x + dx, y + dy)

    def home(self):
        """Връщане в началната позиция."""
        self.move_joints(*self.home_joints)

    def wait(self, seconds):
        """Изчакване. Сцената продължава да работи (конвейерът се движи)."""
        self._run(float(seconds), lambda s: self._q)

    def can_reach(self, x, y):
        """True, ако роботът може да достигне точката (x, y)."""
        try:
            self._solve(x, y, None)
            return True
        except RobotError:
            return False

    # ---------- хващач ----------
    def grip(self):
        """Затваря хващача. Връща True, ако е хванат детайл."""
        self.wait(self.grip_time)
        return self._close()

    def _close(self):
        self.gripper_closed = True
        if self.holding is None:
            cube = self.scene.top_cube_at(*self.position)
            if cube is not None:
                cube.held_by = self
                cube.level = 0
                self.holding = cube
                self.picks += 1
                self._log(f"Хванат детайл {cube.name} ({cube.color})")
            else:
                self._log("Хващачът е затворен, но няма детайл")
        self._redraw()
        return self.holding is not None

    def release(self):
        """Отваря хващача и оставя детайла (ако има такъв) в текущата позиция."""
        self.wait(self.grip_time)
        self._open()

    def _open(self):
        self.gripper_closed = False
        cube = self.holding
        if cube is not None:
            x, y = self.position
            cube.x, cube.y = x, y
            cube.held_by = None
            self.holding = None
            below = [c for c in self.scene.cubes if c is not cube and c.held_by is None and c.covers(x, y)]
            cube.level = (max(c.level for c in below) + 1) if below else 0
            where = f" върху {len(below)} детайл(а)" if below else ""
            self._log(f"Оставен детайл {cube.name} в {self._fmt((x, y))}{where}")
        self._redraw()

    close_gripper = grip
    open_gripper = release

    # ---------- рисуване ----------
    def pen_down(self, color="black"):
        """Започва рисуване: хващачът оставя следа."""
        if self.show:
            line = self.scene.view.add_trace(color)
            x, y = self.position
            self._pen = (line, [x], [y])
        else:
            self._pen = (None, [], [])

    def pen_up(self):
        """Спира рисуването."""
        self._pen = None

    # ---------- сензори ----------
    def sensor(self, name):
        """Състоянието на сензор от сцената (True или False)."""
        return self.scene.sensor(name)

    # ---------- отчет ----------
    def report(self):
        """Извежда обобщение на работата."""
        print(f"Робот {self.name}")
        print(f"  време на симулацията: {self.time:.2f} s")
        print(f"  изминат път на хващача: {self.distance:.0f} mm")
        print(f"  хванати детайли: {self.picks}")

    def done(self):
        """Оставя прозореца отворен, докато потребителят го затвори."""
        if self.show:
            _keep_open(self.scene.view)

    # ---------- ръчно водене ----------
    def teach(self, step=2.0):
        """Ръчно водене с клавиатурата. Връща списък със записаните точки.

        Стрелки наляво/надясно: става 1, нагоре/надолу: става 2,
        g: хващач, интервал: запис на точка, + / -: стъпка, Enter: край.
        """
        if not self.show:
            raise RobotError("Ръчното водене изисква прозорец (show=True)")
        import matplotlib as mpl
        view = self.scene.view
        saved = {k: v for k, v in mpl.rcParams.items() if k.startswith("keymap.")}
        for k in saved:
            mpl.rcParams[k] = []
        points = []
        state = {"done": False, "step": float(step)}
        print("Ръчно водене: стрелки - стави, g - хващач, интервал - запис, + / - стъпка, Enter - край")

        def on_key(event):
            q1, q2 = self._q
            st = state["step"]
            moves = {"left": (st, 0), "right": (-st, 0), "up": (0, st), "down": (0, -st)}
            try:
                if event.key in moves:
                    d = moves[event.key]
                    self._set((q1 + d[0], q2 + d[1]))
                elif event.key == "g":
                    self._open() if self.gripper_closed else self._close()
                elif event.key == " ":
                    x, y = self.position
                    points.append((round(x, 1), round(y, 1), self.gripper_closed))
                    print(f"  точка {len(points)}: ({x:.1f}, {y:.1f}), хващач {'затворен' if self.gripper_closed else 'отворен'}")
                elif event.key in ("+", "="):
                    state["step"] = min(state["step"] * 2, 20)
                    print(f"  стъпка {state['step']:g}°")
                elif event.key == "-":
                    state["step"] = max(state["step"] / 2, 0.25)
                    print(f"  стъпка {state['step']:g}°")
                elif event.key == "enter":
                    state["done"] = True
            except RobotError as err:
                print("  ", err)
            self._redraw()

        cid = view.fig.canvas.mpl_connect("key_press_event", on_key)
        try:
            while not state["done"]:
                view.update(0.05)
        finally:
            view.fig.canvas.mpl_disconnect(cid)
            mpl.rcParams.update(saved)
        print(f"Записани точки: {len(points)}")
        return points

    # ---------- вътрешни ----------
    def _fmt(self, p):
        return f"({p[0]:.1f}, {p[1]:.1f})"

    def _log(self, text):
        self.log.append(f"{self.scene.time:8.2f} s  {text}")

    def _check_limits(self, q):
        for i, (a, (lo, hi)) in enumerate(zip(q, self.limits)):
            if not lo - 1e-9 <= a <= hi + 1e-9:
                raise RobotError(f"Става {i + 1}: ъгъл {a:.1f}° е извън границите [{lo}°, {hi}°]")

    def _unwrap(self, q):
        """Избира ъглите най-близо до текущите (без скок от 180 към -180)."""
        out = []
        for a, cur in zip(q, self._q):
            while a - cur > 180:
                a -= 360
            while a - cur < -180:
                a += 360
            out.append(a)
        return tuple(out)

    def _solve(self, x, y, elbow):
        lo, hi = self.reach
        d = math.hypot(x - self.base[0], y - self.base[1])
        if d > hi + 1e-6 or d < lo - 1e-6:
            raise RobotError(f"Точката {self._fmt((x, y))} е извън обхвата: разстояние {d:.1f} mm, обхват от {lo:g} до {hi:g} mm")
        order = [elbow or self.elbow]
        order.append("left" if order[0] == "right" else "right")
        last = None
        for e in order if elbow is None else order[:1]:
            q = kin.inverse(self.links, x, y, e, self.base)
            for cand in (self._unwrap(q), q):
                try:
                    self._check_limits(cand)
                    return cand
                except RobotError as err:
                    last = err
        raise RobotError(f"Точката {self._fmt((x, y))} не е достижима: {last}")

    def _segments(self):
        pts = self.points
        return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]

    def _check_collision(self, q):
        pts = kin.forward(self.links, q, self.base)
        segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        for a, b in segs:
            for o in self.scene.obstacles:
                if _seg_rect(a, b, o):
                    raise RobotError(f"Сблъсък с препятствие {o.name!r} при q = ({q[0]:.1f}°, {q[1]:.1f}°)")
            for r in self.scene.robots:
                if r is self:
                    continue
                for c, d in r._segments():
                    if _seg_intersect(a, b, c, d):
                        raise RobotError(f"Сблъсък с робот {r.name} при q = ({q[0]:.1f}°, {q[1]:.1f}°)")

    def _set(self, q):
        """Поставя ставите в положение q след проверка (без анимация)."""
        self._check_limits(q)
        self._check_collision(q)
        old = self.position
        self._q = (float(q[0]), float(q[1]))
        new = self.position
        self.distance += math.hypot(new[0] - old[0], new[1] - old[1])
        if self.holding:
            self.holding.x, self.holding.y = new
        if self._pen:
            line, xs, ys = self._pen
            xs.append(new[0])
            ys.append(new[1])
            if line is not None:
                line.set_data(xs, ys)

    def _run(self, duration, path):
        steps = max(1, math.ceil(duration / DT - 1e-9))
        dt = duration / steps if duration > 0 else 0.0
        draw_every = max(1, int(round(self.sim_speed)))
        for i in range(1, steps + 1):
            self._set(path(i / steps))
            self.scene.step(dt)
            if self.show and (i % draw_every == 0 or i == steps):
                self.scene.view.update(dt * draw_every / self.sim_speed if dt > 0 else 0.001)

    def _redraw(self):
        if self.show:
            self.scene.view.update(0.001)


def _keep_open(view):
    import matplotlib.pyplot as plt
    if view is not None and not view.closed and not getattr(view, "_kept", False):
        view._kept = True
        plt.ioff()
        plt.show()
