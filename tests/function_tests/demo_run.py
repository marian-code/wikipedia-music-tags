from demo import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets

class Window(Ui_MainWindow):

    def setup_overlay(self):
        self.browse_button.clicked.connect(self.folder)

    def folder(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory()
        self.display_dir.setText('{}'.format(directory))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Window()
    ui.setupUi(MainWindow)
    ui.setup_overlay()
    MainWindow.show()
    sys.exit(app.exec_())