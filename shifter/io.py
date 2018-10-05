# Shifter guides IO utility functions

import pymel.core as pm
from mgear import shifter

def get_guide_template_dict(guide_node):
    rig = shifter.Rig()
    rig.guide.setFromHierarchy(guide_node)
    return rig.guide.get_guide_template_dict()

def get_template_from_selection():
    return get_guide_template_dict(pm.selected()[0])


def export_guide_template(path=None):
    pass

def import_guide_template(path=None):
    pass

def import_partial(comp, parent_guide=None):
    """Import a partial part of a template

    Args:
        comp (str): Name of the componets to be imported
        parent_guide (None, optional): Parent of the new components imported.
            If None, a new guide root will be created.
    """
    pass


def build_from_file(path=None):
    """Build a rig from a template file.
    The rig will be build from a previously exported guide template, without
    creating the guide in the scene.

    Args:
        path (None, optional): Guide template file path

    """
    pass