# -*- coding: utf-8 -*-
# !/usr/bin/env python
# Future
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import generators
from __future__ import division

# standard
import os
import copy
import pprint
import itertools

# dcc
import pymel.core as pm
import maya.cmds as cmds

# mgear
from mgear.core import pyqt
from mgear.core import utils
from mgear.core import callbackManager
from mgear.shifter import io
from mgear.shifter import afg_tools
from mgear.shifter import relative_guide_placement
from mgear.vendor.Qt import QtCore
from mgear.vendor.Qt import QtWidgets

# For debugging
# from PySide2 import QtCore
# from PySide2 import QtWidgets
# reload(pyqt)
# reload(afg_tools)
# reload(relative_guide_placement)

# constants -------------------------------------------------------------------
WINDOW_TITLE = "Auto Fit Guide Tools (AFG) (BETA)"
AFB_FILE_EXTENSION = "afg"
RELATIVE_FILE_EXTENSION = "rgp"
UI_REFRESH_RATE = 3
DANCE_EMOTICON = ["v(._.)v", "<(*-* <)", "^(*-*)^", "(>._.)>", "<(._.)v", "^(*-*)v", "(>._.)v"]


def get_top_level_widgets(class_name=None, object_name=None):
    """
    Get existing widgets for a given class name

    Args:
        class_name (str): Name of class to search top level widgets for
        object_name (str): Qt object name

    Returns:
        List of QWidgets
    """
    matches = []

    # Find top level widgets matching class name
    for widget in QtWidgets.QApplication.topLevelWidgets():
        try:
            # Matching class
            if class_name and widget.metaObject().className() == class_name:
                matches.append(widget)
            # Matching object name
            elif object_name and widget.objectName() == object_name:
                matches.append(widget)
        except AttributeError:
            continue
        # Print unhandled to the shell
        except Exception as e:
            print(e)

    return matches


def close_existing(class_name=None, object_name=None):
    """
    Close and delete any existing windows of class_name

    Args:
        class_name (str): QtWidget class name
        object_name (str): Qt object name

    Returns: None
    """
    for widget in get_top_level_widgets(class_name, object_name):
        # Close
        widget.close()
        # Delete
        widget.deleteLater()


def show(*args):
    """convenience function to show the UI for which the moule is named after

    Args:
        *args: catch all to allow anything to call it

    Returns:
        Instance: AutofitGuideTool
    """
    try:
        close_existing(class_name="AutoFitGuideTool",
                       object_name="AutoFitGuideTool")
    except Exception:
        pass
    # maya_window = None
    maya_window = pyqt.maya_main_window() or None
    AFG_TOOL_UI = AutoFitGuideTool(parent=maya_window)
    AFG_TOOL_UI.show()
    return AFG_TOOL_UI


def fileDialog(startDir, ext=None, mode=0):
    """prompt dialog for either import/export from a UI

    Args:
        startDir (str): A directory to start from
        mode (int, optional): import or export, 0/1

    Returns:
        str: path selected by user
    """

    fPath = cmds.fileDialog2(dialogStyle=2,
                             fileMode=mode,
                             startingDirectory=startDir,
                             fileFilter=ext)
    if fPath is not None:
        fPath = fPath[0]
    return fPath


def _guideRootNode():
    """Get the top node of the guides no matter the name
    based off the mGear attr

    Returns:
        str: Name of topnode

    Raises:
        ValueError: Too few or many guide root nodes in the scene.
    """
    guides = cmds.ls("|*.ismodel", o=True)
    num_of_guides = len(guides)
    if num_of_guides == 1:
        return guides[0]
    elif num_of_guides > 1:
        msg = "Too many guides found! {}".format(num_of_guides)
        raise ValueError(msg)
    else:
        msg = "No guides found!"
        raise ValueError(msg)


class PathObjectExistsEdit(QtWidgets.QLineEdit):

    """Custom QlineEdit that displays the validation of the information
    entered. Path or maya node

    Attributes:
        default_value (str): default value so that validation shows neutral
        export_path (bool): Export mode, allows qfiledialogue to save
        focusedIn (Signal): emit signal when qline widget gains focus
        validate_mode (str): mayaNode or path
    """

    focusedIn = QtCore.Signal()

    def __init__(self,
                 default_value=None,
                 text=None,
                 placeholderText=None,
                 validate_mode="path",
                 parent=None):
        super(PathObjectExistsEdit, self).__init__(text=text,
                                                   placeholderText=placeholderText,
                                                   parent=parent)

        self.validate_mode = validate_mode
        self.export_path = False
        self.setDefaultValue(default_value)
        self.editingFinished.connect(self.visualizeValidation)
        self.editingFinished.connect(self.selectMayaNode)
        self.installEventFilter(self)

    def setNeutral(self):
        self.setStyleSheet("")

    def setDefaultValue(self, default_value):
        if default_value is None:
            self.default_value = None
            return
        self.default_value = "[{}]".format(default_value)
        self.setText(self.default_value)
        completer = QtWidgets.QCompleter([self.default_value])
        completer.setFilterMode(QtCore.Qt.MatchContains)
        self.setCompleter(completer)

    def setValid(self):
        self.setStyleSheet("border: 1px solid green;")

    def setInvalid(self):
        self.setStyleSheet("border: 1px solid red;")

    def selectMayaNode(self):
        if self.validate_mode == "mayaExists" and self.validateNodeExists:
            text = self.text()
            if text == "" or not cmds.objExists(text):
                return
            cmds.select(cl=True)
            cmds.select(text)

    def visualizeValidation(self):
        text = self.text()
        if (text.replace(" ", "") == "" or
                text.replace(" ", "") == self.default_value):
            self.setNeutral()
            return

        if self.validate_mode == "path" and self.validatePath():
            self.setValid()
        elif self.validate_mode == "path" and not self.validatePath():
            self.setInvalid()
        elif self.validate_mode == "mayaExists" and self.validateNodeExists():
            self.setValid()
        elif self.validate_mode == "mayaExists" and not self.validateNodeExists():
            self.setInvalid()

    def validateNodeExists(self):
        return cmds.objExists(self.text())

    def validatePath(self):
        validated = os.path.exists(self.text())
        if self.export_path:
            validated = True
        return validated

    # TODO: This crashes, investigate why
    # def eventFilter(self, watched, event):
    #     if event.type() == QtCore.QEvent.DragEnter:
    #         event.accept()
    #     if event.type() == QtCore.QEvent.Drop:
    #         return True
    #     return False

    def focusInEvent(self, event):
        self.focusedIn.emit()
        super(PathObjectExistsEdit, self).focusInEvent(event)


