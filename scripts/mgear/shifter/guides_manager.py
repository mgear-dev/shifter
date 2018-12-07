
import os

from functools import partial

# pymel
import pymel.core as pm

import mgear
from mgear.core import pyqt
from mgear import shifter


##############################
# Helper Functions
##############################

def draw_comp(comp_type, *args):
    """Draw a new component of a given name

    Args:
        comp_type (str): Name of the component to draw
        *args: Description
    """
    guide = shifter.guide.Rig()

    if pm.selected():
        parent = pm.selected()[0]
    else:
        parent = None

    guide.drawNewComponent(parent, comp_type)


def duplicate(sym, *args):
    """Duplicate a component by drawing a new one and setting the same
    properties values

    Args:
        sym (bool): If True, will create a symmetrical component
        *args: None

    """
    oSel = pm.selected()
    if oSel:
        root = oSel[0]
        guide = shifter.guide.Rig()
        guide.duplicate(root, sym)
    else:
        mgear.log("Select one component root to edit properties",
                  mgear.sev_error)


def build_from_selection(*args):
    """Build rig from current selection

    Args:
        *args: None
    """
    shifter.log_window()
    rg = shifter.Rig()
    rg.buildFromSelection()


def inspect_settings(*args):
    """Open the component or root setting UI.

    Args:
        *args: None

    Returns:
        None: None if nothing is selected
    """
    oSel = pm.selected()
    if oSel:
        root = oSel[0]
    else:
        pm.displayWarning(
            "please select one object from the componenet guide")
        return

    comp_type = False
    guide_root = False
    while root:
        if pm.attributeQuery("comp_type", node=root, ex=True):
            comp_type = root.attr("comp_type").get()
            break
        elif pm.attributeQuery("ismodel", node=root, ex=True):
            guide_root = root
            break
        root = root.getParent()
        pm.select(root)

    if comp_type:
        guide = shifter.importComponentGuide(comp_type)
        pyqt.showDialog(guide.componentSettings)

    elif guide_root:
        module_name = "mgear.shifter.guide"
        guide = __import__(module_name, globals(), locals(), ["*"], -1)
        pyqt.showDialog(guide.guideSettings)

    else:
        pm.displayError(
            "The selected object is not part of component guide")


def extract_controls(*args):
    """Extract the selected controls from the rig to use it in the new build

    The controls shapes are stored under the controller_org group.
    The controls are renamed witht "_controlBuffer" suffix

    Args:
        *args: None
    """
    oSel = pm.selected()

    try:
        cGrp = pm.PyNode("controllers_org")
    except TypeError:
        cGrp = False
        mgear.log(
            "Not controller group in the scene or the group is not unique",
            mgear.sev_error)
    for x in oSel:
        try:
            old = pm.PyNode(cGrp.name() + "|" +
                            x.name().split("|")[-1] + "_controlBuffer")
            pm.delete(old)
        except TypeError:
            pass
        new = pm.duplicate(x)[0]
        pm.parent(new, cGrp, a=True)
        pm.rename(new, x.name() + "_controlBuffer")
        toDel = new.getChildren(type="transform")
        pm.delete(toDel)
        try:
            pm.sets("rig_controllers_grp", remove=new)
        except TypeError:
            pass
