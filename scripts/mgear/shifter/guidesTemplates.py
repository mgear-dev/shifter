import pymel.core as pm
from mgear.shifter import guide


def updateGuide(*args):
    """Update the guide rig"""
    if pm.selected():
        rgGuide = guide.Rig()
        rgGuide.update(pm.selected()[0])
    else:
        pm.displayWarning("Please select the guide top node")


# guide differences checkers
##################################

# WIP
def guide_diff(guide,
               master_guide,
               check_guide_component_diff=True,
               check_guide_transform_diff=True,
               check_guide_root_settings_diff=True,
               check_component_settings_diff=True,
               check_guide_custom_step_diff=True):
    """Compare a guide agaisnt a master guide. This check will return false,
    if the guide is missing anything or have a missmatch with the master guide.
    Also will print a complete report.

    Returns:
        bool: True if the test pass
    """
    gdiff = {}
    if check_guide_component_diff:
        comp_diff = guide_component_diff(guide, master_guide)
        if comp_diff:
            gdiff["components_diff"] = comp_diff

    if check_guide_transform_diff:
        not_match_tra, root_tra = guide_transform_diff(guide, master_guide)
        if not_match_tra:
            gdiff["component_transform_diff"] = not_match_tra
        gdiff["root_transform_match"] = root_tra

    if check_guide_root_settings_diff:
        root_sett_diff = guide_root_settings_diff(guide, master_guide)
        if root_sett_diff:
            gdiff["root_settings_diff"] = root_sett_diff

    if check_component_settings_diff:
        comp_sett_diff = guide_component_settings_diff(guide, master_guide)
        if comp_sett_diff:
            gdiff["component_settings_diff"] = comp_sett_diff

    return gdiff


def guide_component_diff(guideA, guideB):
    """Components matching report.

    Compare guide "A" components, against guide "B" components. Considering A
    the guide that we want to check and B the guide used as a checker.

    Return a dictionary with marching components, missing components and
    extra components.

    dictionary keys = match, miss, extra

    Returns:
        dict: Component matching report in dict format.
    """
    compA = guideA["components_list"]
    compB = guideB["components_list"]

    match = [c for c in compA if c in compB]
    miss = list(set(compB).difference(compA))
    extra = list(set(compA).difference(compB))

    diff_dict = {"match": match, "miss": miss, "extra": extra}

    return diff_dict


def guide_transform_diff(guideA, guideB, pos=False):
    """Return guide transform differences

    Returns:
        TYPE: Description
    """
    # get matching components
    match_comp = guide_component_diff(guideA, guideB)["match"]

    # check matching components transform
    not_match_tra = component_transform_diff(guideA,
                                             guideB,
                                             match_comp,
                                             componentB=None,
                                             pos=pos)

    # check root position
    root_tra_A = guideA["guide_root"]['tra']
    root_tra_B = guideB["guide_root"]['tra']
    if root_tra_A != root_tra_B:
        root_tra_match = False
    else:
        root_tra_match = True

    return not_match_tra, root_tra_match


def guide_root_settings_diff(guideA, guideB):

    pvA = guideA["guide_root"]['param_values']
    pvB = guideB["guide_root"]['param_values']

    return param_diff(pvA, pvB)


def guide_component_settings_diff(guideA, guideB, comp_diff=None):
    """Summary

    Args:
        guideA (TYPE): Description
        guideB (TYPE): Description
        comp_diff (None, optional): Description

    Returns:
        list: the not matching settings dict and the missing comonent list
    """
    if not comp_diff:
        comp_diff = guide_component_diff(guideA, guideB)

    match = comp_diff["match"]
    miss = comp_diff["miss"]
    comp_sett_diff = component_settings_diff(guideA, guideB, match)

    return [comp_sett_diff, miss]


def guide_custom_step_diff(guideA, guideB):
    # same custom steps
    # same custom steps with diff path
    # custom step order
    return


# component difference checkers
##################################


def componentAB_type_diff(guideA, guideB, componentA, componentB=None):
    """Return list of not matching types components and the types found

    Usually componentA list and componentB list is the same list. But keeping
    this separated we can check an arbitrary list with not matching names.
    In this case the componentB list should match the order and number of
    componentA types

    Args:
        guideA (dict): Guide dictionary template
        guideB (dict): Guide dictionary template
        componentA (str or str list): Names of the components to check
        componentB (None, optional): If None will use the component A list in
            both guides

    Returns:
        list: Not matching components
    """
    componentA, componentB = to_list_AB(componentA, componentB)

    not_match = []
    for ca, cb in zip(componentA, componentB):
        typeA = guideA["components_dict"][ca]['param_values']['comp_type']
        typeB = guideB["components_dict"][cb]['param_values']['comp_type']
        if typeA != typeB:
            not_match.append([ca, cb, typeA, typeB])
    return not_match


