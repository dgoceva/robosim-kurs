"""Модул frames: трансформации в равнината с хомогенни матрици 3 x 3."""
import numpy as np


def rot(deg):
    """Матрица на ротация 2 x 2 на ъгъл deg градуса."""
    a = np.radians(deg)
    return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])


def T(x, y, deg):
    """Хомогенна матрица: ротация на deg градуса, после транслация (x, y)."""
    M = np.eye(3)
    M[:2, :2] = rot(deg)
    M[:2, 2] = [x, y]
    return M


def apply(M, pts):
    """Прилага M към точка (2,) или към масив от точки (N, 2)."""
    pts = np.asarray(pts, dtype=float)
    P = np.atleast_2d(pts)
    H = np.column_stack([P, np.ones(len(P))])
    R = (H @ M.T)[:, :2]
    return R[0] if pts.ndim == 1 else R


def inv_T(M):
    """Обратна трансформация: R -> R.T, t -> -R.T @ t."""
    R, t = M[:2, :2], M[:2, 2]
    Mi = np.eye(3)
    Mi[:2, :2] = R.T
    Mi[:2, 2] = -R.T @ t
    return Mi


def pose(M):
    """(x, y, ъгъл в градуси) от хомогенна матрица."""
    return M[0, 2], M[1, 2], np.degrees(np.arctan2(M[1, 0], M[0, 0]))
