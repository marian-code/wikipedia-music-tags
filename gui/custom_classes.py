from os.path import basename, isfile

from wiki_music import DIR_FILE
from wiki_music.gui.qt_importer import (Property, QBuffer, QByteArray,
                                        QFileDialog, QHBoxLayout, QImage,
                                        QIODevice, QLabel, QPixmap, QRect,
                                        QResizeEvent, QRubberBand, QSize,
                                        QSizeGrip, QSizePolicy,
                                        QSortFilterProxyModel, QStandardItem,
                                        QStandardItemModel, QStyleFactory, Qt,
                                        QTableWidget, QVBoxLayout, QWidget)
from wiki_music.utilities.gui_utils import get_music_path

__all__ = ["NumberSortModel", "CustomQStandardItem", "ImageTable",
           "ResizableRubberBand"]


class NumberSortModel(QSortFilterProxyModel):

    def lessThan(self, left_index, right_index):

        left_var = left_index.data(Qt.EditRole)
        right_var = right_index.data(Qt.EditRole)

        try:
            return float(left_var) < float(right_var)
        except (ValueError, TypeError):
            pass

        try:
            return left_var < right_var
        except TypeError:  # in case of NoneType
            return True


class CustomQStandardItem(QStandardItem):
    """Overrides default methods so only the filename is "displayed"
    even though the object stores the full path
    """

    def data(self, role):
        if role != Qt.DisplayRole:
            return super(CustomQStandardItem, self).data(role)
        else:
            filtered = super(CustomQStandardItem, self).data(role)
            if isfile(filtered):
                return basename(filtered)
            else:
                return filtered

    def real_data(self, role):
        return super(CustomQStandardItem, self).data(role)

    def text(self):
        text_text = super(CustomQStandardItem, self).text()
        text_data = self.real_data(Qt.DisplayRole)

        if len(text_data) > len(text_text):
            return text_data
        else:
            return text_text


class CustomQStandardItemModel(QStandardItemModel):

    def col_index(self, name):

        for column in range(self.columnCount()):
            if self.headerData(column, Qt.Horizontal) == name:
                return column

        return None


class ImageWidget(QWidget):

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
        image = QImage()
        image.loadFromData(self._img)
        self.lbPixmap.setPixmap(QPixmap(image).scaledToWidth(150))
        self.lbText.setText(self._text)

    @Property(str)
    def img(self):
        return self._img

    @img.setter
    def total(self, value):
        if self._img == value:
            return
        self._img = value
        self.initUi()

    @Property(str)
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if self._text == value:
            return
        self._text = value
        self.initUi()


class ImageTable(QTableWidget):

    def __init__(self, parent=None):
        QTableWidget.__init__(self, parent)

        self.max_columns = 4
        self.actualCol = -1
        self.setColumnCount(1)
        self.setRowCount(1)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        # self.cellClicked.connect(self.onCellClicked)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

    """
    @Slot(int, int)
    def onCellClicked(self, row, column):
        w = self.cellWidget(row, column)
        print(row, column)
    """

    def add_pic(self, label, picture):

        if self.actualCol < self.max_columns:
            self.actualCol += 1
            if self.rowCount() == 1:
                self.setColumnCount(self.columnCount() + 1)
        elif self.actualCol == self.max_columns:
            self.actualCol = 0
            self.setRowCount(self.rowCount() + 1)
        else:
            # TODO raise some exception
            pass

        i = self.rowCount() - 1
        j = self.actualCol
        lb = ImageWidget(label, picture)
        self.setCellWidget(i, j, lb)

        self.resizeColumnsToContents()
        self.resizeRowsToContents()


