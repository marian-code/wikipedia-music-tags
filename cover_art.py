# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'cover_art.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(301, 166)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.gridLayout_2 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.size_spinbox_X = QtWidgets.QSpinBox(Dialog)
        self.size_spinbox_X.setMinimum(10)
        self.size_spinbox_X.setMaximum(2000)
        self.size_spinbox_X.setProperty("value", 1400)
        self.size_spinbox_X.setObjectName("size_spinbox_X")
        self.gridLayout.addWidget(self.size_spinbox_X, 0, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.size_spinbox_Y = QtWidgets.QSpinBox(Dialog)
        self.size_spinbox_Y.setMinimum(10)
        self.size_spinbox_Y.setMaximum(2000)
        self.size_spinbox_Y.setProperty("value", 1400)
        self.size_spinbox_Y.setObjectName("size_spinbox_Y")
        self.gridLayout.addWidget(self.size_spinbox_Y, 1, 1, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.ca_clipboard = QtWidgets.QCheckBox(Dialog)
        self.ca_clipboard.setChecked(True)
        self.ca_clipboard.setObjectName("ca_clipboard")
        self.gridLayout_2.addWidget(self.ca_clipboard, 1, 0, 1, 1)
        self.ca_file = QtWidgets.QCheckBox(Dialog)
        self.ca_file.setObjectName("ca_file")
        self.gridLayout_2.addWidget(self.ca_file, 2, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout_2.addWidget(self.buttonBox, 3, 0, 1, 1)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_2.setText(_translate("Dialog", "X:"))
        self.label_3.setText(_translate("Dialog", "Y:"))
        self.label.setText(_translate("Dialog", "Select dimensions (ratio is fixed)"))
        self.ca_clipboard.setText(_translate("Dialog", "Copy Cover Art to clipboard"))
        self.ca_file.setText(_translate("Dialog", "Export Cover Art to file (Folder.jpg)"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

