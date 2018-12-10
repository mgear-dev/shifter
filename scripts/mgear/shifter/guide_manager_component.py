import os
from functools import partial

import pymel.core as pm

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from mgear.core import pyqt

from mgear.vendor.Qt import QtCore, QtWidgets, QtGui

from mgear import shifter
from mgear.shifter import guide_manager
from mgear.shifter import guide_manager_component_ui as gmcUI


class GuideManagerComponentUI(QtWidgets.QDialog, gmcUI.Ui_Form):

    def __init__(self, parent=None):
        super(GuideManagerComponentUI, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setupUi(self)
        self.component_listView.setAcceptDrops(False)
        self.component_listView.setDragEnabled(True)
        self.component_listView.setDropIndicatorShown(False)


class GuideManagerComponent(MayaQWidgetDockableMixin, QtWidgets.QDialog):

    def __init__(self, parent=None):
        self.toolName = "shifterComponentManager"
        super(GuideManagerComponent, self).__init__(parent=parent)

        self.gmcUIInst = GuideManagerComponentUI()

        self.start_dir = pm.workspace(q=True, rootDirectory=True)

        self.__proxyModel = QtCore.QSortFilterProxyModel(self)
        self.gmcUIInst.component_listView.setModel(self.__proxyModel)

        self.create_window()
        self.create_layout()
        self.create_connections()
        self._refreshList()

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)


    def create_window(self):

        self.setObjectName(self.toolName)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle("Shifter Guide Component")
        self.resize(280, 600)

    def create_layout(self):

        self.gmc_layout = QtWidgets.QVBoxLayout()
        self.gmc_layout.addWidget(self.gmcUIInst)
        self.gmc_layout.setContentsMargins(3, 3, 3, 3)

        self.setLayout(self.gmc_layout)

    def get_component_list(self):
        comp_list = []
        compDir = shifter.getComponentDirectories()
        trackLoadComponent = []
        for path, comps in compDir.iteritems():
            for comp_name in comps:
                if comp_name in trackLoadComponent:
                    pm.displayWarning(
                        "Custom component name: %s, already in default "
                        "components. Names should be unique. This component is"
                        " not loaded" % comp_name)
                    continue
                else:
                    trackLoadComponent.append(comp_name)

                if not os.path.exists(os.path.join(path,
                                                   comp_name, "__init__.py")):
                    continue

                module = shifter.importComponentGuide(comp_name)
                reload(module)
                comp_list.append(module.TYPE)
        return comp_list

    def setSourceModel(self, model):
        """Set the source model for the listview

        Args:
            model (Qt model): QtCore.QSortFilterProxyModel
        """
        self.__proxyModel.setSourceModel(model)

    def _refreshList(self):
        """Refresh listview content
        """
        model = QtGui.QStandardItemModel(self)
        for c_node in self.get_component_list():
            model.appendRow(QtGui.QStandardItem(c_node))
        self.setSourceModel(model)

    ###########################
    # "right click context menu"
    ###########################

    def _component_menu(self, QPos):
        """Create the component list rightclick menu

        Args:
            QPos (QPos): Position

        Returns:
            None: None
        """
        comp_widget = self.gmcUIInst.component_listView
        currentSelection = comp_widget.selectedIndexes()
        if currentSelection is None:
            return
        self.comp_menu = QtWidgets.QMenu()
        parentPosition = comp_widget.mapToGlobal(QtCore.QPoint(0, 0))
        menu_item_01 = self.comp_menu.addAction("Draw Component")
        self.comp_menu.addSeparator()
        menu_item_02 = self.comp_menu.addAction("Component Folders")
        menu_item_03 = self.comp_menu.addAction("Refresh List")

        menu_item_01.triggered.connect(self.draw_component)
        menu_item_02.triggered.connect(self._refreshList)
        menu_item_03.triggered.connect(self._refreshList)

        self.comp_menu.move(parentPosition + QPos)
        self.comp_menu.show()

    ###########################
    # create connections SIGNALS
    ###########################
    def create_connections(self):

        self.gmcUIInst.search_lineEdit.textChanged.connect(
            self.filter_changed)

        self.gmcUIInst.component_listView.clicked.connect(self.update_info)
        self.gmcUIInst.component_listView.doubleClicked.connect(
            self.draw_component)

        # connect menu
        self.gmcUIInst.component_listView.setContextMenuPolicy(
            QtCore.Qt.CustomContextMenu)
        self.gmcUIInst.component_listView.customContextMenuRequested.connect(
            self._component_menu)

    def test(self):
        print "Temp Test"

    def update_info(self):
        item = self.gmcUIInst.component_listView.selectedIndexes()[0]
        comp_name = item.data()
        module = shifter.importComponentGuide(comp_name)
        reload(module)
        self.gmcUIInst.info_plainTextEdit.setPlainText(module.DESCRIPTION)

    def draw_component(self):
        for x in self.gmcUIInst.component_listView.selectedIndexes():
            guide_manager.draw_comp(x.data())

    def filter_changed(self, filter):
        """Filter out the elements in the list view

        """
        regExp = QtCore.QRegExp(filter,
                                QtCore.Qt.CaseSensitive,
                                QtCore.QRegExp.Wildcard
                                )
        self.__proxyModel.setFilterRegExp(regExp)
        self.gmcUIInst.info_plainTextEdit.setPlainText("")


if __name__ == "__main__":

    pyqt.showDialog(GuideManagerComponent, dockable=True)
