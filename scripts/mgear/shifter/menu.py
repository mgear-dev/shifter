from functools import partial
import mgear.menu
from mgear import shifter
from . import guidesTemplates, mocapTools, gameTools, io
from . import guide_manager, guide_manager_gui


def install():
    """Install Shifter submenu
    """
    commands = (
        ("Guide Manager", guide_manager_gui.show_guide_manager),
        ("-----", None),
        ("Settings", guide_manager.inspect_settings),
        ("Duplicate", partial(guide_manager.duplicate, False)),
        ("Duplicate Sym", partial(guide_manager.duplicate, True)),
        ("Extract Controls", guide_manager.extract_controls),
        ("-----", None),
        ("Build from Selection", guide_manager.build_from_selection),
        ("Build From Guide Template File", partial(io.build_from_file, None)),
        ("-----", None),
        ("Import Guide Template", partial(io.import_guide_template, None)),
        ("Export Guide Template", partial(io.export_guide_template,
                                          None,
                                          None)),
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
