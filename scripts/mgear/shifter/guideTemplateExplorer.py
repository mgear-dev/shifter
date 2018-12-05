import pymel.core as pm


import mgear.shifter.guideTemplateExplorerUI as gteUI
from mgear.shifter import io
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from mgear.core import pyqt
from mgear.vendor.Qt import QtCore, QtWidgets
from mgear.vendor.qjsonmodel import QJsonModel


class GuideTemplateExplorerUI(QtWidgets.QMainWindow, gteUI.Ui_MainWindow):

    def __init__(self, parent=None):
        super(GuideTemplateExplorerUI, self).__init__(parent)
        self.setupUi(self)


class GuideTemplateExplorer(MayaQWidgetDockableMixin, QtWidgets.QDialog):

    def __init__(self, parent=None):
        self.toolName = "shifterGuideTemplateExplorer"
        super(GuideTemplateExplorer, self).__init__(parent=parent)
        self.gteUIInst = GuideTemplateExplorerUI()
        self.__model = QJsonModel()
        self.gteUIInst.explorer_treeView.setModel(self.__model)

        self.start_dir = pm.workspace(q=True, rootDirectory=True)

        self.create_window()
        self.create_layout()
        self.create_connections()

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

    def create_window(self):

        self.setObjectName(self.toolName)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle("Guide Template Explorer")
        self.resize(300, 330)

    def create_layout(self):

        self.gte_layout = QtWidgets.QVBoxLayout()
        self.gte_layout.addWidget(self.gteUIInst)

        self.setLayout(self.gte_layout)

    ###########################
    # create connections SIGNALS
    ###########################
    def create_connections(self):
        self.gteUIInst.actionOpen.triggered.connect(self.open_template)
        self.gteUIInst.actionBuild.triggered.connect(self.build_template)

    #############
    # SLOTS
    #############
    def open_template(self):
        template = io._import_guide_template()
        self.__model.load(template)
        
    def build_template(self):
        template = self.__model.json()
        io.build_from_file(conf=template)


def open_guide_template_explorer(*args):

    pyqt.showDialog(GuideTemplateExplorer, dockable=True)


if __name__ == "__main__":

    pyqt.showDialog(GuideTemplateExplorer, dockable=True)
