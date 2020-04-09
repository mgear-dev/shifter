# -*- coding: utf-8 -*-
# Standard
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import generators
from __future__ import division

import json
import math


# dcc
import maya.OpenMaya as OpenMaya
import pymel.core as pm
from maya import cmds


# mgear
from mgear.core import vector
from mgear.core import transform
from mgear.core import callbackManager


# constants -------------------------------------------------------------------
UI_TITLE = 'Auto Fit Guide'

# This order is very important
DEFAULT_BIPIED_POINTS = ['hips',
                        'left_thigh',
                        'left_knee',
                        'left_ankle',
                        'left_foot',
                        'right_thigh',
                        'right_knee',
                        'right_ankle',
                        'right_foot',
                        'back',
                        'shoulders',
                        'head',
                        'left_shoulder',
                        'left_elbow',
                        'left_hand',
                        'right_shoulder',
                        'right_elbow',
                        'right_hand']

DEFAULT_BIPIED_POINTS_SET = set(DEFAULT_BIPIED_POINTS)

INTERACTIVE_ASSOCIATION_INFO = {}


# Utils ----------------------------------------------------------------------


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


def getEmbedInfoFromShape(shape_name,
                          segmentationMethod=3,
                          segmentationResolution=128):
    # First select the shape, not the transform.
    cmds.select(cl=True)
    cmds.select(shape_name, r=True)
    cmds.skeletonEmbed()
    # For debugging: get the merged mesh that will be used
    merged_mesh_info = cmds.skeletonEmbed(query=True, mergedMesh=True)
    # Embed skeleton using polygon soup and 512 resolution.
    cmds.skeletonEmbed(segmentationMethod=segmentationMethod,
                       segmentationResolution=segmentationResolution)
    # This method creates a few joints to see the embedding.
    embed_info = cmds.skeletonEmbed()
    return to_json(embed_info), to_json(merged_mesh_info)


def scaleNodeAToNodeB(nodeA, nodeB):

    cmds.setAttr('{}.v'.format(nodeA), 1)
    guide_min = cmds.getAttr('{}.boundingBoxMin'.format(nodeA))[0]
    guide_max = cmds.getAttr('{}.boundingBoxMax'.format(nodeA))[0]
    guide_length = math.sqrt(math.pow(guide_min[1] - guide_max[1], 2))

    cmds.setAttr('{}.v'.format(nodeB), 1)
    mesh_min = cmds.getAttr('{}.boundingBoxMin'.format(nodeB))[0]
    mesh_max = cmds.getAttr('{}.boundingBoxMax'.format(nodeB))[0]
    mesh_length = math.sqrt(math.pow(mesh_min[1] - mesh_max[1], 2))

    scale_factor = round(mesh_length / guide_length, 0)
    cmds.setAttr('{}.sx'.format(nodeA), scale_factor)
    cmds.setAttr('{}.sy'.format(nodeA), scale_factor)
    cmds.setAttr('{}.sz'.format(nodeA), scale_factor)

    return scale_factor


def interactiveAssociation(*args):
    selection = cmds.ls(sl=True, type=['transform'])
    if len(selection) == 2:
        sel_set = set(selection)
        guide = sel_set - DEFAULT_BIPIED_POINTS_SET
        default_point = sel_set.intersection(DEFAULT_BIPIED_POINTS_SET)
        if not guide or not default_point:
            return
        guide = list(guide)[0]
        default_point = list(default_point)[0]
        INTERACTIVE_ASSOCIATION_INFO[default_point] = guide
        cmds.matchTransform(guide, default_point, pos=True)


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


def linerlyInterpSelected():
    selected = pm.selected()
    if not len(selected) > 2:
        return
    a = pm.PyNode(selected[0])
    b = pm.PyNode(selected[1])
    nodes = selected[2:]
    blend = 0
    blend_step = .5
    if len(nodes) > 1:
        blend_step = 1.0 / (len(nodes) + 1)
    for node in nodes:
        blend += blend_step
        node = pm.PyNode(node)
        interp_vector = vector.linearlyInterpolate(a.getMatrix(ws=True).translate,
                                                   b.getMatrix(ws=True).translate,
                                                   blend=blend)
        node.setTranslation(interp_vector)