def component_type_diff(guideA, guideB, component):
    """Return Dictionary with not maching components and types

    Args:
        guideA (dict): Guide dictionary template
        guideB (dict): Guide dictionary template
        componentA (str or str list): Names of the components to check

    Returns:
        dict: Not matching components
    """
    not_match = componentAB_type_diff(guideA, guideB, component)
    not_match_dict = {}
    for c in not_match:
        not_match_dict[c[0]] = [c[2], c[3]]

    return not_match_dict

# TODO: need to round the precision to check the transformation.
# Maya is not very exact :(


def component_transform_diff(guideA,
                             guideB,
                             componentA,
                             componentB=None,
                             pos=False):
    """Return a dictionary with the not matching transform and blades

    If the position information is miss or missmatch the report
    will inform

    Usually componentA list and componentB list is the same list. But keeping
    this separated we can check an arbitrary list with not matching names.
    In this case the componentB list should match the order and number of
    componentA types

    Args:
        guideA (dict): Guide dictionary template
        guideB (dict): Guide dictionary template
        componentA (str or str list): Names of the components to check
        componentB (None, optional): If None will use the component A list in
            both guides
        pos (bool, optional): If True will check only the position not the full
            transformation of the componet locators

    Returns:
        dict: Not matching components transform
    """
    if pos:
        check = "pos"
    else:
        check = "tra"

    componentA, componentB = to_list_AB(componentA, componentB)
    not_match_dict = {}
    for ca, cb in zip(componentA, componentB):
        # check transform
        traA_dict = guideA["components_dict"][ca][check]
        traB_dict = guideB["components_dict"][cb][check]
        not_found_tra, not_match_tra = dict_diff(traA_dict, traB_dict)

        # check blades
        bladesA = guideA["components_dict"][ca]['blade']
        bladesB = guideB["components_dict"][cb]['blade']
        not_found_blades, not_match_blades = dict_diff(bladesA, bladesB)

        if (not_found_tra
                or not_match_tra
                or not_found_blades
                or not_match_blades):
            not_match_dict[ca] = {"not_found_tra": not_found_tra,
                                  "not_match_tra": not_match_tra,
                                  "not_found_blades": not_found_blades,
                                  "not_match_blades": not_match_blades}

    return not_match_dict


def component_settings_diff(guideA, guideB, componentA, componentB=None):
    """Return list of not matching types components and the types found

    Usually componentA list and componentB list is the same list. But keeping
    this separated we can check an arbitrary list with not matching names.
    In this case the componentB list should match the order and number of
    componentA types

    Args:
        guideA (dict): Guide dictionary template
        guideB (dict): Guide dictionary template
        componentA (str or str list): Names of the components to check
        componentB (None, optional): If None will use the component A list in
            both guides

    Returns:
        dict: Not matching components settings
    """
    componentA, componentB = to_list_AB(componentA, componentB)
    not_match = {}
    for ca, cb in zip(componentA, componentB):
        pvA = guideA["components_dict"][ca]['param_values']
        pvB = guideB["components_dict"][cb]['param_values']
        cp_not_match = param_diff(pvA, pvB)
        if cp_not_match:
            not_match[ca] = cp_not_match

    return not_match


# helper functions
def to_list(item):
    if not isinstance(item, list):
        return list(item)
    else:
        return item


def to_list_AB(componentA, componentB):
    componentA = to_list(componentA)
    if not componentB:
        componentB = componentA
    componentB = to_list(componentB)

    return componentA, componentB


def param_diff(pvA, pvB):
    """Compare the parameter differences

    Args:
        pvA (dict): parameter values dictionary
        pvB (dict): parameter values dictionary

    Returns:
        dict: Not matching settings
    """

    not_match = {}
    not_found_param, not_match_param = dict_diff(pvA, pvB)
    if not_found_param or not_match_param:
        not_match = {"not_found_param": not_found_param,
                     "not_match_param": not_match_param}
    return not_match


def dict_diff(dictA, dictB):
    """Return key and value differences from 2 given dictionaries

    Args:
        dictA (dict): Dictionary A
        dictB (dict): Dictionary B

    Returns:
        list, lit: Not found keys, not matching values
    """
    not_found_key = []
    not_match_value = []
    for k in dictA.keys():
        if k in dictB.keys():
            if dictA[k] != dictB[k]:
                not_match_value.append([k, dictA[k], dictB[k]])
        else:
            not_found_key.append(k)

    return not_found_key, not_match_value
