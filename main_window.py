# Form implementation generated from reading ui file '.\main.ui'
#
# Created by: PyQt6 UI code generator 6.7.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_mainWindow(object):
    def setupUi(self, mainWindow):
        mainWindow.setObjectName("mainWindow")
        mainWindow.resize(782, 546)
        mainWindow.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
        mainWindow.setTabShape(QtWidgets.QTabWidget.TabShape.Rounded)
        self.centralwidget = QtWidgets.QWidget(parent=mainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.scrollArea = QtWidgets.QScrollArea(parent=self.centralwidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 762, 467))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.imageLabel = QtWidgets.QLabel(parent=self.scrollAreaWidgetContents)
        self.imageLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setObjectName("imageLabel")
        self.verticalLayout.addWidget(self.imageLabel)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout.addWidget(self.scrollArea, 0, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.folderPathSelectorButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.folderPathSelectorButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.folderPathSelectorButton.setFlat(False)
        self.folderPathSelectorButton.setObjectName("folderPathSelectorButton")
        self.horizontalLayout.addWidget(self.folderPathSelectorButton)
        self.line_3 = QtWidgets.QFrame(parent=self.centralwidget)
        self.line_3.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line_3.setObjectName("line_3")
        self.horizontalLayout.addWidget(self.line_3)
        self.prevButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.prevButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.prevButton.setFlat(True)
        self.prevButton.setObjectName("prevButton")
        self.horizontalLayout.addWidget(self.prevButton)
        self.line = QtWidgets.QFrame(parent=self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout.addWidget(self.line)
        self.nextButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.nextButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.nextButton.setFlat(True)
        self.nextButton.setObjectName("nextButton")
        self.horizontalLayout.addWidget(self.nextButton)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.catListComboBox = QtWidgets.QComboBox(parent=self.centralwidget)
        self.catListComboBox.setMinimumSize(QtCore.QSize(150, 0))
        self.catListComboBox.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.catListComboBox.setEditable(True)
        self.catListComboBox.setObjectName("catListComboBox")
        self.horizontalLayout.addWidget(self.catListComboBox)
        self.addCatButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.addCatButton.setMaximumSize(QtCore.QSize(45, 16777215))
        self.addCatButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.addCatButton.setObjectName("addCatButton")
        self.horizontalLayout.addWidget(self.addCatButton)
        self.delCatButton = QtWidgets.QPushButton(parent=self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.delCatButton.sizePolicy().hasHeightForWidth())
        self.delCatButton.setSizePolicy(sizePolicy)
        self.delCatButton.setMinimumSize(QtCore.QSize(0, 0))
        self.delCatButton.setMaximumSize(QtCore.QSize(45, 16777215))
        self.delCatButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.delCatButton.setObjectName("delCatButton")
        self.horizontalLayout.addWidget(self.delCatButton)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.buttonsGridLayout = QtWidgets.QGridLayout()
        self.buttonsGridLayout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMinimumSize)
        self.buttonsGridLayout.setSpacing(6)
        self.buttonsGridLayout.setObjectName("buttonsGridLayout")
        self.gridLayout.addLayout(self.buttonsGridLayout, 2, 0, 1, 1)
        mainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(parent=mainWindow)
        self.statusbar.setObjectName("statusbar")
        mainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(mainWindow)
        QtCore.QMetaObject.connectSlotsByName(mainWindow)

    def retranslateUi(self, mainWindow):
        _translate = QtCore.QCoreApplication.translate
        mainWindow.setWindowTitle(_translate("mainWindow", "Image Sorter"))
        self.imageLabel.setText(_translate("mainWindow", "Select a folder to get started!"))
        self.folderPathSelectorButton.setText(_translate("mainWindow", "Select Folder"))
        self.prevButton.setText(_translate("mainWindow", "< Prev"))
        self.nextButton.setText(_translate("mainWindow", "Next >"))
        self.catListComboBox.setPlaceholderText(_translate("mainWindow", "Category"))
        self.addCatButton.setText(_translate("mainWindow", "Add"))
        self.delCatButton.setText(_translate("mainWindow", "Del"))