class SelectComboBoxRefreshWidget(QtWidgets.QWidget):

    """convenience widget with refresh button and qcombobox

    Attributes:
        mainLayout (QBoxLayout): the widgets layout
        refresh_btn (QPushButton): refresh button
        selected_mesh_ledit (lineedit): qlineedit
    """

    def __init__(self, label_text, default_value=None, parent=None):
        super(SelectComboBoxRefreshWidget, self).__init__(parent=parent)
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.setLayout(self.mainLayout)
        self.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        msg = "Enter Mesh Name..."
        self.selected_mesh_ledit = PathObjectExistsEdit(text=None,
                                                        default_value=default_value,
                                                        validate_mode="mayaExists",
                                                        placeholderText=msg)
        self.selected_mesh_ledit.setMinimumHeight(24 + 2)
        self.select_src_mesh_btn = QtWidgets.QPushButton()
        self.select_src_mesh_btn.setStatusTip("Select Source Mesh")
        self.select_src_mesh_btn.setToolTip("Select Source Mesh")
        reload_btn = pyqt.get_icon("mouse-pointer")
        # style = QtWidgets.QStyle
        # reload_btn = self.style().standardIcon(getattr(style, "SP_BrowserReload"))
        self.select_src_mesh_btn.setIcon(reload_btn)
        self.select_src_mesh_btn.setMinimumHeight(24)
        self.select_src_mesh_btn.setMaximumHeight(24)
        self.select_src_mesh_btn.setMinimumWidth(24)
        self.select_src_mesh_btn.setMaximumWidth(24)
        self.mainLayout.addWidget(QtWidgets.QLabel(label_text))
        self.mainLayout.addWidget(self.selected_mesh_ledit, 1)
        self.mainLayout.addWidget(self.select_src_mesh_btn)

        self.refreshMeshList()
        self.connectSignals()

    def connectSignals(self):
        # self.select_src_mesh_btn.clicked.connect(self.refreshMeshList)
        self.select_src_mesh_btn.clicked.connect(self.addSelection)
        self.selected_mesh_ledit.focusedIn.connect(self.refreshMeshList)

    def addSelection(self):
        selected = cmds.ls(sl=True)
        if not selected:
            return

        node = None
        if cmds.nodeType(selected[0]) == "mesh":
            node = selected[0]
        elif cmds.nodeType(selected[0]) == "transform":
            children = cmds.listRelatives(selected[0], s=True)
            if not children:
                return
            node = children[0]

        if node is not None:
            self.selected_mesh_ledit.setText(node)

    def refreshMeshList(self):
        # self.selected_mesh_ledit.clear()
        items = list(set(cmds.ls(exactType="mesh")))
        items.sort()
        completer = QtWidgets.QCompleter(items)
        completer.setFilterMode(QtCore.Qt.MatchContains)
        self.selected_mesh_ledit.setCompleter(completer)
        self.selected_mesh_ledit.setNeutral()

    @property
    def text(self):
        return self.selected_mesh_ledit.text()


class LoadImportWidget(QtWidgets.QWidget):

    """convenience widget with qlineedit, load filedialoq

    Attributes:
        ext (List): of supported extensions
        import_button (QPushButton): imports the path
        import_type (str): mGear guide import or traditional maya .ma
        load_button (QPushButton): button connected to filedialog
        mainLayout (QBoxLayout): widgets main layout
        mode (int): 0 - 1 for importing or exporting
        path_widget (PathObjectExistEdit): custom QLineEdit
    """

    def __init__(self,
                 file_contents=None,
                 ext=None,
                 import_type="maya",
                 mode=1,
                 show_import_button=True,
                 parent=None):
        super(LoadImportWidget, self).__init__(parent=parent)
        self.import_type = import_type
        self.ext = ext
        self.mode = mode
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.mainLayout)
        if file_contents:
            button_label = "Import {}".format(file_contents)
            placeholderText = "Path to {} file...".format(file_contents)
        else:
            button_label = "Import"
            placeholderText = "Path to file..."
        self.path_widget = PathObjectExistsEdit(placeholderText=placeholderText)
        self.load_button = QtWidgets.QPushButton("...")
        self.import_button = QtWidgets.QPushButton(button_label)
        self.import_button.setMinimumWidth(100)
        if not show_import_button:
            self.import_button.hide()

        self.mainLayout.addWidget(self.path_widget, 1)
        self.mainLayout.addWidget(self.load_button, 0)
        self.mainLayout.addWidget(self.import_button, 0)
        self.path_widget.setMinimumHeight(24)
        self.load_button.setMinimumHeight(24)
        self.import_button.setMinimumHeight(24)
        self.connectSignals()

    def connectSignals(self):
        self.load_button.clicked.connect(self.loadPathDialog)
        self.import_button.clicked.connect(self._import)

    def _import(self):
        if self.path_widget.text().replace(" ", "") == "":
            return
        if self.import_type == "maya":
            cmds.file(self.path_widget.text(), i=True)
        elif self.import_type == "mgear":
            io.import_guide_template(filePath=self.path_widget.text())

    def loadPathDialog(self):
        # multipleFilters = "Maya Files (*.ma *.mb);;Maya ASCII (*.ma)
        if self.ext:
            tmp = " ".join(["*.{}".format(x) for x in self.ext])
            all_exts = ["AFG Files ({})".format(tmp), "All Files (*.*)"]
            all_exts = ";;".join(all_exts)
        file_path = fileDialog("/", ext=all_exts, mode=self.mode)
        if file_path:
            self.path_widget.setText(file_path)
        if self.mode > 0:
            self.path_widget.visualizeValidation()

    @property
    def path(self):
        return self.path_widget.text()


