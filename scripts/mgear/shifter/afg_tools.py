# -*- coding: utf-8 -*-
# Standard
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import generators
from __future__ import division

import json
import math
import copy

# dcc
from maya import cmds
import pymel.core as pm
import maya.OpenMaya as OpenMaya
import pymel.core.datatypes as dt


# mgear
from mgear.shifter import io
from mgear.core import utils
from mgear.core import vector
from mgear.core import transform
from mgear.core import callbackManager
from mgear.core import string as m_string


# constants -------------------------------------------------------------------
UI_TITLE = 'Auto Fit Guide'
GUIDE_ROOT_NAME = 'guide'
SETUP_GEO_SHAPE_NAME = 'setup_C0_geoShape'

SIDE_MIRROR_INFO = {'left': 'right', 'right': 'left'}

IGNORE_GUIDE_NODES = ['global_C0_root', 'local_C0_root']

# This order is very important
DEFAULT_BIPIED_POINTS = ['hips',
                        'left_thigh',
                        'left_knee',
                        'left_ankle',
                        'left_foot',
                        'left_shoulder',
                        'left_elbow',
                        'left_hand',
                        'back',
                        'shoulders',
                        'head',
                        'right_thigh',
                        'right_knee',
                        'right_ankle',
                        'right_foot',
                        'right_shoulder',
                        'right_elbow',
                        'right_hand']

DEFAULT_BIPIED_POINTS_SET = set(DEFAULT_BIPIED_POINTS)

# Default association based off the biped template
DEFAULT_EMBED_GUIDE_ASSOCIATION = {'back': ['spine_C0_eff'],
                                   'head': ['neck_C0_head'],
                                   'hips': ['body_C0_root'],
                                   'left_ankle': ['leg_L0_ankle'],
                                   'left_elbow': ['arm_L0_elbow'],
                                   'left_foot': ['foot_L0_0_loc'],
                                   'left_hand': ['arm_L0_wrist'],
                                   'left_knee': ['leg_L0_knee'],
                                   'left_shoulder': ['shoulder_L0_tip', 'arm_L0_root'],
                                   'left_thigh': ['leg_L0_root'],
                                   'right_ankle': ['leg_R0_ankle'],
                                   'right_elbow': ['arm_R0_elbow'],
                                   'right_foot': ['foot_R0_0_loc'],
                                   'right_hand': ['arm_R0_wrist'],
                                   'right_knee': ['leg_R0_knee'],
                                   'right_shoulder': ['shoulder_R0_tip', 'arm_R0_root'],
                                   'right_thigh': ['leg_R0_root'],
                                   'shoulders': ['shoulder_R0_root', 'shoulder_L0_root']}

DEFAULT_BIPED_FEET = ['foot_L0_heel',
                      'foot_L0_inpivot',
                      'foot_L0_outpivot',
                      'foot_R0_heel',
                      'foot_R0_inpivot',
                      'foot_R0_outpivot']

try:
    INTERACTIVE_ASSOCIATION_INFO
    REVERSE_INTERACTIVE_ASSOCIATION_INFO
except NameError:
    INTERACTIVE_ASSOCIATION_INFO = {}
    REVERSE_INTERACTIVE_ASSOCIATION_INFO = {}


def clearUserAssociations():

    global INTERACTIVE_ASSOCIATION_INFO
    global REVERSE_INTERACTIVE_ASSOCIATION_INFO
    INTERACTIVE_ASSOCIATION_INFO = {}
    REVERSE_INTERACTIVE_ASSOCIATION_INFO = {}

# =============================================================================
# file i/o
# =============================================================================


def _importData(filePath):
    """Import json data

    Args:
        filePath (str): file path

    Returns:
        dict: json contents
    """
    try:
        with open(filePath, 'r') as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(e)


def _exportData(data, filePath):
    """Save out data from dict to a json file

    Args:
        data (dict): data you wish stored
        filePath (str): Have it your way, burgerking.
    """
    try:
        with open(filePath, 'w') as f:
            json.dump(data, f, sort_keys=False, indent=4)
    except Exception as e:
        print(e)

# Utils ----------------------------------------------------------------------


