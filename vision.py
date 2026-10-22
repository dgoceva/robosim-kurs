"""Модул vision: намиране на цветни детайли на изображение с OpenCV.

Изображенията от камерата на симулатора са RGB. Цветът се търси в
пространството HSV: H е тонът (0-179 в OpenCV), S е наситеността, V е яркостта.
"""
import cv2
import numpy as np

HSV_RANGES = {                 # интервали за H; червеното е около 0 и около 180
    "red": [(0, 8), (172, 179)],
    "orange": [(9, 19)],
    "yellow": [(20, 35)],
    "green": [(40, 85)],
    "blue": [(95, 130)],
    "purple": [(131, 160)],
}


def color_mask(img_rgb, color, s_min=100, v_min=80):
    """Маска (0 или 255) на пикселите с дадения цвят."""
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    mask = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in HSV_RANGES[color]:
        mask |= cv2.inRange(hsv, (lo, s_min, v_min), (hi, 255, 255))
    return mask


def find_blobs(mask, min_area=50):
    """Отделните петна в маската: център (u, v), площ и ъгъл в пиксели."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    blobs = []
    for c in contours:
        area = cv2.contourArea(c)
        m = cv2.moments(c)
        if area < min_area or m["m00"] == 0:          # m00 = 0 при петно от една линия
            continue
        _, (w, h), angle = cv2.minAreaRect(c)
        if w < h:                                   # ъгълът на дългата страна
            angle -= 90
        angle = (angle + 90) % 180 - 90             # от -90 до 90 градуса
        blobs.append({"u": m["m10"] / m["m00"] + 0.5, "v": m["m01"] / m["m00"] + 0.5,
                      "area": area, "angle": angle, "contour": c})
    return blobs


def detect(camera, colors=("red", "green", "blue"), img=None):
    """Детайлите, видими от камерата: списък от речници с цвят, x и y в mm."""
    if img is None:
        img = camera.capture()
    min_area = 0.3 * (40 * camera.scale) ** 2          # поне 30 % от детайл 40 mm
    found = []
    for color in colors:
        for b in find_blobs(color_mask(img, color), min_area):
            x, y = camera.pixel_to_mm(b["u"], b["v"])
            found.append({"color": color, "x": round(x, 1), "y": round(y, 1)})
    return found
