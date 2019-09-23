from os.path import basename, isfile

from wiki_music.constants.paths import DIR_FILE
from wiki_music.gui.qt_importer import (Property, QBuffer, QByteArray, QEvent,
                                        QFileDialog, QHBoxLayout, QImage,
                                        QIODevice, QLabel, QPixmap, QPoint,
                                        QRect, QResizeEvent, QRubberBand,
                                        QSize, QSizeGrip, QSizePolicy,
                                        QSortFilterProxyModel, QStandardItem,
                                        QStandardItemModel, QStyleFactory, Qt,
                                        QTableWidget, QVBoxLayout, QWidget,
                                        Signal)
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


class ResizableRubberBand(QRubberBand):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aspect_ratio = None

    def resizeEvent(self, event):

        if self.aspect_ratio:
            size = QSize(*self.aspect_ratio)
            size.scale(self.size(), Qt.KeepAspectRatio)
            self.resize(size)

    def set_aspect_ratio(self, ratio):
        self.aspect_ratio = ratio
        self.resizeEvent(None)


class ResizablePixmap(QLabel):

    def __init__(self, bytes_image):
        QLabel.__init__(self)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #ffffff;")

        self.update_pixmap(bytes_image)

    def update_pixmap(self, bytes_image):
        self.bytes_image_edit = bytes_image
        self.current_pixmap = self._bytes2pixmap(bytes_image)
        self.scale()

    def scale(self, fromResize=False):
        # use a single central method for scaling; there's no need to call it upon
        # creation and also resize() won't work anyway in a layout
        self.setPixmap(self.current_pixmap.scaled(self.width(), self.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super(ResizablePixmap, self).resizeEvent(event)
        self.scale(True)

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


class SelectablePixmap(ResizablePixmap):

    selectionActive = Signal(bool)

    def __init__(self, bytes_image):
        super().__init__(bytes_image)

        # activate mouse tracking to change cursor on rubberband hover
        self.setMouseTracking(True)
        self.currentQRubberBand = None
        self.rubber_band_offset = None
        self.moveDirection = 0
        self.rubberBandRatio = None

    def set_aspect_ratio(self, ratio):
        self.rubberBandRatio = ratio
        self._update_ratio()

    def _update_ratio(self):
        if self.currentQRubberBand:
            self.currentQRubberBand.set_aspect_ratio(self.rubberBandRatio)

    def create_selection(self, pos):
        if self.currentQRubberBand:
            self.cancel_selection()
        self.currentQRubberBand = ResizableRubberBand(QRubberBand.Rectangle, self)
        self.currentQRubberBand.setStyle(QStyleFactory.create("Fusion"))
        self.currentQRubberBand.setGeometry(pos.x(), pos.y(), 1, 1)
        self.currentQRubberBand.show()
        self.originQPoint = pos
        self.currentQRubberBand.installEventFilter(self)

    def cancel_selection(self):
        self.currentQRubberBand.hide()
        self.currentQRubberBand.deleteLater()
        self.currentQRubberBand = None
        self.originQPoint = None
        self.selectionActive.emit(False)

    def scale(self, fromResize=False):
        if fromResize and self.currentQRubberBand:
            # keep data for rubber resizing, before scaling
            oldPixmapRect = self.pixmap().rect()
            oldOrigin = (self.currentQRubberBand.pos() -
                         self.pixmapRect.topLeft())
        super(SelectablePixmap, self).scale()

        # assuming that you always align the image in the center,
        # get the current pixmap rect and move
        # the rectangle center to the current geometry
        self.pixmapRect = self.pixmap().rect()
        self.pixmapRect.moveCenter(self.rect().center())
        if fromResize and self.currentQRubberBand:
            # find the new size ratio based on the previous
            xRatio = self.pixmapRect.width() / oldPixmapRect.width()
            yRatio = self.pixmapRect.height() / oldPixmapRect.height()
            # create a new geometry using 0-rounding for improved accuracy
            self.currentQRubberBand.setGeometry(
                round(oldOrigin.x() * xRatio, 0) + self.pixmapRect.x(),
                round(oldOrigin.y() * yRatio + self.pixmapRect.y(), 0),
                round(self.currentQRubberBand.width() * xRatio, 0),
                round(self.currentQRubberBand.height() * yRatio, 0))

    def updateMargins(self):
        # whenever the rubber rectangle geometry changes, create virtual
        # rectangles for corners and sides to ease up mouse event checking
        rect = self.currentQRubberBand.geometry()
        self.rubberTopLeft = QRect(rect.topLeft(),
                                   QSize(8, 8))
        self.rubberTopRight = QRect(rect.topRight(),
                                    QSize(-8, 8)).normalized()
        self.rubberBottomRight = QRect(rect.bottomRight(),
                                       QSize(-8, -8)).normalized()
        self.rubberBottomLeft = QRect(rect.bottomLeft(),
                                      QSize(8, -8)).normalized()
        self.rubberLeft = QRect(self.rubberTopLeft.bottomLeft(),
                                self.rubberBottomLeft.topRight())
        self.rubberTop = QRect(self.rubberTopLeft.topRight(),
                               self.rubberTopRight.bottomLeft())
        self.rubberRight = QRect(self.rubberTopRight.bottomLeft(),
                                 self.rubberBottomRight.topRight())
        self.rubberBottom = QRect(self.rubberBottomLeft.topRight(),
                                  self.rubberBottomRight.bottomLeft())
        self.rubberInnerRect = QRect(self.rubberTop.bottomLeft(),
                                     self.rubberBottom.topRight())

    def eventFilter(self, source, event):
        if event.type() in (QEvent.Resize, QEvent.Move):
            self.updateMargins()
        return super(SelectablePixmap, self).eventFilter(source, event)

    def mousePressEvent(self, event):
        pos = event.pos()
        
        if (not self.currentQRubberBand or
            pos not in self.currentQRubberBand.geometry()):
            if pos not in self.pixmapRect:
                self.originQPoint = None
                return
            self.create_selection(pos)
            self.selectionActive.emit(True)
            self._update_ratio()
        elif pos in self.rubberTopLeft:
            self.originQPoint = self.currentQRubberBand.geometry().bottomRight()
        elif pos in self.rubberTopRight:
            self.originQPoint = self.currentQRubberBand.geometry().bottomLeft()
        elif pos in self.rubberBottomRight:
            self.originQPoint = self.currentQRubberBand.geometry().topLeft()
        elif pos in self.rubberBottomLeft:
            self.originQPoint = self.currentQRubberBand.geometry().topRight()
        elif pos in self.rubberTop:
            self.originQPoint = self.currentQRubberBand.geometry().bottomLeft()
            self.moveDirection = Qt.Vertical
        elif pos in self.rubberBottom:
            self.originQPoint = self.currentQRubberBand.geometry().topLeft()
            self.moveDirection = Qt.Vertical
        elif pos in self.rubberLeft:
            self.originQPoint = self.currentQRubberBand.geometry().topRight()
            self.moveDirection = Qt.Horizontal
        elif pos in self.rubberRight:
            self.originQPoint = self.currentQRubberBand.geometry().topLeft()
            self.moveDirection = Qt.Horizontal
        else:
            self.rubber_band_offset = pos - self.currentQRubberBand.pos()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if event.buttons() == Qt.NoButton and self.currentQRubberBand:
            if pos in self.rubberTopLeft or pos in self.rubberBottomRight:
                self.setCursor(Qt.SizeFDiagCursor)
            elif pos in self.rubberTopRight or pos in self.rubberBottomLeft:
                self.setCursor(Qt.SizeBDiagCursor)
            elif pos in self.rubberLeft or pos in self.rubberRight:
                self.setCursor(Qt.SizeHorCursor)
            elif pos in self.rubberTop or pos in self.rubberBottom:
                self.setCursor(Qt.SizeVerCursor)
            elif pos in self.rubberInnerRect:
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.unsetCursor()
        elif event.buttons():
            if self.rubber_band_offset:
                target = pos - self.rubber_band_offset
                rect = QRect(target, self.currentQRubberBand.size())
                # limit positioning of the selection to the image rectangle
                if rect.x() < self.pixmapRect.x():
                    rect.moveLeft(self.pixmapRect.x())
                elif rect.right() > self.pixmapRect.right():
                    rect.moveRight(self.pixmapRect.right())
                if rect.y() < self.pixmapRect.y():
                    rect.moveTop(self.pixmapRect.y())
                elif rect.bottom() > self.pixmapRect.bottom():
                    rect.moveBottom(self.pixmapRect.bottom())
                self.currentQRubberBand.setGeometry(rect)
            elif self.originQPoint:
                if self.moveDirection == Qt.Vertical:
                    # keep the X fixed to the current right, so that only the
                    # vertical position is changed
                    pos.setX(self.currentQRubberBand.geometry().right())
                else:
                    # limit the X to the pixmapRect extent
                    if pos.x() < self.pixmapRect.x():
                        pos.setX(self.pixmapRect.x())
                    elif pos.x() > self.pixmapRect.right():
                        pos.setX(self.pixmapRect.right())
                if self.moveDirection == Qt.Horizontal:
                    # same as before, but for the Y position
                    pos.setY(self.currentQRubberBand.geometry().bottom())
                else:
                    # limit the Y to the pixmapRect extent
                    if pos.y() < self.pixmapRect.y():
                        pos.setY(self.pixmapRect.y())
                    elif pos.y() > self.pixmapRect.bottom():
                        pos.setY(self.pixmapRect.bottom())
                rect = QRect(self.originQPoint, pos)
                self.currentQRubberBand.setGeometry(rect.normalized())

    def mouseReleaseEvent(self, event):
        self.rubber_band_offset = None
        self.originQPoint = None
        self.moveDirection = 0


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