def dot(x, y):
    """Dot product as sum of list comprehension doing element-wise multiplication"""
    return sum(x_i * y_i for x_i, y_i in zip(x, y))


def constrainPointToVectorPlanar(point_a, point_b, driven_point, pcp=False, ws=True):
    point_a = pm.PyNode(point_a)
    point_b = pm.PyNode(point_b)
    drivent_point = pm.PyNode(driven_point)
    v = vector.linearlyInterpolate(point_a.getMatrix(ws=ws).translate,
                                   point_b.getMatrix(ws=ws).translate)
    v.normalize()

    p1 = v * dot(drivent_point.getMatrix(ws=ws).translate, v)
    # p1.normalize()
    if pcp:
        cmds.move(p1[0], p1[1], p1[2], drivent_point.name(), os=not ws, pcp=True)
    else:
        drivent_point.setTranslation(p1, ws=True)


def lookAt(driven, driver, up=[0, 1, 0]):
    # http://www.soup-dev.com/forum.html?p=post%2Faim-constraint-math-7885117
    # check if the "driven" object has parent
    try:
        parent = cmds.listRelatives(driven, pa=True, p=True)[0]
    except Exception:
        parent = None

    driven = cmds.getAttr("{}.worldMatrix".format(driven))
    driver = cmds.getAttr("{}.worldMatrix".format(driver))

    # build transformation matrix
    x = OpenMaya.MVector(driver[12] - driven[12], driver[13] - driven[13], driver[14] - driven[14])
    x.normalize()
    z = x ^ OpenMaya.MVector(-up[0], -up[1], -up[2])
    z.normalize()
    y = x ^ z
    y.normalize()
    m = OpenMaya.MMatrix()
    par_mat = [x.x, x.y, x.z, 0, y.x, y.y, y.z, 0, z.x, z.y, z.z, 0, 0, 0, 0, 1]
    OpenMaya.MScriptUtil.createMatrixFromList(par_mat, m)

    if parent:
       # transform the matrix in the local space of the parent object
        m2 = OpenMaya.MMatrix()
        par_mat = cmds.getAttr("{}.worldMatrix".format(parent))
        OpenMaya.MScriptUtil.createMatrixFromList(par_mat, m2)
        m *= m2.inverse()
    # retrieve the desired rotation for "driven" to aim at "driver", in degrees
    rot = OpenMaya.MTransformationMatrix(m).eulerRotation() * 57.2958

    return rot[0], rot[1], rot[2]


def orientAt(driven, driver, pcp=True, up=[0, 1, 0]):
    rot = lookAt(driven, driver, up=up)
    cmds.rotate(rot[0], rot[1], rot[2], driven, os=False, pcp=True)


def to_json(string_data):
    return json.loads(string_data)


def createMeshFromDescription(mesh_info):
    meshPoints = mesh_info['points']
    meshFaces = mesh_info['faces']
    factor = 1.0 / mesh_info['conversionFactor']
    # Vertices
    vertexArray = OpenMaya.MFloatPointArray()
    for i in range(0, len(meshPoints), 3):
        vertex = OpenMaya.MFloatPoint(meshPoints[i] * factor,
                                      meshPoints[i + 1] * factor,
                                      meshPoints[i + 2] * factor)
        vertexArray.append(vertex)
    numVertices = vertexArray.length()
    # Faces
    polygonCounts = OpenMaya.MIntArray()
    polygonConnects = OpenMaya.MIntArray()
    for face in meshFaces:
        for i in face:
            polygonConnects.append(i)
        polygonCounts.append(len(face))
    numPolygons = polygonCounts.length()
    fnMesh = OpenMaya.MFnMesh()
    newMesh = fnMesh.create(numVertices,
                            numPolygons,
                            vertexArray,
                            polygonCounts,
                            polygonConnects)
    fnMesh.updateSurface()
    # Assign new mesh to default shading group
    nodeName = fnMesh.name()
    cmds.sets(nodeName, e=True, fe='initialShadingGroup')
    return nodeName


