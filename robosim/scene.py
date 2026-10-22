"""Сцената: работна маса, кубчета, зони, сензори, препятствия и конвейер.

Всички координати са в милиметри. Правоъгълниците се задават с център (x, y),
ширина w и височина h.
"""
import json
import random
from pathlib import Path

COLORS = {
    "red": (215, 45, 45),
    "green": (45, 160, 70),
    "blue": (45, 90, 215),
    "yellow": (235, 195, 30),
    "orange": (240, 130, 20),
    "purple": (140, 60, 170),
    "gray": (120, 120, 120),
    "black": (30, 30, 30),
    "white": (250, 250, 250),
}


class RobotError(Exception):
    """Грешка при работа с робота или сцената."""


class Rect:
    """Правоъгълна област със център (x, y), ширина w и височина h."""

    def __init__(self, name, x, y, w, h, color="gray"):
        self.name = name
        self.x, self.y, self.w, self.h = float(x), float(y), float(w), float(h)
        self.color = color

    @property
    def center(self):
        return (self.x, self.y)

    @property
    def bounds(self):
        """(xmin, xmax, ymin, ymax)"""
        return (self.x - self.w / 2, self.x + self.w / 2, self.y - self.h / 2, self.y + self.h / 2)

    def contains(self, x, y):
        x0, x1, y0, y1 = self.bounds
        return x0 <= x <= x1 and y0 <= y <= y1

    def __repr__(self):
        return f"{type(self).__name__}({self.name!r}, x={self.x:g}, y={self.y:g}, w={self.w:g}, h={self.h:g})"


class Zone(Rect):
    """Зона за оставяне на детайли."""


class Sensor(Rect):
    """Сензор за присъствие: активен е, когато в областта има кубче."""


class Obstacle(Rect):
    """Препятствие: звената на робота не трябва да го пресичат."""


class Cube:
    """Кубче (детайл). level е броят кубчета под него."""

    def __init__(self, name, x, y, color="red", size=40):
        self.name = name
        self.x, self.y = float(x), float(y)
        self.color = color
        self.size = float(size)
        self.level = 0
        self.held_by = None

    @property
    def position(self):
        return (self.x, self.y)

    def covers(self, x, y, tolerance=2.0):
        """True, ако точката (x, y) е над кубчето (с допуск в mm)."""
        h = self.size / 2 + tolerance
        return abs(x - self.x) <= h and abs(y - self.y) <= h

    def __repr__(self):
        return f"Cube({self.name!r}, x={self.x:.1f}, y={self.y:.1f}, color={self.color!r})"


class Conveyor(Rect):
    """Конвейер: движи кубчетата върху себе си по оста X."""

    def __init__(self, name, x, y, w, h, speed=50, direction="+x", spawn=None):
        super().__init__(name, x, y, w, h, "gray")
        self.speed = float(speed)
        self.direction = 1 if direction == "+x" else -1
        self.spawn = spawn
        self.running = True
        self._timer = 0.0
        self._count = 0
        self._rng = random.Random(spawn.get("seed", 1) if spawn else 1)