class ResizableRubberBand(QWidget):
    """Wrapper to make QRubberBand mouse-resizable using QSizeGrip

    Source: http://stackoverflow.com/a/19067132/435253
    """

    def __init__(self, parent=None):
        super(ResizableRubberBand, self).__init__(parent)

        self.aspect_ratio = None

        self.setWindowFlags(Qt.SubWindow)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.grip1 = QSizeGrip(self)
        self.grip2 = QSizeGrip(self)
        self.grip3 = QSizeGrip(self)
        self.grip4 = QSizeGrip(self)
        self.layout.addWidget(self.grip1, 0, Qt.AlignLeft | Qt.AlignTop)
        self.layout.addWidget(self.grip2, 0, Qt.AlignRight | Qt.AlignBottom)
        # self.layout.addWidget(self.grip3, 0, Qt.AlignLeft | Qt.AlignBottom)
        # self.layout.addWidget(self.grip4, 0, Qt.AlignRight | Qt.AlignBottom)

        self.rubberband = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberband.setStyle(QStyleFactory.create("Fusion"))
        self.rubberband.move(0, 0)
        self.rubberband.show()
        self.show()

    def resizeEvent(self, event):

        if self.aspect_ratio:
            size = QSize(*self.aspect_ratio)
            size.scale(self.size(), Qt.KeepAspectRatio)
            self.resize(size)

        self.rubberband.resize(self.size())

    def set_aspect_ratio(self, ratio):
        self.aspect_ratio = ratio
        self.resizeEvent(None)


class ResizablePixmap(QLabel):

    def __init__(self, bytes_image):

        QLabel.__init__(self)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

        self.bytes_image_edit = bytes_image

        self.current_pixmap = self._bytes2pixmap(bytes_image)
        self.setPixmap(self.current_pixmap)

    def resizeEvent(self, event):

        if event:
            x = event.size().width()
            y = event.size().height()
        else:
            x = self.width()
            y = self.height()

        self.current_pixmap = self._bytes2pixmap(self.bytes_image_edit)
        self.setPixmap(self.current_pixmap.scaled(x, y, Qt.KeepAspectRatio))
        self.resize(x, y)

    @staticmethod
    def _bytes2pixmap(raw_image):

        image = QImage()
        image.loadFromData(raw_image)
        return QPixmap(image)

    @staticmethod
    def _pixmap2bytes(pixmap):

        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, 'PNG')
        return byte_array.data()

    @property
    def image_dims(self):
        return self.width(), self.height()

    def force_resize(self, qsize):
        self.resizeEvent(QResizeEvent(qsize, qsize))


class SelectablePixmap(ResizablePixmap):

    def __init__(self, bytes_image):

        super().__init__(bytes_image)

        self.currentQRubberBand = None
        self.move_rubber_band = False
        self.rubber_band_offset = None

    def cancel_selection(self):
        self.currentQRubberBand.hide()
        self.currentQRubberBand.deleteLater()
        self.currentQRubberBand = None
        self.selectionActive.emit(False)

    def mousePressEvent(self, eventQMouseEvent):

        if not self.currentQRubberBand:
            self.currentQRubberBand = ResizableRubberBand(self)
            self.selectionActive.emit(True)

        if self.currentQRubberBand.geometry().contains(eventQMouseEvent.pos()):
            self.move_rubber_band = True
            self.rubber_band_offset = (eventQMouseEvent.pos() -
                                       self.currentQRubberBand.pos())
        else:
            self.originQPoint = eventQMouseEvent.pos()
            self.currentQRubberBand.setGeometry(QRect(self.originQPoint,
                                                      QSize()))
            self.currentQRubberBand.show()

    def mouseMoveEvent(self, eventQMouseEvent):

        if self.move_rubber_band:
            pos = eventQMouseEvent.pos() - self.rubber_band_offset
            if self.pixmap().rect().contains(pos):
                self.currentQRubberBand.move(pos)
        else:
            rect = QRect(self.originQPoint, eventQMouseEvent.pos())
            self.currentQRubberBand.setGeometry(rect.normalized())

    def mouseReleaseEvent(self, eventQMouseEvent):

        if self.move_rubber_band:
            self.move_rubber_band = False


class RememberDir:

    def __init__(self, window_instance):

        self.window_instance = window_instance

    def get_dir(self):
        self.start_dir = QFileDialog.getExistingDirectory(self.window_instance,
                                                          "Open Folder",
                                                          self.start_dir)

        return self.start_dir

    def __enter__(self):

        # load last opened dir
        try:
            f = open(DIR_FILE, "r")
        except FileNotFoundError:
            self.start_dir = get_music_path()
        else:
            self.start_dir = f.readline().strip()
            f.close()

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):

        with open(DIR_FILE, "w") as f:
            f.write(self.start_dir)
