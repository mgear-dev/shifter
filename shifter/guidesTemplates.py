import os

import pymel.core as pm
from mgear.shifter import component, gui, guide


def updateGuide(*args):
    """Update the guide rig"""
    if pm.selected():
        rgGuide = guide.Rig()
        rgGuide.update(pm.selected()[0])
    else:
        pm.displayWarning("Please select the guide top node")


def bipedGuide(*args):
    """Import the basic biped template"""
    path = os.path.dirname(component.__file__)
    pm.importFile(os.path.join(path, "_templates", "biped_guide.ma"))


def quadrupedGuide(*args):
    """Import the basic quadruped template"""
    path = os.path.dirname(component.__file__)
    pm.importFile(os.path.join(path, "_templates", "quadruped.ma"))
