from functools import partial
import mgear.menu
from mgear import shifter
from . import guide_template, mocap_tools, game_tools, io
from . import guide_manager, guide_manager_gui


def install():
    """Install Shifter submenu
    """
    commands = (
        ("Guide Manager", guide_manager_gui.show_guide_manager),
        ("-----", None),
        ("Settings", partial(guide_manager.inspect_settings, 0)),
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
        (None, guide_template_samples_submenu),
        ("-----", None),
        (None, mocap_submenu),
        ("Game Tools", game_tools.openGameTools),
        ("-----", None),
        ("Update Guide", guide_template.updateGuide),
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
        ("Import Mocap Skeleton Biped", mocap_tools.importSkeletonBiped),
        ("Characterize Biped", mocap_tools.characterizeBiped),
        ("Bake Mocap Biped", mocap_tools.bakeMocap)
    )

    mgear.menu.install("Mocap", commands, parent_menu_id)


def guide_template_samples_submenu(parent_menu_id):
    """Create the guide sample templates submenu

    Args:
        parent_menu_id (str): Parent menu. i.e: "MayaWindow|mGear|menuItem355"
    """
    commands = (
        ("Biped Template",
         partial(io.import_sample_template, "biped.sgt")),
        ("Quadruped Template",
         partial(io.import_sample_template, "quadruped.sgt"))
    )

    mgear.menu.install("Guide Template Samples", commands, parent_menu_id)
