from functools import partial
import mgear.menu
from mgear import shifter
from . import gui, guidesTemplates, mocapTools, gameTools, io
from . import guideTemplateExplorer


def install():
    """Install Shifter submenu
    """
    commands = (
        ("Guide UI", gui.Guide_UI),
        ("-----", None),
        ("Build from Selection", gui.Guide_UI.buildFromSelection),
        ("Build From Guide Template File", partial(io.build_from_file, None)),
        ("-----", None),
        ("Import Guide Template", partial(io.import_guide_template, None)),
        ("Export Guide Template", partial(io.export_guide_template,
                                          None,
                                          None)),
        ("Guide Template Explorer",
         guideTemplateExplorer.open_guide_template_explorer),
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
