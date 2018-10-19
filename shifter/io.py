# Shifter guides IO utility functions

import json
import pymel.core as pm
from mgear import shifter


def get_guide_template_dict(guide_node):
    """Get the guide template dictionary from a guide node.

    Args:
        guide_node (PyNode): The guide node to start the parsing from.

    Returns:
        dict: the parsed guide dictionary
    """
    rig = shifter.Rig()
    rig.guide.setFromHierarchy(guide_node)
    return rig.guide.get_guide_template_dict()


def get_template_from_selection():
    """Get the guide template dictionary from a selected guide element.

    Returns:
        dict: the parsed guide dictionary
    """
    return get_guide_template_dict(pm.selected()[0])


def _get_file(write=False):
    """Convinience function to retrive the guide file in at export or import.

    Args:
        write (bool, optional): If true, will set the dialog to write.
            If false will se the dialog to read.

    Returns:
        str: the file path
    """
    if write:
        mode = 0
    else:
        mode = 1
    startDir = pm.workspace(q=True, rootDirectory=True)
    filePath = pm.fileDialog2(
        dialogStyle=2,
        startingDirectory=startDir,
        fileMode=mode,
        fileFilter='Shifter Guide Template .sgt (*%s)' % ".sgt")

    if not filePath:
        raise
    if not isinstance(filePath, basestring):
        filePath = filePath[0]

    return filePath


def export_guide_template(filePath=None):
    """Export the guide templata to a file

    Args:
        filePath (str, optional): Path to save the file
    """
    conf = get_template_from_selection()

    data_string = json.dumps(conf, indent=4, sort_keys=True)
    if not filePath:
        filePath = _get_file(True)

    with open(filePath, 'w') as f:
        f.write(data_string)


def _import_guide_template(filePath=None):
    """Summary

    Args:
        filePath (str, optional): Path to the template file to import

    Returns:
        dict: the parsed guide dictionary
    """
    if not filePath:
        filePath = _get_file()

    with open(filePath, 'r') as f:
        conf = json.load(f)

    return conf


def import_partial_guide(filePath=None, partial=None, initParent=None):
    """Import a partial part of a template

    Args:
        filePath (str, optional): Path to the template file to import
        partial (str or list of str, optional): If Partial starting
            component is defined, will try to add the guide to a selected
            guide part of an existing guide.
        initParent (dagNode, optional): Initial parent. If None, will
            create a new initial heirarchy
    """
    conf = _import_guide_template(filePath)
    rig = shifter.Rig()
    rig.guide.set_from_dict(conf)
    rig.guide.draw_guide(partial, initParent)


def import_guide_template(filePath=None):
    """Import a guide template

    Args:
        filePath (str, optional): Path to the template file to import
    """
    import_partial_guide(filePath)


def build_from_file(filePath=None):
    """Build a rig from a template file.
    The rig will be build from a previously exported guide template, without
    creating the guide in the scene.

    Args:
        filePath (None, optional): Guide template file path

    """
    conf = _import_guide_template(filePath)
    rig = shifter.Rig()
    rig.buildFromDict(conf)