class AutoFitBipedWidget(QtWidgets.QWidget):

    """Main widget for autofitting embed nodes for bipeds

    Attributes:
        cb_manager (CallBackManager): Callback manager for the AutoFit Biped
        storedEmbedInfo (dict): Store the embed info if nothing has changed
        for speed.
    """

    def __init__(self, parent=None):
        super(AutoFitBipedWidget, self).__init__(parent=parent)
        self.cb_manager = callbackManager.CallbackManager()
        self.stored_embed_info = {}
        self.window().afg_callback_managers.append(self.cb_manager)
        self.setWindowTitle("Auto Fit Biped")
        self.model_path = None
        self.guide_path = None
        self.__isInteractiveEnabled = False
        self.__matchPositionEnabled = False
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.mainLayout.addWidget(self.embedSettingsInfoWidget())
        self.mainLayout.addWidget(self.exportEmbedInfoWidget())
        self.connectSignals()

    def connectSignals(self):
        # self.default_association_cb.toggled.connect(self.setAssociationWidget)
        self.run_all_settings_btn.clicked.connect(self.runAllEmbed)
        # self.import_default_biped_btn.clicked.connect(self.importDefaultGuide)
        self.delete_embed_nodes.clicked.connect(afg_tools.deleteEmbedNodes)
        self.smart_adjust_btn.clicked.connect(self.runSmartAdjust)
        self.mirror_embed_btns.clicked.connect(self.runMirrorEmbed)
        self.match_guides_toEmbed_btn.clicked.connect(self.matchGuidesToEmbedOutput)
        self.create_embed_nodes_btn.clicked.connect(self.createEmbedNodes)
        self.src_geo_widget.selected_mesh_ledit.editingFinished.connect(self._updateStoredEmbedInfo)
        # create/export -------------------------------------------------------
        self.association_list_widget.currentRowChanged.connect(self.selectAssociationListItem)
        self.enable_association_snap_cb.toggled.connect(self._matchPositionToggled)
        self.enable_association_btn.toggled.connect(self._interactiveToggled)
        self.apply_default_association_btn.clicked.connect(self.applyDefaultAssociation)
        self.mirror_association_btn.clicked.connect(self._mirrorAssociationInfo)
        self.import_association_btn.clicked.connect(self.importAssociation)
        self.clear_association_btn.clicked.connect(self._clearUserAssociations)
        self.print_association_btn.clicked.connect(self._printUserAssociation)
        self.export_association_btn.clicked.connect(self.exportAssociation)

    def importDefaultGuide(self):
        io.import_sample_template("biped.sgt")

    def setAssociationWidget(self, *args):
        self.import_association_path_widget.setEnabled(not(self.default_association_cb.isChecked()))

    def getGuideAssociationInfoLegacy(self):
        filePath = self.import_association_path_widget.path
        if self.default_association_cb.isChecked():
            return copy.decepcopy(afg_tools.DEFAULT_EMBED_GUIDE_ASSOCIATION)
        else:
            return afg_tools._importData(filePath)

    def getGuideAssociationInfo(self):
        """Return the interactive session guide association info

        Returns:
            dict: embed_node: guide name
        """
        return copy.deepcopy(afg_tools.INTERACTIVE_ASSOCIATION_INFO)

    def _getMirrorSide(self):
        mirror_embed_side = "left"
        if self.mirror_none_rbtn.isChecked():
            mirror_embed_side = False
        elif self.mirror_right_rbtn.isChecked():
            mirror_embed_side = "right"
        return mirror_embed_side

    def createEmbedNodes(self):
        if not self.safetyChecksRun():
            return
        embed_info = self.getEmbedInfo()
        afg_tools.createNodeFromEmbedInfo(embed_info)
        # self._updateStoredEmbedInfo(embed_info=embed_info)

    def matchGuidesToEmbedOutput(self):
        if not self.safetyChecksRun():
            return
        guide_association_info = self.getGuideAssociationInfo()
        if self.enable_adjust_rbtn.isChecked():
            afg_tools.matchGuidesToEmbedOutput(guide_association_info=guide_association_info,
                                               guide_root=_guideRootNode(),
                                               setup_geo=self.src_geo_widget.text,
                                               scale_guides=True,
                                               manual_scale=False,
                                               lowest_point_node=None,
                                               min_height_nodes=None,
                                               adjust_hand_position=True,
                                               orient_adjust_arms=True)
        else:
            afg_tools.simpleMatchGuideToEmbed(guide_association_info)

    def runMirrorEmbed(self):
        if not self._getMirrorSide():
            return
        mr_side = self._getMirrorSide()
        afg_tools.mirrorEmbedNodesSide(search=self._getMirrorSide(),
                                       replace=afg_tools.SIDE_MIRROR_INFO[mr_side])

    def runSmartAdjust(self):
        afg_tools.smartAdjustEmbedOutput(make_limbs_planar=True,
                                         mirror_side=True,
                                         favor_side=self._getMirrorSide(),
                                         center_hips=True,
                                         align_spine=True,
                                         adjust_Back_pos=True,
                                         spine_blend=.6,
                                         spine_height_only=True)

    def safetyChecksRun(self):
        # if self.model_path.path == "" and not cmds.objExists(self.src_geo_widget.text):
        #     msg = "No Source geometry supplied!"
        #     cmds.warning(msg)
        #     self.window().statusBar().showMessage(msg, 3000)
        #     return False
        if self.src_geo_widget.text == "" or not cmds.objExists(self.src_geo_widget.text):
            msg = "No Source geometry supplied!"
            cmds.warning(msg)
            self.window().statusBar().showMessage(msg, 3000)
            self.src_geo_widget.selected_mesh_ledit.setFocus()
            return False

        if not cmds.objExists(_guideRootNode()):
            msg = "No Guide node supplied!"
            cmds.warning(msg)
            self.window().statusBar().showMessage(msg, 3000)
            return False
        # if (not self.default_association_cb.isChecked() and
        #         self.import_association_path_widget.path == ""):
        #     msg = "No Association info supplied! Either filepath or Default"
        #     cmds.warning(msg)
        #     self.window().statusBar().showMessage(msg, 3000)
        #     self.import_association_path_widget.path_widget.setFocus()
        #     return False
        return True

    def _updateStoredEmbedInfo(self, embed_info=None):
        self.stored_embed_info = {}
        self.stored_embed_info[self.src_geo_widget.text] = embed_info

    def _getEmbedInfo(self):
        index = self.embed_options_cbb.currentIndex()
        rez = int(self.embed_rez_cbb.currentText())
        embed_info = afg_tools.getEmbedInfoFromShape(self.src_geo_widget.text,
                                                     segmentationMethod=index,
                                                     segmentationResolution=rez)
        return embed_info

    def getEmbedInfo(self):
        embed_info = self.stored_embed_info.get(self.src_geo_widget.text, {})
        if not embed_info:
            embed_info = self._getEmbedInfo()
            self._updateStoredEmbedInfo(embed_info)
        return embed_info

    def runAllEmbed(self):

        if not self.safetyChecksRun():
            return
        smart_adjust = self.enable_adjust_rbtn.isChecked()

        # if self.model_path.path:
        #     self.model_path._import()
        # if self.guide_path.path and not cmds.objExists(_guideRootNode()):
        #     self.guide_path._import()

        index = self.embed_options_cbb.currentIndex()
        rez = int(self.embed_rez_cbb.currentText())
        embed_info = afg_tools.runAllEmbed(self.getGuideAssociationInfo(),
                                           self.src_geo_widget.text,
                                           _guideRootNode(),
                                           segmentationMethod=index,
                                           segmentationResolution=rez,
                                           scale_guides=True,
                                           lowest_point_node=None,
                                           min_height_nodes=None,
                                           smart_adjust=smart_adjust,
                                           adjust_hand_position=smart_adjust,
                                           orient_adjust_arms=smart_adjust,
                                           mirror_embed_side=self._getMirrorSide())
        self._updateStoredEmbedInfo(embed_info)


    # create/export function --------------------------------------------------
    def exportAssociation(self):
        tmp = " ".join(["*.{}".format(x) for x in [AFB_FILE_EXTENSION]])
        all_exts = ["AFG Files ({})".format(tmp), "All Files (*.*)"]
        all_exts = ";;".join(all_exts)
        filePath = fileDialog("/", ext=all_exts, mode=0)
        if not filePath:
            msg = "No file path selected."
            self.window().statusBar().showMessage(msg)
            cmds.warning(msg)
            return
        afg_tools._exportData(afg_tools.INTERACTIVE_ASSOCIATION_INFO, filePath)
        self.window().statusBar().showMessage("Exported! {}".format(filePath),
                                              3000)
        print("Exported! {}".format(filePath))

    def importAssociation(self):
        tmp = " ".join(["*.{}".format(x) for x in [AFB_FILE_EXTENSION]])
        all_exts = ["AFG Files ({})".format(tmp), "All Files (*.*)"]
        all_exts = ";;".join(all_exts)
        filePath = fileDialog("/", ext=all_exts, mode=1)
        if not filePath:
            msg = "No file path selected."
            self.window().statusBar().showMessage(msg)
            cmds.warning(msg)
            return
        self.applyAssociation(afg_tools._importData(filePath))
        self.window().statusBar().showMessage("Imported! {}".format(filePath),
                                              3000)
        print("Exported! {}".format(filePath))

    def _printUserAssociation(self):
        print("----- Guide and Embed node association -----")
        pprint.pprint(afg_tools.INTERACTIVE_ASSOCIATION_INFO)

    def applyDefaultAssociation(self):
        self.applyAssociation(afg_tools.DEFAULT_EMBED_GUIDE_ASSOCIATION)

    def applyAssociation(self, guide_association_info):
        tmp = {}
        non_existant = []
        for guide, values in guide_association_info.iteritems():
            existing_nodes = []
            for v in values:
                if cmds.objExists(v):
                    existing_nodes.append(v)
                else:
                    non_existant.append(v)
            if existing_nodes:
                tmp[guide] = existing_nodes
        afg_tools.INTERACTIVE_ASSOCIATION_INFO = tmp
        self.visualizeAssociationEntry()
        if non_existant:
            msg = "Nodes are do not exist!\n{}".format(non_existant)
            print(msg)
            self.window().statusBar().showMessage(msg, 3000)

    def _mirrorAssociationInfo(self):
        afg_tools.mirrorInteractiveAssociation()
        self.visualizeAssociationEntry()

    def _clearUserAssociations(self):
        afg_tools.clearUserAssociations()
        self.visualizeAssociationEntry()
        self.window().statusBar().showMessage("Association Cleared!", 3000)

    def togglePreserveChildren(self):
        """TODO - Add this as a checkbox
        """
        cmds.optionVar(iv=["setTRSPreserveChildPosition", True])
        cmds.manipMoveContext("Move", e=True, pcp=True)
        cmds.manipRotateContext("Rotate", e=True, pcp=True)
        cmds.manipScaleContext("Scale", e=True, pcp=True)

    def _matchPositionToggled(self):
        if self.__matchPositionEnabled:
            self.__matchPositionEnabled = False
            self.enable_association_snap_cb.setText("Enable Match Position")

        else:
            self.__matchPositionEnabled = True
            self.enable_association_snap_cb.setText("Disable Match Position")

    def _interactiveToggled(self):
        if self.__isInteractiveEnabled:
            self.endInteractiveAssociation()
            self.__isInteractiveEnabled = False
            self.enable_association_btn.setText("Enable\nInteractive Association")

        else:
            self.startInteractiveAssociation()
            self.__isInteractiveEnabled = True
            self.enable_association_btn.setText("Disable\nInteractive Association")
            msg = "Select embed node and then guide(s)"
            self.window().statusBar().showMessage(msg, 3000)

    def updateInteractiveAssociation(self, *args):
        afg_tools.interactiveAssociation(matchTransform=self.__matchPositionEnabled)
        self.visualizeAssociationEntry()

    def startInteractiveAssociation(self):
        self.cb_manager.selectionChangedCB("interactive_association",
                                               self.updateInteractiveAssociation)

    def endInteractiveAssociation(self):
        self.cb_manager.removeManagedCB("interactive_association")

    def visualizeAssociationEntry(self):
        # window = self.window()
        # ids = [id(x) for x in window._toolTip_widgets]
        for index in xrange(self.association_list_widget.count()):
            item = self.association_list_widget.item(index)
            embed_name = item.text()
            font = item.font()
            if embed_name in afg_tools.INTERACTIVE_ASSOCIATION_INFO:
                font.setItalic(True)
            else:
                font.setItalic(False)
            item.setFont(font)
            nodes = afg_tools.INTERACTIVE_ASSOCIATION_INFO.get(embed_name)
            msg = "{} >> {}".format(embed_name, nodes)
            item.setToolTip(msg)
            item.setStatusTip(msg)
            # if id(item) not in ids:
            #     window._toolTip_widgets.append(item)

    def selectAssociationListItem(self, *args):
        item = self.association_list_widget.currentItem()
        if not item:
            return
        item = item.text()
        if not cmds.objExists(item):
            return
        if item in afg_tools.INTERACTIVE_ASSOCIATION_INFO:
            items = [item]
            items.extend(afg_tools.INTERACTIVE_ASSOCIATION_INFO[item])
        else:
            items = [item]
        cmds.select(items)

    def embedSettingsInfoWidget(self):
        widget = QtWidgets.QGroupBox("Embed Node Settings")
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        widget.setLayout(layout)
        association_layout = QtWidgets.QHBoxLayout()
        msg = "Import Biped Template"
        # self.import_default_biped_btn = QtWidgets.QPushButton(msg)
        msg = "mGear > Shifter > Guide Template Sample > Biped Template"
        # self.import_default_biped_btn.setToolTip(msg)
        # self.import_default_biped_btn.setStatusTip(msg)
        # self.default_association_cb = QtWidgets.QCheckBox("Use Default")
        # msg = "Use default Biped Association or Import."
        # self.default_association_cb.setToolTip(msg)
        # self.default_association_cb.setStatusTip(msg)
        # self.window()._toolTip_widgets.append(self.default_association_cb)
        # self.default_association_cb.setChecked(True)
        # msg = "Import Biped Association Info"
        # self.import_association_path_widget = LoadImportWidget(file_contents=msg,
        #                                                        ext=[AFB_FILE_EXTENSION],
        #                                                        show_import_button=False)
        # msg = "Import Association Path"
        # self.import_association_path_widget.setToolTip(msg)
        # self.import_association_path_widget.setStatusTip(msg)
        # self.window()._toolTip_widgets.append(self.import_association_path_widget)
        # self.import_association_path_widget.setEnabled(False)
        # association_layout.addWidget(self.default_association_cb)
        # association_layout.addWidget(self.import_association_path_widget)
        # self.import_association_path_widget.load_button.setMinimumWidth(24)
        self.src_geo_widget = SelectComboBoxRefreshWidget("Source Mesh        ")
        self.window()._toolTip_widgets.append(self.src_geo_widget.select_src_mesh_btn)
        # embed options ------------------------------------------------------
        h_layout_01 = QtWidgets.QHBoxLayout()
        label_01 = QtWidgets.QLabel("Embed Resolution")
        self.embed_rez_cbb = QtWidgets.QComboBox()
        self.embed_rez_cbb.addItems(["64", "128", "512", "1024"])
        self.embed_rez_cbb.setCurrentIndex(1)
        self.embed_rez_cbb.setMinimumHeight(24 + 2)
        self.embed_rez_cbb.setMinimumWidth(150)
        style = "background-color: transparent; QComboBox::down-arrow:on { top: 1px; left: 1px;};"
        self.embed_rez_cbb.setStyleSheet(style)
        h_layout_01.addWidget(label_01)
        h_layout_01.insertStretch(1, 1)
        h_layout_01.addWidget(self.embed_rez_cbb, 1)

        h_layout_02 = QtWidgets.QHBoxLayout()
        label_02 = QtWidgets.QLabel("Embed type")
        self.embed_options_cbb = QtWidgets.QComboBox()
        items = ["Perfect Mesh",
                 "Watertight Mesh ",
                 "Imperfect mesh",
                 "Polygon Repair"]
        self.embed_options_cbb.addItems(items)
        self.embed_options_cbb.setStyleSheet("background-color: transparent;")
        self.embed_options_cbb.setCurrentIndex(3)
        self.embed_options_cbb.setMinimumHeight(24 + 2)
        self.embed_options_cbb.setMinimumWidth(150)
        h_layout_02.addWidget(label_02)
        h_layout_02.insertStretch(1, 1)
        h_layout_02.addWidget(self.embed_options_cbb, 1)
        #  ----------------------------------------------------------------
        mirror_radio_layout = QtWidgets.QHBoxLayout()
        radio_label = QtWidgets.QLabel("Mirror Embed Nodes")
        self.mirror_left_rbtn = QtWidgets.QRadioButton("Left")
        self.mirror_left_rbtn.setChecked(True)
        self.mirror_right_rbtn = QtWidgets.QRadioButton("Right")
        self.mirror_none_rbtn = QtWidgets.QRadioButton("None")
        self.mirror_embed_btns = QtWidgets.QPushButton("Run")
        self.mirror_embed_btns.setMaximumWidth(30)
        mirror_radio_layout.addWidget(radio_label)
        mirror_radio_layout.insertStretch(1, 1)
        mirror_radio_layout.addWidget(self.mirror_left_rbtn, 1)
        mirror_radio_layout.addWidget(self.mirror_none_rbtn, 1)
        mirror_radio_layout.addWidget(self.mirror_right_rbtn, 1)
        mirror_radio_layout.addWidget(self.mirror_embed_btns)
        mirror_rbtn_group = QtWidgets.QButtonGroup()
        mirror_rbtn_group.setObjectName("mirror_rbtn_group")
        mirror_rbtn_group.setExclusive(True)
        mirror_rbtn_group.addButton(self.mirror_left_rbtn)
        mirror_rbtn_group.addButton(self.mirror_none_rbtn)
        mirror_rbtn_group.addButton(self.mirror_right_rbtn)
        mirror_rbtn_group.setParent(mirror_radio_layout)

        #  --------------------------------------------------------------------
        smart_adjust_layout = QtWidgets.QHBoxLayout()
        msg = "Adjust hand, symmetry, spine and more."
        smart_label = QtWidgets.QLabel("Smart Adjust")
        smart_label.setStatusTip(msg)
        smart_label.setToolTip(msg)
        self.window()._toolTip_widgets.append(smart_label)
        self.enable_adjust_rbtn = QtWidgets.QRadioButton("Enable")
        self.enable_adjust_rbtn.setChecked(True)
        self.smart_adjust_btn = QtWidgets.QPushButton("Run")
        self.smart_adjust_btn.setStatusTip(msg)
        self.smart_adjust_btn.setToolTip(msg)
        self.smart_adjust_btn.setMaximumWidth(30)
        self.window()._toolTip_widgets.append(self.smart_adjust_btn)
        self.off_adjust_rbtn = QtWidgets.QRadioButton("Disable")
        smart_adjust_rbtn_group = QtWidgets.QButtonGroup()
        smart_adjust_rbtn_group.addButton(self.enable_adjust_rbtn)
        smart_adjust_rbtn_group.addButton(self.off_adjust_rbtn)
        smart_adjust_rbtn_group.setObjectName("smart_adjust_rbtn_group")
        smart_adjust_rbtn_group.setExclusive(True)
        smart_adjust_rbtn_group.setParent(smart_adjust_layout)

        smart_adjust_layout.addWidget(smart_label)
        smart_adjust_layout.insertStretch(1, 1)
        smart_adjust_layout.addWidget(self.enable_adjust_rbtn, 1)
        smart_adjust_layout.addWidget(self.off_adjust_rbtn, 1)
        smart_adjust_layout.addWidget(self.smart_adjust_btn)

        #  --------------------------------------------------------------------
        rerun_layout = QtWidgets.QHBoxLayout()
        self.create_embed_nodes_btn = QtWidgets.QPushButton("Create Embed Nodes")
        self.match_guides_toEmbed_btn = QtWidgets.QPushButton("Match Guides")
        rerun_layout.addWidget(self.create_embed_nodes_btn)
        rerun_layout.addWidget(self.match_guides_toEmbed_btn)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.run_all_settings_btn = QtWidgets.QPushButton("Create and Match (Run All)")
        msg = "Create, match, and smart adjust output."
        self.run_all_settings_btn.setToolTip(msg)
        self.run_all_settings_btn.setStatusTip(msg)
        self.window()._toolTip_widgets.append(self.run_all_settings_btn)
        self.delete_embed_nodes = QtWidgets.QPushButton("Delete Embed Nodes")

        #  --------------------------------------------------------------------
        # layout.addWidget(self.import_default_biped_btn)
        layout.addLayout(association_layout)
        layout.addWidget(self.src_geo_widget)
        layout.addLayout(h_layout_01)
        layout.addLayout(h_layout_02)
        layout.addLayout(mirror_radio_layout)
        layout.addLayout(smart_adjust_layout)
        layout.addLayout(rerun_layout)
        layout.addWidget(line)
        layout.addWidget(self.run_all_settings_btn)
        layout.addWidget(self.delete_embed_nodes)
        return widget

    def exportEmbedInfoWidget(self):
        widget = QtWidgets.QGroupBox("Create/Export Association Info")
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        widget.setLayout(layout)

        association_list_layout = QtWidgets.QHBoxLayout()
        association_btn_layout = QtWidgets.QVBoxLayout()
        self.association_list_widget = QtWidgets.QListWidget()
        self.window()._toolTip_widgets.append(self.association_list_widget)
        self.association_list_widget.setMaximumWidth(150)
        embed_nodes = afg_tools.DEFAULT_BIPED_POINTS
        self.association_list_widget.addItems(embed_nodes)

        msg = "Enable Match Position"
        self.enable_association_snap_cb = QtWidgets.QCheckBox(msg)
        msg = "Enable\nInteractive Associations"
        self.enable_association_btn = QtWidgets.QPushButton(msg)
        msg = "Make associations to guides based off selection."
        self.enable_association_btn.setToolTip(msg)
        self.enable_association_btn.setStatusTip(msg)
        self.window()._toolTip_widgets.append(self.enable_association_btn)
        self.mirror_association_btn = QtWidgets.QPushButton("Mirror Left->Right")
        msg = "Apply Default Associations"
        self.apply_default_association_btn = QtWidgets.QPushButton(msg)
        msg = "Start with the default and make edits."
        self.apply_default_association_btn.setToolTip(msg)
        self.apply_default_association_btn.setStatusTip(msg)
        self.window()._toolTip_widgets.append(self.apply_default_association_btn)
        self.import_association_btn = QtWidgets.QPushButton("Import Guide Associations")
        self.clear_association_btn = QtWidgets.QPushButton("Clear Associations")
        self.print_association_btn = QtWidgets.QPushButton("Print Association info")
        self.enable_association_snap_cb.setCheckable(True)
        self.enable_association_btn.setCheckable(True)

        association_btn_layout.addWidget(self.enable_association_snap_cb)
        association_btn_layout.addWidget(self.enable_association_btn)
        association_btn_layout.addWidget(self.mirror_association_btn)
        association_btn_layout.addWidget(self.apply_default_association_btn)
        association_btn_layout.addWidget(self.import_association_btn)
        association_btn_layout.addWidget(self.clear_association_btn)
        association_btn_layout.addWidget(self.print_association_btn)
        #  -------------------------------------------------------------------
        # msg = "Export association Info"
        # self.export_embed_path_widget = LoadImportWidget(file_contents=msg,
        #                                                  ext=[AFB_FILE_EXTENSION],
        #                                                  mode=0,
        #                                                  show_import_button=False)
        self.export_association_btn = QtWidgets.QPushButton("Export Association")
        self.export_association_btn.setStatusTip("Export association to file")
        association_list_layout.addWidget(self.association_list_widget)
        association_list_layout.addLayout(association_btn_layout)
        layout.addLayout(association_list_layout)
        # layout.addWidget(self.export_embed_path_widget)
        layout.addWidget(self.export_association_btn)
        self.visualizeAssociationEntry()
        return widget


class RelativeGuidePlacementWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(RelativeGuidePlacementWidget, self).__init__(parent=parent)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(self.mainLayout)
        # self.cb_manager = callbackManager.CallbackManager()
        self.ordered_hierarchy = []
        self.relativeGuide_dict = {}
        self.mainLayout.addWidget(self.ui())
        self.mainLayout.addStretch(1)
        self.connectSignals()

    def connectSignals(self):
        self.record_placement_btn.clicked.connect(self.recordInitialGuidePlacement)
        self.update_placement_btn.clicked.connect(self.updateGuidePlacement)
        self.add_skip_nodes_btn.clicked.connect(self.addSkipNodes)
        self.remove_skip_nodes_btn.clicked.connect(self.removeSkipNodes)
        self.default_skip_nodes_btn.clicked.connect(self.defaultSkipNodes)
        self.import_placement_btn.clicked.connect(self._importGuidePlacement)
        self.export_placement_btn.clicked.connect(self._exportGuidePlacement)

    def addSkipNodes(self, nodes=None):
        if not nodes:
            nodes = cmds.ls(sl=True, type="transform")
        if not nodes:
            return
        relative_guide_placement.SKIP_CRAWL_NODES.extend(nodes)
        tmp = relative_guide_placement.SKIP_CRAWL_NODES
        tmp = list(set(tmp))
        tmp.sort()
        tmp = [x for x in tmp if cmds.objExists("{}.isGearGuide".format(x))]
        relative_guide_placement.SKIP_CRAWL_NODES = tmp
        self.refreshSkipList()

    def removeSkipNodes(self, nodes=None):
        removed_items = []
        if nodes:
            for i in xrange(self.skip_crawl_list.count()):
                item = self.skip_crawl_list.item(i)
                if item.text() in nodes:
                    removed_items.append(item.text())
                    self.skip_crawl_list.removeItemWidget(item)
        else:
            item = self.skip_crawl_list.currentItem()
            if item:
                removed_items.append(item.text())
                # self.skip_crawl_list.removeItemWidget(item)
        for item in removed_items:
            relative_guide_placement.SKIP_CRAWL_NODES.remove(item)
        self.refreshSkipList()

    def defaultSkipNodes(self):
        relative_guide_placement.SKIP_CRAWL_NODES = list(relative_guide_placement.DEFAULT_SKIP_CRAWL_NODES)
        relative_guide_placement.SKIP_PLACEMENT_NODES = list(relative_guide_placement.DEFAULT_SKIP_PLACEMENT_NODES)
        self.refreshSkipList()

    def getSkipNodes(self):
        items = []
        for i in xrange(self.skip_crawl_list.count()):
            items.append(self.skip_crawl_list.item(i).text())
        return items

    @utils.viewport_off
    @utils.one_undo
    def recordInitialGuidePlacement(self):
        reference_mesh = self.src_geo_widget.text
        if reference_mesh == "" or not cmds.objExists(reference_mesh):
            msg = "No Source Mesh Provided!"
            self.window().statusBar().showMessage(msg, 3000)
            raise ValueError(msg)
        relativeGuide_dict = {}
        ordered_hierarchy = []
        relative_guide_placement.crawlHierarchy(_guideRootNode(),
                                                ordered_hierarchy,
                                                self.getSkipNodes())
        reference_mesh = pm.PyNode(reference_mesh)
        increment_value = 100 / len(ordered_hierarchy)
        starting_val = 0
        dance = itertools.cycle(DANCE_EMOTICON)

        gen = relative_guide_placement.yieldGuideRelativeDictionary(reference_mesh,
                                                                    ordered_hierarchy,
                                                                    relativeGuide_dict)
        for result in gen:
            msg = "{}% completed... {}".format(int(starting_val), dance.next())
            self.window().statusBar().showMessage(msg)
            starting_val = starting_val + increment_value
            # if (starting_val % UI_REFRESH_RATE == 0):
                # QtWidgets.QApplication.processEvents()

        self.relativeGuide_dict = relativeGuide_dict
        self.ordered_hierarchy = ordered_hierarchy
        msg = "Initial Guide Placement Recorded!"
        self.window().statusBar().showMessage(msg, 3000)

    @utils.viewport_off
    @utils.one_undo
    def updateGuidePlacement(self):
        if not self.ordered_hierarchy:
            msg = "Record initial Placement first!"
            self.window().statusBar().showMessage(msg, 3000)
            raise ValueError(msg)

        increment_value = 100 / len(self.ordered_hierarchy)
        starting_val = 0
        dance = itertools.cycle(DANCE_EMOTICON)
        for x in relative_guide_placement.updateGuidePlacement(self.ordered_hierarchy,
                                                               self.relativeGuide_dict):
            msg = "{}% completed... {}".format(int(starting_val), dance.next())
            self.window().statusBar().showMessage(msg)
            starting_val = starting_val + increment_value
            # if (starting_val % UI_REFRESH_RATE == 0):
                # QtWidgets.QApplication.processEvents()
        self.window().statusBar().showMessage("Guides plcement updated!", 3000)

    def _importGuidePlacement(self):
        tmp = " ".join(["*.{}".format(x) for x in [RELATIVE_FILE_EXTENSION]])
        # TODO Make the file extension here more verbose
        all_exts = ["Relative Placement Guides Files ({})".format(tmp), "All Files (*.*)"]
        all_exts = ";;".join(all_exts)
        file_path = fileDialog("/", ext=all_exts, mode=1)
        (self.relativeGuide_dict,
         self.ordered_hierarchy) = relative_guide_placement.importGuidePlacement(file_path)
        print("Relative Guide Placement Imported: {}".format(file_path))

    def _exportGuidePlacement(self):
        tmp = " ".join(["*.{}".format(x) for x in [RELATIVE_FILE_EXTENSION]])
        # TODO Make the file extension here more verbose
        all_exts = ["Relative Placement Guides Files ({})".format(tmp), "All Files (*.*)"]
        all_exts = ";;".join(all_exts)
        file_path = fileDialog("/", ext=all_exts, mode=0)
        # relative_guide_placement.importGuidePlacement(file_path)
        if not self.relativeGuide_dict or not self.ordered_hierarchy:
            msg = "Record Placement!"
            self.window().statusBar().showMessage(msg)
            raise ValueError(msg)
            return
        data = {}
        data["relativeGuide_dict"] = self.relativeGuide_dict
        data["ordered_hierarchy"] = self.ordered_hierarchy
        relative_guide_placement._exportData(data, file_path)
        msg = "Relative Guide position exported: {}".format(file_path)
        print(msg)
        self.window().statusBar().showMessage(msg)
        return self.relativeGuide_dict, self.ordered_hierarchy, file_path

    def refreshSkipList(self):
        self.skip_crawl_list.clear()
        nodes = relative_guide_placement.SKIP_CRAWL_NODES
        nodes.sort()
        self.skip_crawl_list.addItems(nodes)

    def ui(self):
        widget = QtWidgets.QGroupBox("Relative Guide Placement Settings")
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        widget.setLayout(layout)
        self.src_geo_widget = SelectComboBoxRefreshWidget("Source Mesh ")
        self.window()._toolTip_widgets.append(self.src_geo_widget.select_src_mesh_btn)

        list_layout_01 = QtWidgets.QHBoxLayout()
        list_layout_02 = QtWidgets.QVBoxLayout()
        list_layout_03 = QtWidgets.QVBoxLayout()
        list_layout_03.setAlignment(QtCore.Qt.AlignTop)
        self.skip_crawl_list = QtWidgets.QListWidget()
        self.skip_crawl_list.setToolTip("Skip node hierarchy crawling")
        self.skip_crawl_list.setStatusTip("Skip node hierarchy crawling")
        self.window()._toolTip_widgets.append(self.skip_crawl_list)
        self.refreshSkipList()
        self.skip_crawl_list.setMaximumWidth(125)
        self.skip_crawl_list.setMaximumHeight(200)
        self.add_skip_nodes_btn = QtWidgets.QPushButton("< Add Skip Node")
        self.remove_skip_nodes_btn = QtWidgets.QPushButton("< Remove Node")
        self.default_skip_nodes_btn = QtWidgets.QPushButton("< Set Default nodes")
        list_layout_02.addWidget(self.skip_crawl_list)
        list_layout_03.addWidget(self.add_skip_nodes_btn)
        list_layout_01.addLayout(list_layout_02)
        list_layout_01.addLayout(list_layout_03)
        list_layout_03.addWidget(self.remove_skip_nodes_btn)
        list_layout_03.addWidget(self.default_skip_nodes_btn)

        io_layout = QtWidgets.QHBoxLayout()
        msg = "Record\nRelative Guide Placement"
        self.record_placement_btn = QtWidgets.QPushButton(msg)
        # TODO - Look into using a gradient for a type of indicator of progress
        # self.record_placement_btn.setStyleSheet("QPushButton {\
    # background-color: qlineargradient(x1: 0, x2: 1, stop: 0 white, stop: 1 green, stop: .5 red);}")
    # background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,stop: 0 white, stop: 0.4 gray, stop: 1 green);}")
        msg = "Import\nRelative Guide Placement"
        self.import_placement_btn = QtWidgets.QPushButton(msg)
        io_layout.addWidget(self.record_placement_btn)
        io_layout.addWidget(self.import_placement_btn)
        msg = "Update\nGuide Placement"
        self.update_placement_btn = QtWidgets.QPushButton(msg)
        msg = "Export Guide Placement"
        self.export_placement_btn = QtWidgets.QPushButton(msg)

        layout.addWidget(self.src_geo_widget)
        layout.addLayout(list_layout_01)
        layout.addLayout(io_layout)
        layout.addWidget(self.update_placement_btn)
        layout.addWidget(self.export_placement_btn)
        return widget


