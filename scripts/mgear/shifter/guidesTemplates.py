import pymel.core as pm
from mgear.shifter import guide


def updateGuide(*args):
    """Update the guide rig"""
    if pm.selected():
        rgGuide = guide.Rig()
        rgGuide.update(pm.selected()[0])
    else:
        pm.displayWarning("Please select the guide top node")