def createNodeFromEmbedInfo(embed_info, node_type=None):
    if not node_type:
        node_type = 'joint'
    created_nodes = []
    for name, position in embed_info['joints'].iteritems():
        if not cmds.objExists(name):
            name = cmds.createNode(node_type, name=name)
        cmds.xform(name, worldSpace=True, translation=position)
        created_nodes.append(name)
    for point in DEFAULT_BIPIED_POINTS:
        cmds.reorder(point, back=True)
    return created_nodes


def resetNodesToEmbedInfo(nodes, embed_info):
    skipped = []
    for name in nodes:
        position = embed_info['joints'].get(name)
        if position:
            cmds.xform(name, worldSpace=True, translation=position)
        else:
            skipped.append(name)
    return skipped


def getEmbedMeshInfoFromShape(shape_name):
    # First select the shape, not the transform.
    cmds.select(cl=True)
    cmds.select(shape_name, r=True)
    cmds.skeletonEmbed()
    # For debugging: get the merged mesh that will be used
    merged_mesh_info = cmds.skeletonEmbed(query=True, mergedMesh=True)
    return to_json(merged_mesh_info)


def getEmbedInfoFromShape(shape_name,
                          segmentationMethod=3,
                          segmentationResolution=128):
    # First select the shape, not the transform.
    cmds.select(cl=True)
    cmds.select(shape_name, r=True)
    cmds.skeletonEmbed()
    # Embed skeleton using polygon soup and 512 resolution.
    cmds.skeletonEmbed(segmentationMethod=segmentationMethod,
                       segmentationResolution=segmentationResolution)
    # This method creates a few joints to see the embedding.
    embed_info = cmds.skeletonEmbed()
    return to_json(embed_info)


def scaleNodeAToNodeB(nodeA, nodeB, manual_scale=False):
    cmds.showHidden([nodeA, nodeB], a=True)
    cmds.setAttr('{}.v'.format(nodeA), 1)
    guide_min = cmds.getAttr('{}.boundingBoxMin'.format(nodeA))[0]
    guide_max = cmds.getAttr('{}.boundingBoxMax'.format(nodeA))[0]
    # guide_length = math.sqrt(math.pow(guide_min[1] - guide_max[1], 2))
    guide_length = (dt.Vector(guide_min[1]) - dt.Vector(guide_max[1])).length()

    cmds.setAttr('{}.v'.format(nodeB), 1)
    mesh_min = cmds.getAttr('{}.boundingBoxMin'.format(nodeB))[0]
    mesh_max = cmds.getAttr('{}.boundingBoxMax'.format(nodeB))[0]
    # mesh_length = math.sqrt(math.pow(mesh_min[1] - mesh_max[1], 2))
    mesh_length = (dt.Vector(mesh_min[1]) - dt.Vector(mesh_max[1])).length()

    scale_factor = mesh_length / guide_length
    if manual_scale:
        scale_factor = manual_scale
    if .5 <= scale_factor <= 2:
        print('Skipping scale...')
        return
    cmds.setAttr('{}.sx'.format(nodeA), scale_factor)
    cmds.setAttr('{}.sy'.format(nodeA), scale_factor)
    cmds.setAttr('{}.sz'.format(nodeA), scale_factor)

    return scale_factor


def interactiveAssociationMatch(*args):
    interactiveAssociation(matchTransform=True, *args)


def interactiveAssociationLegacy(matchTransform=False, *args):
    selection = cmds.ls(sl=True, type=['transform'])
    if len(selection) == 2:
        sel_set = set(selection)
        guide = sel_set - DEFAULT_BIPIED_POINTS_SET
        default_point = sel_set.intersection(DEFAULT_BIPIED_POINTS_SET)
        if not guide or not default_point:
            return
        guide = list(guide)[0]
        default_point = list(default_point)[0]
        INTERACTIVE_ASSOCIATION_INFO[default_point] = [guide]
        REVERSE_INTERACTIVE_ASSOCIATION_INFO[guide] = [default_point]
        if matchTransform:
            cmds.matchTransform(guide, default_point, pos=True)