class AutoFitGuideToolWidget(QtWidgets.QWidget):
    """docstring for AutoFitGuideToolWidget"""
    def __init__(self, parent=None):
        super(AutoFitGuideToolWidget, self).__init__(parent=parent)
        self.setWindowTitle("AFG Tool")
        self.setContentsMargins(0, 0, 0, 0)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.setSpacing(0)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(self.mainLayout)
        # self.mainLayout.addWidget(self.loadSettingsWidget())
        self.mainLayout.addWidget(self.afgTabWidget())

        self.afb_widget = AutoFitBipedWidget(parent=parent)
        # self.afb_widget.model_path = self.model_path_widget
        # self.afb_widget.guide_path = self.guide_path_widget
        self.relative_placement_widget = RelativeGuidePlacementWidget(parent=parent)
        # self.relative_placement_widget.setToolTip("Placeholder!")
        # self.relative_placement_widget.setStatusTip("Placeholder!")
        # self.window()._toolTip_widgets.append(self.relative_placement_widget)
        self.afg_tab_widget.addTab(self.afb_widget, "Auto Fit Biped")
        self.afg_tab_widget.addTab(self.relative_placement_widget,
                                   "Relative Guide Placement")

    def loadSettingsWidget(self):
        self.load_settings_widget = QtWidgets.QGroupBox("Load Model | Guide")
        self.load_settings_layout = QtWidgets.QVBoxLayout()
        self.load_settings_widget.setLayout(self.load_settings_layout)
        self.model_path_widget = LoadImportWidget(file_contents="Models",
                                                  import_type="maya",
                                                  ext=["ma", "mb"])
        self.load_settings_layout.addWidget(self.model_path_widget)
        self.model_path_widget.setToolTip("Select path to model, if needed.")
        self.model_path_widget.setStatusTip("Select path to model, if needed.")
        self.window()._toolTip_widgets.append(self.model_path_widget)

        self.guide_path_widget = LoadImportWidget(file_contents="Guides",
                                                  import_type="mgear",
                                                  ext=["sgt"])
        self.guide_path_widget.setToolTip("Select path to Guides, if needed.")
        self.guide_path_widget.setStatusTip("Select path to Guides, if needed.")
        self.window()._toolTip_widgets.append(self.guide_path_widget)
        self.load_settings_layout.addWidget(self.guide_path_widget)
        return self.load_settings_widget

    def afgTabWidget(self):
        self.afg_tab_widget = QtWidgets.QTabWidget()
        self.afg_tab_widget.setContentsMargins(0, 0, 0, 0)
        return self.afg_tab_widget


