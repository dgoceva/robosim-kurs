"""Кинематика на плосък манипулатор с две звена (изглед отгоре, тип SCARA).

Ъглите са в градуси, дължините в милиметри.
q1 е ъгълът на първото звено спрямо оста X.
q2 е ъгълът на второто звено спрямо продължението на първото.
"""
import math


def forward(links, angles, base=(0.0, 0.0)):
    """Права кинематика.

    Връща списък от точки: основата, всяка става и края на последното звено.
    Пример: forward([350, 300], [0, 90]) -> [(0, 0), (350, 0), (350, 300)]
    """
    x, y = float(base[0]), float(base[1])
    points = [(x, y)]
    angle = 0.0
    for length, q in zip(links, angles):
        angle += math.radians(q)
        x += length * math.cos(angle)
        y += length * math.sin(angle)
        points.append((x, y))
    return points


def inverse(links, x, y, elbow="right", base=(0.0, 0.0)):
    """Обратна кинематика за две звена.

    Връща (q1, q2) в градуси или None, ако точката е извън обхвата.
    elbow="right" дава q2 > 0, elbow="left" дава q2 < 0.
    """
    l1, l2 = links[0], links[1]
    dx, dy = x - base[0], y - base[1]
    d2 = dx * dx + dy * dy
    c = (d2 - l1 * l1 - l2 * l2) / (2 * l1 * l2)
    if c > 1 + 1e-9 or c < -1 - 1e-9:
        return None
    c = max(-1.0, min(1.0, c))
    s = math.sqrt(1 - c * c)
    if elbow == "left":
        s = -s
    q2 = math.atan2(s, c)
    q1 = math.atan2(dy, dx) - math.atan2(l2 * s, l1 + l2 * c)
    return normalize(math.degrees(q1)), normalize(math.degrees(q2))


def normalize(angle):
    """Привежда ъгъл в градуси в интервала (-180, 180]."""
    a = (angle + 180.0) % 360.0 - 180.0
    if a == -180.0:
        a = 180.0
    return a


def reach(links):
    """Минимален и максимален обхват на манипулатора."""
    return abs(links[0] - links[1]), links[0] + links[1]
