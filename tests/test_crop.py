import sys
from PyQt5 import QtGui, QtCore, QtWidgets

from PyQt5.QtWidgets import QHBoxLayout, QSizeGrip, QRubberBand, QWidget, QStyleFactory
from PyQt5.QtCore import Qt


class ResizableRubberBand(QtWidgets.QWidget):
    """Wrapper to make QRubberBand mouse-resizable using QSizeGrip

    Source: http://stackoverflow.com/a/19067132/435253
    """
    def __init__(self, parent=None):
        super(ResizableRubberBand, self).__init__(parent)

        self.setWindowFlags(Qt.SubWindow)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.grip1 = QSizeGrip(self)
        self.grip2 = QSizeGrip(self)
        self.layout.addWidget(self.grip1, 0, Qt.AlignLeft | Qt.AlignTop)
        self.layout.addWidget(self.grip2, 0, Qt.AlignRight | Qt.AlignBottom)

        self.rubberband = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberband.setStyle(QStyleFactory.create("Fusion"))
        self.rubberband.move(0, 0)
        self.rubberband.show()
        self.show()

    def resizeEvent(self, event):
        self.rubberband.resize(self.size())


class QExampleLabel (QtWidgets.QLabel):

    def __init__(self, parentQWidget=None):
        super(QExampleLabel, self).__init__(parentQWidget)
        self.initUI()

    def initUI(self):
        self.setPixmap(QtGui.QPixmap('input.png'))

    def mousePressEvent(self, eventQMouseEvent):
        self.originQPoint = eventQMouseEvent.pos()
        self.currentQRubberBand = ResizableRubberBand(self)
        self.currentQRubberBand.setGeometry(QtCore.QRect(self.originQPoint, QtCore.QSize()))
        self.currentQRubberBand.show()

    def mouseMoveEvent(self, eventQMouseEvent):
        self.currentQRubberBand.setGeometry(QtCore.QRect(self.originQPoint, eventQMouseEvent.pos()).normalized())

    def mouseReleaseEvent(self, eventQMouseEvent):
        #self.currentQRubberBand.hide()
        currentQRect = self.currentQRubberBand.geometry()
        #self.currentQRubberBand.deleteLater()
        cropQPixmap = self.pixmap().copy(currentQRect)
        cropQPixmap.save('output.png')

if __name__ == '__main__':
    print(QStyleFactory.keys())

    myQApplication = QtWidgets.QApplication(sys.argv)
    myQExampleLabel = QExampleLabel()
    myQExampleLabel.show()
    sys.exit(myQApplication.exec_())