class AutoFitGuideTool(QtWidgets.QMainWindow):
    """docstring for AutoFitGuideTool"""
    def __init__(self, parent=None):
        super(AutoFitGuideTool, self).__init__(parent=parent)
        self.afg_callback_managers = []
        self._toolTip_widgets = []
        self.parent = parent
        self.setWindowTitle(WINDOW_TITLE)
        self.setObjectName(self.__class__.__name__)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.statusBar().showMessage("Starting up...", 3000)
        self.setCentralWidget(AutoFitGuideToolWidget(parent=self))
        self.connectToolTips()
        settings = QtCore.QSettings("mGear's", "AutoFitGuideTool")
        if settings:
            self.restoreGeometry(settings.value("geometry"))
            self.restoreState(settings.value("windowState"))

    def connectToolTips(self):
        for widget in self.window()._toolTip_widgets:
            widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.ToolTip:
            tooltip = obj.toolTip()
            if tooltip:
                self.statusBar().showMessage(tooltip, 3000)
                return True
        return False

    def closeEvent(self, evnt):
        settings = QtCore.QSettings("mGear's", "AutoFitGuideTool")
        settings.setValue("windowState", self.saveState())
        settings.setValue("geometry", self.saveGeometry())
        for manager in getattr(self, "afg_callback_managers", []):
            manager.removeAllManagedCB()
        try:
            super(AutoFitGuideTool, self).closeEvent(evnt)
        except TypeError:
            pass
