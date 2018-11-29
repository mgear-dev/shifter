import mgear.menu
from mgear import shifter
from . import gui, guidesTemplates, mocapTools, gameTools


def install():
    """Install Shifter submenu
    """
    commands = (
        ("Guide UI", gui.Guide_UI),
        ("-----", None),
        ("Build from Selection", gui.Guide_UI.buildFromSelection),
        ("-----", None),
        ("Import Biped Guide", guidesTemplates.bipedGuide),
        ("Import Quadruped Guide", guidesTemplates.quadrupedGuide),
        ("-----", None),
        (None, mocap_submenu),
        ("Game Tools", gameTools.openGameTools),
        ("-----", None),
        ("Update Guide", guidesTemplates.updateGuide),
        ("-----", None),
        ("Reload Components", shifter.reloadComponents)
    )

    mgear.menu.install("Shifter", commands)


def mocap_submenu(parent_menu_id):
    """Create the mocap submenu

    Args:
        parent_menu_id (str): Parent menu. i.e: "MayaWindow|mGear|menuItem355"
    """
    commands = (
        ("Import Mocap Skeleton Biped", mocapTools.importSkeletonBiped),
        ("Characterize Biped", mocapTools.characterizeBiped),
        ("Bake Mocap Biped", mocapTools.bakeMocap)
    )

    mgear.menu.install("Mocap", commands, parent_menu_id)
