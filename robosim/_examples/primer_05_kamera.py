# Пример 5: виртуалната камера намира червените кубчета
import numpy as np
import matplotlib.pyplot as plt
from robosim import Robot

robot = Robot("sorting.json", show=False)    # без прозорец на робота
camera = robot.scene.camera

img = camera.capture()                       # масив (височина, ширина, 3), RGB
print("Размер на изображението:", img.shape)

# маска: пиксели, които са "червени"
r, g, b = img[:, :, 0].astype(int), img[:, :, 1].astype(int), img[:, :, 2].astype(int)
mask = (r > 180) & (g < 100) & (b < 100)

# средата на всички червени пиксели (засега общо за всички червени кубчета)
vs, us = np.nonzero(mask)
print("Червени пиксели:", len(us))
u, v = us.mean(), vs.mean()
x, y = camera.pixel_to_mm(u, v)
print(f"Среден център на червеното: пиксел ({u:.0f}, {v:.0f}) -> ({x:.1f}, {y:.1f}) mm")

plt.figure("Камера")
plt.subplot(1, 2, 1); plt.imshow(img); plt.title("Снимка")
plt.subplot(1, 2, 2); plt.imshow(mask, cmap="gray"); plt.title("Червени пиксели")
plt.show()