class Scene:
    """Работната среда на робота."""

    def __init__(self, name="Учебна сцена", table=None):
        self.name = name
        self.table = table or {"xmin": -400, "xmax": 750, "ymin": -600, "ymax": 600}
        self.robot_config = {}
        self.cubes = []
        self.zones = []
        self.sensors = []
        self.obstacles = []
        self.conveyor = None
        self.robots = []
        self.time = 0.0
        self.view = None
        self._camera = None

    # ---------- зареждане и запис ----------
    @classmethod
    def load(cls, path):
        """Зарежда сцена от JSON файл."""
        path = Path(path)
        if not path.exists():
            # търсим в ./scenes, в сцените на пакета и в папката scenes до пакета
            here = Path(__file__).resolve().parent
            for alt in (Path.cwd() / "scenes" / path.name, here / "scenes" / path.name,
                        here.parent / "scenes" / path.name):
                if alt.exists():
                    path = alt
                    break
            else:
                raise RobotError(f"Файлът със сцената не е намерен: {path}")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        s = cls(data.get("name", path.stem), data.get("table"))
        s.robot_config = data.get("robot", {})
        for c in data.get("cubes", []):
            s.add_cube(c.get("name"), c["x"], c["y"], c.get("color", "red"), c.get("size", 40))
        for z in data.get("zones", []):
            s.zones.append(Zone(z["name"], z["x"], z["y"], z["w"], z["h"], z.get("color", "gray")))
        for z in data.get("sensors", []):
            s.sensors.append(Sensor(z["name"], z["x"], z["y"], z["w"], z["h"]))
        for z in data.get("obstacles", []):
            s.obstacles.append(Obstacle(z.get("name", "препятствие"), z["x"], z["y"], z["w"], z["h"]))
        c = data.get("conveyor")
        if c:
            s.conveyor = Conveyor(c.get("name", "конвейер"), c["x"], c["y"], c["w"], c["h"],
                                  c.get("speed", 50), c.get("direction", "+x"), c.get("spawn"))
        return s

    def save(self, path):
        """Записва сцената (с текущите позиции на кубчетата) в JSON файл."""
        rect = lambda r: {"name": r.name, "x": r.x, "y": r.y, "w": r.w, "h": r.h}
        data = {
            "name": self.name, "table": self.table, "robot": self.robot_config,
            "cubes": [{"name": c.name, "x": round(c.x, 1), "y": round(c.y, 1), "color": c.color, "size": c.size} for c in self.cubes],
            "zones": [dict(rect(z), color=z.color) for z in self.zones],
            "sensors": [rect(z) for z in self.sensors],
            "obstacles": [rect(z) for z in self.obstacles],
        }
        if self.conveyor:
            cv = self.conveyor
            data["conveyor"] = dict(rect(cv), speed=cv.speed, direction="+x" if cv.direction > 0 else "-x", spawn=cv.spawn)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ---------- обекти ----------
    def add_cube(self, name, x, y, color="red", size=40):
        """Добавя кубче в сцената и го връща."""
        if name is None:
            name = f"c{len(self.cubes) + 1}"
        if color not in COLORS:
            raise RobotError(f"Непознат цвят {color!r}. Възможни: {', '.join(COLORS)}")
        cube = Cube(name, x, y, color, size)
        self.cubes.append(cube)
        if self.view:
            self.view.add_cube(cube)
        return cube

    def add_zone(self, name, x, y, w, h, color="gray"):
        z = Zone(name, x, y, w, h, color)
        self.zones.append(z)
        if self.view:
            self.view.add_rect(z)
        return z

    def add_obstacle(self, name, x, y, w, h):
        o = Obstacle(name, x, y, w, h)
        self.obstacles.append(o)
        if self.view:
            self.view.add_rect(o)
        return o

    def remove_cube(self, cube):
        """Премахва кубче от сцената (например брак, изхвърлен от клетката)."""
        cube = self.cube(cube) if isinstance(cube, str) else cube
        self.cubes.remove(cube)
        if self.view:
            self.view.remove_cube(cube)

    def cube(self, name):
        """Връща кубчето с даденото име."""
        for c in self.cubes:
            if c.name == name:
                return c
        raise RobotError(f"Няма кубче с име {name!r}")

    def zone(self, name):
        """Връща зоната с даденото име."""
        for z in self.zones:
            if z.name == name:
                return z
        raise RobotError(f"Няма зона с име {name!r}")

    def cubes_in(self, zone_name):
        """Списък с кубчетата, чийто център е в зоната."""
        z = self.zone(zone_name)
        return [c for c in self.cubes if c.held_by is None and z.contains(c.x, c.y)]

    def sensor(self, name):
        """True, ако в зоната на сензора има кубче."""
        for s in self.sensors:
            if s.name == name:
                return any(c.held_by is None and s.contains(c.x, c.y) for c in self.cubes)
        raise RobotError(f"Няма сензор с име {name!r}")

    def top_cube_at(self, x, y):
        """Най-горното свободно кубче в точката (x, y) или None."""
        found = [c for c in self.cubes if c.held_by is None and c.covers(x, y)]
        return max(found, key=lambda c: c.level) if found else None

    @property
    def camera(self):
        """Виртуална камера, която гледа масата отгоре."""
        if self._camera is None:
            from .camera import Camera
            self._camera = Camera(self)
        return self._camera

    # ---------- време ----------
    def step(self, dt):
        """Придвижва сцената с dt секунди (конвейер, поява на детайли)."""
        self.time += dt
        cv = self.conveyor
        if cv and cv.running:
            self._move_conveyor(cv, dt)

    def _move_conveyor(self, cv, dt):
        x0, x1, y0, y1 = cv.bounds
        on = [c for c in self.cubes if c.held_by is None and c.level == 0 and cv.contains(c.x, c.y)]
        on.sort(key=lambda c: -c.x * cv.direction)  # първо най-предните
        placed = []
        for c in on:
            h = c.size / 2
            target = c.x + cv.direction * cv.speed * dt
            end = x1 - h if cv.direction > 0 else x0 + h
            target = min(target, end) if cv.direction > 0 else max(target, end)
            for p in placed:  # не застъпва кубчето пред себе си
                if abs(p.y - c.y) < (p.size + c.size) / 2:
                    gap = (p.size + c.size) / 2
                    if cv.direction > 0 and p.x > c.x:
                        target = min(target, p.x - gap)
                    elif cv.direction < 0 and p.x < c.x:
                        target = max(target, p.x + gap)
            c.x = target if (target - c.x) * cv.direction >= 0 else c.x
            placed.append(c)
        if cv.spawn:
            cv._timer += dt
            if cv._timer >= cv.spawn.get("interval", 5):
                size = cv.spawn.get("size", 40)
                sx = (x0 + size / 2) if cv.direction > 0 else (x1 - size / 2)
                free = all(not (abs(c.x - sx) < size and abs(c.y - cv.y) < size) for c in self.cubes)
                limit = cv.spawn.get("count", 0)
                if free and (not limit or cv._count < limit):
                    cv._timer = 0.0
                    cv._count += 1
                    color = cv._rng.choice(cv.spawn.get("colors", ["red", "green", "blue"]))
                    self.add_cube(f"p{cv._count}", sx, cv.y, color, size)
