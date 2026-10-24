"""Учебен симулатор на робот за курса „Програмиране на роботизирани системи с Python“.

    from robosim import Robot
    robot = Robot("default.json")
    robot.move_to(400, 200)
"""
from .scene import Scene, RobotError, Cube, Zone, Sensor, Obstacle, Conveyor, COLORS
from .robot import Robot
from . import kinematics

__version__ = "1.0.2"
__all__ = ["Robot", "Scene", "RobotError", "Cube", "Zone", "Sensor", "Obstacle", "Conveyor", "COLORS", "kinematics"]