def interactiveAssociation(matchTransform=False, *args):
    selection = cmds.ls(sl=True, type=['transform'])
    if len(selection) > 1:
        sel_set = set(selection)
        guide = sel_set - DEFAULT_BIPIED_POINTS_SET
        default_point = sel_set.intersection(DEFAULT_BIPIED_POINTS_SET)
        if not guide or not default_point:
            return
        guide = list(guide)
        default_point = list(default_point)[0]
        INTERACTIVE_ASSOCIATION_INFO[default_point] = guide
        if matchTransform:
            [cmds.matchTransform(x, default_point, pos=True) for x in guide]
        cmds.select(cl=True)


def mirrorInteractiveAssociation():
    global INTERACTIVE_ASSOCIATION_INFO
    mirrored = makeAssoicationInfoSymmetrical(INTERACTIVE_ASSOCIATION_INFO)
    INTERACTIVE_ASSOCIATION_INFO = mirrored


def makeAssoicationInfoSymmetrical(association_info, favor_side='left'):
    replace = SIDE_MIRROR_INFO[favor_side]
    mirrored_association_info = copy.deepcopy(association_info)
    for embed, guides in association_info.iteritems():
        if embed.startswith(favor_side):
            mirror_embed = embed.replace(favor_side, replace)
            mirrored_guides = []
            for guide in guides:
                mirror = m_string.convertRLName(guide)
                if cmds.objExists(mirror):
                    mirrored_guides.append(mirror)
                else:
                    mirrored_guides.append(guide)
            mirrored_association_info[mirror_embed] = mirrored_guides
    return mirrored_association_info


def getEmbedGuideAssociationInfoLegacy():
    as_selected_info = copy.deepcopy(INTERACTIVE_ASSOCIATION_INFO)
    reverse_as_selected_info = copy.deepcopy(REVERSE_INTERACTIVE_ASSOCIATION_INFO)

    embed_guide_info = {}

    for guide, embed in reverse_as_selected_info.iteritems():
        if embed not in DEFAULT_BIPIED_POINTS:
            continue
        if embed in embed_guide_info:
            if guide in embed_guide_info[embed]:
                continue
            embed_guide_info[embed].append(guide)
        else:
            embed_guide_info[embed] = [guide]

    for embed, guide in as_selected_info.iteritems():
        if embed not in DEFAULT_BIPIED_POINTS:
            continue
        if embed in embed_guide_info:
            if guide in embed_guide_info[embed]:
                continue
            embed_guide_info[embed].append(guide)
        else:
            embed_guide_info[embed] = [guide]

    return embed_guide_info


def mirrorEmbedNodes(node, target=None, search='left', replace='right'):
    node = pm.PyNode(node)
    if target:
        target_node = pm.PyNode(target)
    else:
        target_node = node.name().replace(search, replace)
        try:
            target_node = pm.PyNode(target_node)
        except Exception as e:
            print(e)
            return
    src_mat = node.getTransformation()
    target_mat = transform.getSymmetricalTransform(src_mat)
    target_mat.rotateTo([0, 0, 0])
    target_node.setTransformation(target_mat)


def mirrorSelectedEmbedNodes():
    for node in cmds.ls(sl=True):
        if node in DEFAULT_BIPIED_POINTS:
            if node.startswith('left'):
                mirrorEmbedNodes(node)
            elif node.startswith('right'):
                mirrorEmbedNodes(node, search='right', replace='left')


def mirrorEmbedNodesSide(search='left', replace='right'):
    for node in DEFAULT_BIPIED_POINTS:
        if node.startswith(search):
            mirrorEmbedNodes(node, search=search, replace=replace)


def linerlyInterperlateNodes(a, b, nodes):
    blend = 0
    blend_step = .5
    a = pm.PyNode(a)
    b = pm.PyNode(b)
    if len(nodes) > 1:
        blend_step = 1.0 / (len(nodes) + 1)
    for node in nodes:
        blend += blend_step
        node = pm.PyNode(node)
        interp_vector = vector.linearlyInterpolate(a.getMatrix(ws=True).translate,
                                                   b.getMatrix(ws=True).translate,
                                                   blend=blend)
        node.setTranslation(interp_vector)


