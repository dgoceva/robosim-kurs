"""Визуализация на сцената с Matplotlib (изглед отгоре)."""
import sys

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

from .scene import COLORS, Zone, Sensor, Obstacle, Conveyor

ZONE_FILL = {"red": "#f6d0d0", "green": "#cfeccf", "blue": "#d2dcf7", "yellow": "#f8ecc0",
             "orange": "#fbe0c4", "purple": "#e6d3ee", "gray": "#e3e3e3", "black": "#cccccc", "white": "#f7f7f7"}


def _rgb(name):
    r, g, b = COLORS.get(name, (128, 128, 128))
    return (r / 255, g / 255, b / 255)


class View:
    """Прозорец с изглед отгоре на масата и роботите."""

    def __init__(self, scene):
        self.scene = scene
        self.closed = False
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(9, 8))
        try:
            self.fig.canvas.manager.set_window_title("Учебен симулатор на робот")
        except Exception:
            pass
        self.fig.canvas.mpl_connect("close_event", self._on_close)
        t = scene.table
        ax = self.ax
        ax.set_xlim(t["xmin"], t["xmax"])
        ax.set_ylim(t["ymin"], t["ymax"])
        ax.set_aspect("equal")
        ax.set_facecolor("#fafafa")
        ax.grid(True, color="#e6e6e6", linewidth=0.6)
        ax.set_xlabel("X, mm")
        ax.set_ylabel("Y, mm")
        ax.set_title(scene.name, fontsize=13)
        self.cube_patches = {}
        self.robot_artists = {}
        self.fig.subplots_adjust(left=0.1, right=0.97, top=0.94, bottom=0.16)
        self.info = self.fig.text(0.1, 0.015, "", va="bottom", ha="left", fontsize=9, family="monospace")
        if scene.conveyor:
            self.add_rect(scene.conveyor)
        for r in scene.zones + scene.sensors + scene.obstacles:
            self.add_rect(r)
        for c in scene.cubes:
            self.add_cube(c)

    def _on_close(self, event):
        self.closed = True

    # ---------- статични обекти ----------
    def add_rect(self, r):
        x0, x1, y0, y1 = r.bounds
        ax = self.ax
        if isinstance(r, Conveyor):
            ax.add_patch(Rectangle((x0, y0), r.w, r.h, fc="#d0d4d8", ec="#7a8288", lw=1.2, zorder=1))
            step = 40
            x = x0 + step
            while x < x1:
                ax.plot([x, x], [y0, y1], color="#b8bec4", lw=0.8, zorder=1)
                x += step
            arrow = "→" if r.direction > 0 else "←"
            ax.text(r.x, y1 + 12, f"{r.name} {arrow} {r.speed:g} mm/s", ha="center", va="bottom", fontsize=8, color="#555555")
        elif isinstance(r, Zone):
            ax.add_patch(Rectangle((x0, y0), r.w, r.h, fc=ZONE_FILL.get(r.color, "#e3e3e3"), ec=_rgb(r.color), lw=1.2, zorder=1))
            edge = "#888888" if r.color in ("white", "gray") else _rgb(r.color)
            ax.patches[-1].set_edgecolor(edge)
            ax.text(r.x, y1 + 8, r.name, ha="center", va="bottom", fontsize=8, color=edge)
        elif isinstance(r, Sensor):
            ax.add_patch(Rectangle((x0, y0), r.w, r.h, fc="none", ec="#d4a017", lw=1.5, ls="--", zorder=3))
            ax.text(r.x, y0 - 8, "сензор " + r.name, ha="center", va="top", fontsize=8, color="#a07800")
        elif isinstance(r, Obstacle):
            ax.add_patch(Rectangle((x0, y0), r.w, r.h, fc="#5b6770", ec="#2f3a40", lw=1.2, hatch="//", zorder=2))
            ax.text(r.x, r.y, r.name, ha="center", va="center", fontsize=8, color="white", zorder=3)

    # ---------- кубчета ----------
    def add_cube(self, c):
        h = c.size / 2
        p = Rectangle((c.x - h, c.y - h), c.size, c.size, fc=_rgb(c.color), ec="#222222", lw=1, zorder=5)
        self.ax.add_patch(p)
        label = self.ax.text(c.x, c.y, "", ha="center", va="center", fontsize=8, color="white", weight="bold", zorder=6)
        self.cube_patches[id(c)] = (p, label)

    def remove_cube(self, c):
        p, label = self.cube_patches.pop(id(c))
        p.remove()
        label.remove()

    # ---------- роботи ----------
    def add_robot(self, robot):
        ax = self.ax
        bx, by = robot.base
        lo, hi = robot.reach
        ax.add_patch(Circle((bx, by), hi, fill=False, ls=":", ec="#9aa5ab", lw=0.8, zorder=0))
        if lo > 1:
            ax.add_patch(Circle((bx, by), lo, fill=False, ls=":", ec="#9aa5ab", lw=0.8, zorder=0))
        ax.add_patch(Circle((bx, by), 35, fc="#3a4a54", ec="#1f2a30", zorder=7))
        ax.text(bx, by, robot.name, ha="center", va="center", color="white", fontsize=8, weight="bold", zorder=8)
        arm, = ax.plot([], [], "-", color=robot.color, lw=9, solid_capstyle="round", alpha=0.85, zorder=9)
        joints, = ax.plot([], [], "o", color="#1f2a30", ms=7, zorder=10)
        grip = Circle((0, 0), 12, fc="white", ec="#1f2a30", lw=2, zorder=11)
        ax.add_patch(grip)
        self.robot_artists[id(robot)] = (arm, joints, grip)

    def add_trace(self, color):
        line, = self.ax.plot([], [], "-", color=color, lw=2, zorder=4)
        return line

    # ---------- обновяване ----------
    def update(self, pause=0.0):
        if self.closed:
            print("Прозорецът на симулатора е затворен. Програмата спира.")
            sys.exit(0)
        for c in self.scene.cubes:
            p, label = self.cube_patches[id(c)]
            h = c.size / 2
            p.set_xy((c.x - h, c.y - h))
            label.set_position((c.x, c.y))
            label.set_text(str(c.level + 1) if c.level > 0 else "")
            p.set_zorder(5 + c.level * 0.01 + (2 if c.held_by else 0))
            label.set_zorder(6 + c.level * 0.01 + (2 if c.held_by else 0))
        lines = []
        for r in self.scene.robots:
            arm, joints, grip = self.robot_artists[id(r)]
            pts = r.points
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            arm.set_data(xs, ys)
            joints.set_data(xs[:-1], ys[:-1])
            grip.center = pts[-1]
            grip.set_facecolor("#1f2a30" if r.gripper_closed else "white")
            q = ", ".join(f"{a:7.1f}°" for a in r.joints)
            state = "затворен" if r.gripper_closed else "отворен"
            held = f" ({r.holding.name})" if r.holding else ""
            lines.append(f"{r.name}: q = ({q})  X = {pts[-1][0]:7.1f}  Y = {pts[-1][1]:7.1f}  хващач: {state}{held}")
        self.info.set_text(f"t = {self.scene.time:6.2f} s\n" + "\n".join(lines))
        self.fig.canvas.draw_idle()
        if pause > 0:
            plt.pause(pause)
        else:
            self.fig.canvas.flush_events()
