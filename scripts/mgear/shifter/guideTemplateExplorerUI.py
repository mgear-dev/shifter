# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:/repo/mgear_dist/framework/shifter/scripts/mgear/shifter/guideTemplateExplorerUI.ui'
#
# Created: Wed Dec  5 18:28:29 2018
#      by: pyside2-uic  running on PySide2 2.0.0~alpha0
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(412, 394)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.explorer_treeView = QtWidgets.QTreeView(self.centralwidget)
        self.explorer_treeView.setObjectName("explorer_treeView")
        self.gridLayout.addWidget(self.explorer_treeView, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 412, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuGuide = QtWidgets.QMenu(self.menubar)
        self.menuGuide.setObjectName("menuGuide")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionBuild = QtWidgets.QAction(MainWindow)
        self.actionBuild.setObjectName("actionBuild")
        self.actionImport = QtWidgets.QAction(MainWindow)
        self.actionImport.setObjectName("actionImport")
        self.actionImport_Partial = QtWidgets.QAction(MainWindow)
        self.actionImport_Partial.setObjectName("actionImport_Partial")
        self.actionOpen = QtWidgets.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QtWidgets.QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSave_As = QtWidgets.QAction(MainWindow)
        self.actionSave_As.setObjectName("actionSave_As")
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSave_As)
        self.menuGuide.addAction(self.actionBuild)
        self.menuGuide.addSeparator()
        self.menuGuide.addAction(self.actionImport)
        self.menuGuide.addAction(self.actionImport_Partial)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuGuide.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "MainWindow", None, -1))
        self.menuFile.setTitle(QtWidgets.QApplication.translate("MainWindow", "File", None, -1))
        self.menuGuide.setTitle(QtWidgets.QApplication.translate("MainWindow", "Guide", None, -1))
        self.actionBuild.setText(QtWidgets.QApplication.translate("MainWindow", "Build", None, -1))
        self.actionImport.setText(QtWidgets.QApplication.translate("MainWindow", "Import", None, -1))
        self.actionImport_Partial.setText(QtWidgets.QApplication.translate("MainWindow", "Import Partial", None, -1))
        self.actionOpen.setText(QtWidgets.QApplication.translate("MainWindow", "Open", None, -1))
        self.actionSave.setText(QtWidgets.QApplication.translate("MainWindow", "Save", None, -1))
        self.actionSave_As.setText(QtWidgets.QApplication.translate("MainWindow", "Save As ...", None, -1))

