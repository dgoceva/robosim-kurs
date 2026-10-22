"""Модул traj: профили на скоростта и траектории за учебния робот.

Профилите връщат времената t и изминатата част s от пътя (от 0 до 1).
Траекториите превръщат s в ъгли на ставите за robot.follow(ъгли, dt).
"""
import numpy as np
from kin2 import best_ik


def trapezoid(dist, v_max, a_max, dt=0.02):
    """Трапецовиден профил за път dist. Връща t, s (0..1), v, a."""
    dist = abs(float(dist))
    if dist == 0:
        return np.zeros(1), np.zeros(1), np.zeros(1), np.zeros(1)
    t_acc = v_max / a_max
    if a_max * t_acc ** 2 > dist:           # къс ход: триъгълен профил
        t_acc = np.sqrt(dist / a_max)
        v_max = a_max * t_acc
    t_const = (dist - a_max * t_acc ** 2) / v_max
    T = 2 * t_acc + t_const
    t = np.linspace(0, T, max(1, int(np.ceil(T / dt))) + 1)
    t1, t2 = t_acc, t_acc + t_const
    pos = np.where(t < t1, 0.5 * a_max * t ** 2,
          np.where(t < t2, 0.5 * a_max * t1 ** 2 + v_max * (t - t1),
                   dist - 0.5 * a_max * (T - t) ** 2))
    v = np.where(t < t1, a_max * t, np.where(t < t2, v_max, a_max * (T - t)))
    a = np.where(t < t1, a_max, np.where(t < t2, 0.0, -a_max))
    return t, pos / dist, v, a


def cubic(T, dt=0.02):
    """Полином от 3 степен: нулева скорост в началото и в края."""
    t = np.linspace(0, T, max(1, int(np.ceil(T / dt))) + 1)
    u = t / T
    return t, 3 * u ** 2 - 2 * u ** 3


def quintic(T, dt=0.02):
    """Полином от 5 степен: нулеви скорост и ускорение в началото и в края."""
    t = np.linspace(0, T, max(1, int(np.ceil(T / dt))) + 1)
    u = t / T
    return t, 10 * u ** 3 - 15 * u ** 4 + 6 * u ** 5


def joint_path(q_start, q_end, s):
    """Ставна траектория: ъглите се менят пропорционално на s."""
    q0, q1 = np.asarray(q_start, float), np.asarray(q_end, float)
    return q0 + (q1 - q0) * np.asarray(s)[:, None]


def line_path(p_start, p_end, s, current=(0.0, 90.0)):
    """Линейна траектория: точки по правата, превърнати в ъгли с best_ik."""
    p0, p1 = np.asarray(p_start, float), np.asarray(p_end, float)
    Q, q = [], current
    for si in s:
        q = best_ik(*(p0 + (p1 - p0) * si), q)
        if q is None:
            raise ValueError(f"недостижима точка при s = {si:.2f}")
        Q.append(q)
    return np.array(Q)


def joint_speeds(Q, dt):
    """Скорости на ставите в °/s между съседните точки (масив N-1 x 2)."""
    return np.abs(np.diff(np.asarray(Q), axis=0)) / dt
