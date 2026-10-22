"""Виртуална камера, която гледа масата отгоре.

Изображението е масив на NumPy с размер (височина, ширина, 3) и цветове RGB.
Внимание: OpenCV работи с ред BGR. За обработка с OpenCV използвайте
    img = cv2.cvtColor(camera.capture(), cv2.COLOR_RGB2BGR)
Роботът не се вижда на изображението.
"""
import numpy as np

from .scene import COLORS

TABLE = (232, 232, 228)
CONVEYOR = (170, 174, 178)
ZONE = {"red": (245, 215, 215), "green": (212, 236, 212), "blue": (214, 222, 246), "yellow": (247, 236, 196),
        "orange": (250, 225, 200), "purple": (230, 215, 238), "gray": (220, 220, 220), "black": (200, 200, 200), "white": (245, 245, 245)}


class Camera:
    """Камера над масата. Резолюцията се задава с ширината в пиксели."""

    def __init__(self, scene, width=640, noise=0.0, seed=0):
        self.scene = scene
        t = scene.table
        self.xmin, self.xmax, self.ymin, self.ymax = t["xmin"], t["xmax"], t["ymin"], t["ymax"]
        self.width = int(width)
        self.scale = self.width / (self.xmax - self.xmin)          # пиксела на mm
        self.height = int(round((self.ymax - self.ymin) * self.scale))
        self.noise = float(noise)
        self._rng = np.random.default_rng(seed)

    def mm_to_pixel(self, x, y):
        """Координати в mm -> пиксел (u, v). v расте надолу."""
        u = (x - self.xmin) * self.scale
        v = (self.ymax - y) * self.scale
        return int(round(u)), int(round(v))

    def pixel_to_mm(self, u, v):
        """Пиксел (u, v) -> координати (x, y) в mm."""
        return self.xmin + u / self.scale, self.ymax - v / self.scale

    def _fill(self, img, x0, x1, y0, y1, color):
        u0, v1 = self.mm_to_pixel(x0, y0)
        u1, v0 = self.mm_to_pixel(x1, y1)
        u0, u1 = max(0, u0), min(self.width, u1)
        v0, v1 = max(0, v0), min(self.height, v1)
        if u1 > u0 and v1 > v0:
            img[v0:v1, u0:u1] = color

    def capture(self):
        """Прави снимка на масата и връща изображението."""
        img = np.empty((self.height, self.width, 3), dtype=np.uint8)
        img[:] = TABLE
        s = self.scene
        if s.conveyor:
            self._fill(img, *s.conveyor.bounds, CONVEYOR)
        for z in s.zones:
            self._fill(img, *z.bounds, ZONE.get(z.color, (220, 220, 220)))
        for c in sorted(s.cubes, key=lambda c: (c.held_by is not None, c.level)):
            h = c.size / 2
            self._fill(img, c.x - h, c.x + h, c.y - h, c.y + h, COLORS[c.color])
        if self.noise > 0:
            n = self._rng.normal(0, self.noise, img.shape)
            img = np.clip(img.astype(float) + n, 0, 255).astype(np.uint8)
        return img

    def save(self, path):
        """Записва снимка във файл (например snapshot.png)."""
        import matplotlib.pyplot as plt
        plt.imsave(path, self.capture())
        return path
