from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QLabel,  QVBoxLayout, QWidget, QTableWidget, QApplication
from PyQt5.QtCore import pyqtProperty, pyqtSlot, Qt
import sys

class CustomWidget(QWidget):
    def __init__(self, text, img, parent=None):
        QWidget.__init__(self, parent)

        self._text = text
        self._img = img

        self.setLayout(QVBoxLayout())
        self.lbPixmap = QLabel(self)
        self.lbText = QLabel(self)
        self.lbText.setAlignment(Qt.AlignCenter)

        self.layout().addWidget(self.lbPixmap)
        self.layout().addWidget(self.lbText)

        self.initUi()

    def initUi(self):
        self.lbPixmap.setPixmap(QPixmap(self._img).scaled(self.lbPixmap.size(),Qt.KeepAspectRatio))
        self.lbText.setText(self._text)


    @pyqtProperty(str)
    def img(self):
        return self._img

    @img.setter
    def total(self, value):
        if self._img == value:
            return
        self._img = value
        self.initUi()

    @pyqtProperty(str)
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if self._text == value:
            return
        self._text = value
        self.initUi()

class TableWidget(QTableWidget):
    def __init__(self, parent=None):
        QTableWidget.__init__(self, parent)

        self.actualCol = -1
        self.setColumnCount(1)
        self.setRowCount(1)
        for i in range(self.columnCount()):
            self.add_pic()

        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.cellClicked.connect(self.onCellClicked)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        
    @pyqtSlot(int, int)
    def onCellClicked(self, row, column):
        w = self.cellWidget(row, column)
        if w.text == "00":
            print("adding")
            self.add_pic()
        print(w.text, w.img)

    def add_pic(self):

        if self.actualCol < 4:
            self.actualCol += 1
            if self.rowCount() == 1:
                self.setColumnCount(self.columnCount() + 1)
        elif self.actualCol == 4:
            self.actualCol = 0
            self.setRowCount(self.rowCount() + 1)

        i = self.rowCount() - 1
        j = self.actualCol
        lb = CustomWidget(str(i) + str(j), "amorphis.jpg")
        self.setCellWidget(i, j, lb)

        self.resizeColumnsToContents()
        self.resizeRowsToContents()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    tw = TableWidget()
    #tw.add_pic(3, 4)

    tw.show()
    sys.exit(app.exec_())