def linerlyInterpSelected():
    selected = cmds.ls(sl=True)
    if not len(selected) > 2:
        return
    a = selected[0]
    b = selected[1]
    nodes = selected[2:]
    linerlyInterperlateNodes(a, b, nodes)


# highly specific and hardcoded funcs -----------------------------------------
# embed point menipulation --------------------------------------------------

def alignSpineToHips():
    tx_val = cmds.getAttr('hips.tx')
    cmds.setAttr('back.tx', tx_val)
    cmds.setAttr('shoulders.tx', tx_val)
    cmds.setAttr('head.tx', tx_val)


def centerHips():
    linerlyInterperlateNodes('left_thigh', 'right_thigh', ['hips'])


def adjustBackPointPosition(blend=.6, height_only=True):
    a = pm.PyNode('hips')
    b = pm.PyNode('shoulders')
    back_point = pm.PyNode('back')
    interp_vector = vector.linearlyInterpolate(a.getMatrix(ws=True).translate,
                                               b.getMatrix(ws=True).translate,
                                               blend=blend)
    if height_only:
        back_mat = back_point.getMatrix(ws=True)
        interp_vector[0] = back_mat.translate[0]
        interp_vector[2] = back_mat.translate[2]
    back_point.setTranslation(interp_vector)


def makeEmbedArmsPlanar(shoulder='left_shoulder',
                        wrist='left_hand',
                        elbow='left_elbow',
                        favor_side='left'):
    if favor_side == 'right':
        shoulder = m_string.convertRLName(shoulder)
        wrist = m_string.convertRLName(wrist)
        elbow = m_string.convertRLName(elbow)
    constrainPointToVectorPlanar(shoulder, wrist, elbow, ws=True)


def smartAdjustEmbedOutput(make_limbs_planar=True,
                           mirror_side=True,
                           favor_side='left',
                           center_hips=True,
                           align_spine=True,
                           adjust_Back_pos=True,
                           spine_blend=.6,
                           spine_height_only=True):
    if make_limbs_planar:
        makeEmbedArmsPlanar()

    if mirror_side:
        mirrorEmbedNodesSide(search=favor_side,
                             replace=SIDE_MIRROR_INFO[favor_side])
    if center_hips:
        centerHips()
    if align_spine:
        alignSpineToHips()
    if adjust_Back_pos:
        adjustBackPointPosition(blend=spine_blend,
                                height_only=spine_height_only)


# guide mannipulation ---------------------------------------------------------

def enforceMinimumHeight(nodes, lowest_point_node=GUIDE_ROOT_NAME):
    lowest_vector = pm.PyNode(lowest_point_node).getMatrix(ws=True).translate
    for node in nodes:
        node = pm.PyNode(node)
        node_vector = node.getTranslation(space='world')
        node_vector[1] = lowest_vector[1]
        node.setTranslation(node_vector, space='world')


def orientChainNodes(nodes_in_order):
    num_nodes = len(nodes_in_order) - 1
    for index, node in enumerate(nodes_in_order):
        if index == num_nodes:
            break
        orientAt(node, nodes_in_order[index + 1])


def orientAdjustArms():
    # arm_guides = ['arm_L0_root', 'arm_L0_elbow', 'arm_L0_wrist', 'arm_L0_eff']
    arm_guides = ['arm_L0_root', 'arm_L0_elbow', 'arm_L0_eff']
    orientChainNodes(arm_guides)
    arm_guides1 = ['arm_L0_wrist', 'arm_L0_eff']
    orientChainNodes(arm_guides1)
    arm_guides = [m_string.convertRLName(x) for x in arm_guides]
    arm_guides1 = [m_string.convertRLName(x) for x in arm_guides1]
    orientChainNodes(arm_guides)
    orientChainNodes(arm_guides1)


def adjustHandPosition(wrist='arm_L0_wrist', metacarpal='arm_L0_eff', favor_side='left'):
    if favor_side != 'left':
        wrist = m_string.convertRLName(wrist)
        metacarpal = m_string.convertRLName(metacarpal)
    a = pm.PyNode(wrist)
    b = pm.PyNode(metacarpal)

    diff_vect = b.getMatrix(ws=True).translate - a.getMatrix(ws=True).translate

    mat = a.getMatrix(ws=True).translate - (diff_vect)
    a.setTranslation(mat, space='world')


