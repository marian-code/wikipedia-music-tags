# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'cover_art_base.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_cover_art_search(object):
    def setupUi(self, cover_art_search):
        cover_art_search.setObjectName("cover_art_search")
        cover_art_search.resize(1000, 650)
        self.verticalLayout = QtWidgets.QVBoxLayout(cover_art_search)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(cover_art_search)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.query = QtWidgets.QLineEdit(cover_art_search)
        self.query.setMaximumSize(QtCore.QSize(200, 16777215))
        self.query.setObjectName("query")
        self.horizontalLayout.addWidget(self.query)
        self.search_button = QtWidgets.QPushButton(cover_art_search)
        self.search_button.setObjectName("search_button")
        self.horizontalLayout.addWidget(self.search_button)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.progressBar = QtWidgets.QProgressBar(cover_art_search)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.horizontalLayout.addWidget(self.progressBar)
        self.browser_button = QtWidgets.QPushButton(cover_art_search)
        self.browser_button.setObjectName("browser_button")
        self.horizontalLayout.addWidget(self.browser_button)
        self.load_button = QtWidgets.QPushButton(cover_art_search)
        self.load_button.setObjectName("load_button")
        self.horizontalLayout.addWidget(self.load_button)
        self.cancel_button = QtWidgets.QPushButton(cover_art_search)
        self.cancel_button.setObjectName("cancel_button")
        self.horizontalLayout.addWidget(self.cancel_button)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(cover_art_search)
        QtCore.QMetaObject.connectSlotsByName(cover_art_search)

    def retranslateUi(self, cover_art_search):
        _translate = QtCore.QCoreApplication.translate
        cover_art_search.setWindowTitle(_translate("cover_art_search", "Cover Art"))
        self.label.setText(_translate("cover_art_search", "Query:"))
        self.search_button.setText(_translate("cover_art_search", "Search"))
        self.browser_button.setText(_translate("cover_art_search", "Show in browser"))
        self.load_button.setText(_translate("cover_art_search", "Load more"))
        self.cancel_button.setText(_translate("cover_art_search", "Cancel"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    cover_art_search = QtWidgets.QDialog()
    ui = Ui_cover_art_search()
    ui.setupUi(cover_art_search)
    cover_art_search.show()
    sys.exit(app.exec_())

