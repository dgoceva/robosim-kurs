"""Модул kin2: кинематика на плосък манипулатор с две звена.

Ъглите са в градуси, дължините в mm. q1 е спрямо оста X,
q2 е спрямо продължението на първото звено.
"""
import numpy as np

L1, L2 = 350.0, 300.0
LIMITS = ((-170.0, 170.0), (-150.0, 150.0))


def fk(q1, q2, l1=L1, l2=L2):
    """Права кинематика: (q1, q2) -> (лакът, край) като масиви."""
    a1 = np.radians(q1)
    a12 = a1 + np.radians(q2)
    elbow = np.array([l1 * np.cos(a1), l1 * np.sin(a1)])
    tip = elbow + np.array([l2 * np.cos(a12), l2 * np.sin(a12)])
    return elbow, tip


def ik(x, y, elbow="right", l1=L1, l2=L2):
    """Обратна кинематика: (x, y) -> (q1, q2) или None, ако е недостижима."""
    c = (x * x + y * y - l1 * l1 - l2 * l2) / (2 * l1 * l2)
    if abs(c) > 1:
        return None
    s = np.sqrt(1 - c * c)
    if elbow == "left":
        s = -s
    q2 = np.arctan2(s, c)
    q1 = np.arctan2(y, x) - np.arctan2(l2 * s, l1 + l2 * c)
    q1 = (np.degrees(q1) + 180) % 360 - 180
    return q1, np.degrees(q2)


def in_limits(q):
    return all(lo <= a <= hi for a, (lo, hi) in zip(q, LIMITS))


def best_ik(x, y, current=(0.0, 90.0)):
    """Решението в границите, най-близко до текущите ъгли, или None."""
    sols = []
    for e in ("right", "left"):
        q = ik(x, y, e)
        if q is not None and in_limits(q):
            sols.append(q)
    if not sols:
        return None
    return min(sols, key=lambda q: abs(q[0] - current[0]) + abs(q[1] - current[1]))