def adjustWristPosition(elbow='left_elbow',
                        wrist_guide='arm_L0_wrist',
                        metacarpal='left_hand',
                        favor_side='left'):
    constrainPointToVectorPlanar(elbow, metacarpal, wrist_guide, ws=True, pcp=True)


def simpleMatchGuideToEmbed(guide_association_info):
    for point in DEFAULT_BIPIED_POINTS:
        for guide in guide_association_info[point]:
            cmds.matchTransform(guide, point, pos=True)


@utils.viewport_off
@utils.one_undo
def matchGuidesToEmbedOutput(guide_association_info=DEFAULT_EMBED_GUIDE_ASSOCIATION,
                             guide_root=GUIDE_ROOT_NAME,
                             setup_geo=SETUP_GEO_SHAPE_NAME,
                             scale_guides=True,
                             manual_scale=False,
                             lowest_point_node=None,
                             min_height_nodes=None,
                             adjust_hand_position=True,
                             orient_adjust_arms=True):
    if scale_guides:
        scaleNodeAToNodeB(guide_root, setup_geo, manual_scale=manual_scale)

    simpleMatchGuideToEmbed(guide_association_info)

    if min_height_nodes:
        if not lowest_point_node:
            lowest_point_node = guide_root
        enforceMinimumHeight(min_height_nodes,
                             lowest_point_node=lowest_point_node)
    if adjust_hand_position:
        adjustHandPosition()
        adjustHandPosition(favor_side='right')
        adjustWristPosition()
        adjustWristPosition(elbow='right_elbow',
                            wrist_guide='arm_R0_wrist',
                            metacarpal='right_hand')
    if orient_adjust_arms:
        orientAdjustArms()


@utils.viewport_off
@utils.one_undo
def runAllEmbed(guide_association_info,
                setup_geo,
                guide_root,
                segmentationMethod=3,
                segmentationResolution=128,
                scale_guides=True,
                lowest_point_node=None,
                min_height_nodes=None,
                smart_adjust=True,
                adjust_hand_position=True,
                orient_adjust_arms=True,
                mirror_embed_side='left'):
    embed_info = getEmbedInfoFromShape(setup_geo,
                                       segmentationMethod=segmentationMethod,
                                       segmentationResolution=segmentationResolution)
    createNodeFromEmbedInfo(embed_info)
    if smart_adjust:
        smartAdjustEmbedOutput(make_limbs_planar=True,
                               mirror_side=bool(mirror_embed_side),
                               favor_side=mirror_embed_side,
                               center_hips=True,
                               align_spine=True,
                               adjust_Back_pos=True,
                               spine_blend=.6,
                               spine_height_only=True)

    matchGuidesToEmbedOutput(guide_association_info=guide_association_info,
                             guide_root=guide_root,
                             setup_geo=setup_geo,
                             scale_guides=scale_guides,
                             lowest_point_node=lowest_point_node,
                             min_height_nodes=min_height_nodes,
                             adjust_hand_position=adjust_hand_position,
                             orient_adjust_arms=orient_adjust_arms)
    return embed_info


def runAllEmbedFromPaths(model_filepath,
                         guide_filepath,
                         guide_association_info,
                         setup_geo,
                         guide_root,
                         scale_guides=True,
                         lowest_point_node=None,
                         min_height_nodes=None,
                         adjust_hand_position=True,
                         orient_adjust_arms=True,
                         mirror_embed_side='left'):

    cmds.file(model_filepath, i=True)
    io.import_guide_template(filePath=guide_filepath)
    if type(guide_association_info) != dict:
        guide_association_info = _importData(guide_association_info)
    runAllEmbed(guide_association_info,
                setup_geo,
                guide_root,
                scale_guides=scale_guides,
                lowest_point_node=lowest_point_node,
                min_height_nodes=min_height_nodes,
                adjust_hand_position=adjust_hand_position,
                orient_adjust_arms=orient_adjust_arms)
