"""This module houses custom Qt classes designed to support the package."""

import logging
from os import makedirs, path
from typing import Callable, Iterable, Optional, Tuple, Union

from wiki_music.constants.paths import DIR_FILE
from wiki_music.gui_lib.qt_importer import (Property, QBuffer, QByteArray,
                                            QEvent, QFileDialog, QHBoxLayout,
                                            QImage, QIODevice, QLabel,
                                            QModelIndex, QPixmap, QPoint,
                                            QRect, QResizeEvent, QRubberBand,
                                            QSize, QSizeGrip, QSizePolicy,
                                            QSortFilterProxyModel,
                                            QStandardItem, QStandardItemModel,
                                            QStyleFactory, Qt, QTableWidget,
                                            QVariant, QVBoxLayout, QWidget,
                                            Signal)
from wiki_music.utilities.gui_utils import get_music_path

logging.getLogger(__name__)

__all__ = ["NumberSortModel", "CustomQStandardItem", "ImageTable",
           "ResizablePixmap", "CustomQStandardItemModel", "RememberDir"]


class NumberSortModel(QSortFilterProxyModel):
    """Custom table proxy model which can sort numbers not only strings."""

    def lessThan(self, left_index: QModelIndex,
                 right_index: QModelIndex) -> bool:
        """Reimplemented comparator method to handle numbers correctly.

        Parameters
        ----------
        left_index: QModelIndex
            index of the left compared element
        right_index: QModelIndex
            index of the right compared element
        """

        left_var: str = left_index.data(Qt.EditRole)
        right_var: str = right_index.data(Qt.EditRole)

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
    even though the object stores the full path.

    Parameters
    ----------
    data: Union[str, int, float, Iterable[str]]
        supports all data types used by parser, all are converted to string
        before passing to superclass constructor
    """

    def __init__(self, data: Union[str, int, float, Iterable[str]]) -> None:

        if isinstance(data, str):
            pass
        elif isinstance(data, (int, float)):
            data = str(data)
        elif isinstance(data, (list, tuple)):
            data = ", ".join(sorted(data))
        else:
            data = ""

        super().__init__(data)
        self._filtered: str = ""

    def data(self, role: Qt.ItemDataRole) -> QVariant:
        """Reimplemented method to show only filename instead of full file
        path. Only Qt.DisplayRole is affected other roles are left untouched.

        Parameters
        ----------
        role: Qt.ItemDataRole
            role of the edited item

        Returns
        -------
        Any
            data contained in QStandardItem
        """

        if role != Qt.DisplayRole:
            return super().data(role)
        else:
            if not self._filtered:

                self._filtered = super().data(Qt.DisplayRole)
                if path.isfile(self._filtered):
                    self._filtered = path.basename(self._filtered)

            return self._filtered

    def setData(self, value: QVariant, role: Qt.UserRole):
        """Reimplemented, sets new data for QStandardItem.
        also sets the :attr:`_filtered` to None so the path for the new item
        can be filtered again.

        Parameters
        ----------
        value: QVariant
            new value to set
        role: Qt.UserRole
            Qt data role
        """
        print("getting")
        self._filtered = ""
        super().setData(value, role)

    def real_data(self, role: Qt.ItemDataRole) -> str:
        """Workaround to show real contained data because the
        :meth:`QStandardItem.data` method is overridden.

        Parameters
        ----------
        role: Qt.ItemDataRole
            role of the edited item

        Returns
        -------
        Any
            data contained in QStandardItem
        """

        return super().data(role)

    def text(self, split=False) -> Union[str, list]:
        """Reimplemented, if the data is path than return full path instead
        of only filename.

        Parameters
        ----------
        split: bool
            if true split string into list of strings on commas

        Returns
        -------
        Union[str, list]
            string or list with actual data based on input
        """
        text = super().text()
        data = self.real_data(Qt.DisplayRole)

        if len(data) < len(text):
            data = text

        if split and "," in data:
            return [x.strip() for x in data.split(",")]
        else:
            return data


class CustomQStandardItemModel(QStandardItemModel):
    """Overrides the default impementation adds `__getitem__` method so the
    table columns ca be indexed by its names.
    """

    def __getitem__(self, name: str) -> int:
        """Column index from column header name.

        Parameters
        ----------
        name: str
            table column name

        Returns
        -------
        int
            column index

        Raises
        ------
        KeyError
            if the name does not exist in column headers
        """

        for column in range(self.columnCount()):
            if self.headerData(column, Qt.Horizontal) == name:
                return column

        raise KeyError(f"No column with name {name}")


class ImageWidget(QWidget):
    """Widget that displays image along with a short string underneath.

    Attributes
    ----------
    text: str
        test to show under picture
    img: bytearray
        picture to show
    """

    def __init__(self, text: str, img: bytearray,
                 parent: Optional[QWidget] = None) -> None:
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
        """Sets the text and image to be visible"""

        image = QImage()
        image.loadFromData(self._img)
        self.lbPixmap.setPixmap(QPixmap(image).scaledToWidth(150))
        self.lbText.setText(self._text)

    @Property(bytearray)
    def img(self) -> bytearray:
        """Dispalyed image in bytes format.

        :type: bytearray
        """
        return self._img

    @img.setter
    def ing_setter(self, value: bytearray):
        if self._img == value:
            return
        self._img = value
        self.initUi()

    @Property(str)
    def text(self) -> str:
        """Short text under the picture.

        :type: str
        """
        return self._text

    @text.setter
    def text_setter(self, value: str):
        if self._text == value:
            return
        self._text = value
        self.initUi()


class ImageTable(QTableWidget):
    """Table with cells holding Images with short text in cells.

    Parameters
    ----------
    parent: QWidget
        reterence to parent widget for centering

    Attribures
    ----------
    self.MAX_COLUMNS: int
        constant saying how many columns should the table have
    self.actualCol: int
        holds the position of actual column

    See also
    --------
    :class:ImageWidget
        each cell holds one of these widgets
    """

    MAX_COLUMNS: int
    actualCol: int

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        QTableWidget.__init__(self, parent)

        self.MAX_COLUMNS: int = 4
        self.actualCol: int = -1
        self.setColumnCount(1)
        self.setRowCount(1)
        self.resizeToContents()
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

    def add_pic(self, label: str, picture: bytearray):
        """Add one picture to table.

        Pictures are added in row until the row has `ImageTable.MAX_COLUMNS`
        pictures then we switch to the next row.

        Parameters
        ----------
        label: str
            short text to display under picture
        picture: bytearray
            picture to display

        Raises
        ------
        ValueError
            when method trie to add picture in column with
            `index` > `ImageTable.MAX_COLUMNS`
        """

        if self.actualCol < self.MAX_COLUMNS:
            self.actualCol += 1
            if self.rowCount() == 1:
                self.setColumnCount(self.columnCount() + 1)
        elif self.actualCol == self.MAX_COLUMNS:
            self.actualCol = 0
            self.setRowCount(self.rowCount() + 1)
        else:
            raise ValueError("Exception in adding picture to table. Actual"
                             " column exceeded value of max columns")

        self.setCellWidget(*self.ij, ImageWidget(label, picture))
        self.resizeToContents()

    @property
    def ij(self) -> Tuple[int, int]:
        """Actual free cell where next picture should be added.

        :type:`Tuple[int, int]`
        """
        return self.rowCount() - 1, self.actualCol

    def resizeToContents(self):
        """Resizes table rows and columns to fit largest cell contents."""
        self.resizeColumnsToContents()
        self.resizeRowsToContents()


class ResizableRubberBand(QRubberBand):
    """Reimplements QRubberBand so its aspect ratio can be set.

    Atttributes
    -----------
    aspect_ratio: Tuple[int, int]
        the aspect ratio that the rubberband is forcet to obey
    """

    aspect_ratio: Optional[float]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.aspect_ratio = None

    def resizeEvent(self, event: QEvent):
        """Reimplements resizeEvent with forced aspect ratio.

        Parameters
        ----------
        event: QEvent
            the event that triggered this method
        """

        if self.aspect_ratio:
            size = QSize(*self.aspect_ratio)
            size.scale(self.size(), Qt.KeepAspectRatio)
            self.resize(size)

    def set_aspect_ratio(self, ratio: float):
        """Sets forced aspect ratio for rubberband

        Parameters
        ----------
        ratio: float
            aspect ratio value, one float number
        """
        self.aspect_ratio = ratio
        self.resizeEvent(None)


class ResizablePixmap(QLabel):
    """Picture that can be arbitrarilly resized while keeping its aspect ratio.

    Parameters
    ----------
    bytes_image_edit: bytearray
        image that is displayed
    """

    bytes_image_edit: bytearray

    def __init__(self, bytes_image: bytearray, stretch: bool = True) -> None:
        QLabel.__init__(self)

        if stretch:
            self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        else:            
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Ignored)

        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #ffffff;")

        self.update_pixmap(bytes_image)

    def update_pixmap(self, bytes_image: bytearray):
        """Changes displayed image for a new one.

        Parameters
        ----------
        bytes_image: bytearray
            new image to display in bytes format
        """
        self.bytes_image_edit = bytes_image
        self.current_pixmap = self._bytes2pixmap(bytes_image)
        self.scale()

    def scale(self, fromResize: bool = False):
        """Handle picture scaling.

        Parameters
        ----------
        fromResize: bool
            special handling if this method was called after resize, but only 
            in subclasses
        """

        # use a single central method for scaling; there's no need to call it
        # upon creation and also resize() won't work anyway in a layout
        self.setPixmap(self.current_pixmap.scaled(self.width(), self.height(),
                                                  Qt.KeepAspectRatio,
                                                  Qt.SmoothTransformation))

    def resizeEvent(self, event: QEvent):
        """Reimplement behaviour on resize with scaling enabled.

        Parameters
        ----------
        event: QEvent
            the event that triggered this method
        """

        super(ResizablePixmap, self).resizeEvent(event)
        self.scale(fromResize=True)

    @staticmethod
    def _bytes2pixmap(raw_image: bytearray) -> QPixmap:
        """Convert bytes image to `QPixmap`

        Parameters
        ----------
        raw_image: bytearray
            bytes image to be converted
        
        Returns
        -------
        QPixmap
            image as Qt QPixmap
        """

        image = QImage()
        image.loadFromData(raw_image)
        return QPixmap(image)

    @staticmethod
    def _pixmap2bytes(pixmap: QPixmap) -> bytearray:
        """Convert `QPixmap` to bytes image.

        Parameters
        ----------
        pixmap: QPixmap
            Qt QPixmap to be converted
        
        Returns
        -------
        bytearray
            bytes image
        """

        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, 'PNG')
        return byte_array.data()

    @property
    def image_dims(self) -> Tuple[int, int]:
        """Actual image dimensions

        Returns
        -------
        Tuple[int, int]
            image width and height
        """
        return self.width(), self.height()


class SelectablePixmap(ResizablePixmap):
    """Pixmap whose part can be selected with selection rubberband.

    Warnings
    --------
    The solution is copied from stackoverflow and is not yet
    properly documented.

    References
    ----------
    https://stackoverflow.com/questions/58053735/get-real-size-of-qpixmap-in-qlabel

    Attributes
    ----------
    currentQRubberBand: Optional[ResizableRubberBand]
        holds reference to current rubberband
    rubberBandOffset: Optional[QPoint]
        rubberband upper left corner offset from the point where the mouse was
        clicked before dragging start
    moveDirection: Optional[Qt.Orientation]
        direction in which rubberband edge is dragged when resizing
    rubberBandRatio: Optional[float]
        forced aspect ratio of rubberband
    pixmapRect: QRect
        rectangle defining the pixmap borders
    selectionActive: Signal(bool)
        signal emited whenerver new rubberband selection is created
        destroyed
    """

    currentQRubberBand: Optional[ResizableRubberBand]
    rubberBandOffset: Optional[QPoint]
    moveDirection: Optional[Qt.Orientation]
    rubberBandRatio: Optional[float]
    pixmapRect: QRect

    selectionActive: Signal = Signal(bool)

    def __init__(self, bytes_image: bytearray) -> None:
        super().__init__(bytes_image)

        # activate mouse tracking to change cursor on rubberband hover
        self.setMouseTracking(True)
        self.currentQRubberBand = None
        self.rubberBandOffset = None
        self.moveDirection = 0
        self.rubberBandRatio = None

    def set_aspect_ratio(self, ratio: float):
        """Sets aspect ratio for rubberband.

        Parameters
        ----------
        ratio: float
            desired aspect ratio
        """
        self.rubberBandRatio = ratio
        self._update_ratio()

    def _update_ratio(self):
        """If rubberband is created updates its aspect ratio."""
        if self.currentQRubberBand:
            self.currentQRubberBand.set_aspect_ratio(self.rubberBandRatio)

    def create_selection(self, pos: QPoint):
        """Creates new rubberband selection.

        Parameters
        ----------
        pos: QPoint
            clicked position

        Note
        ----
        If old selection existed new is created only if mouse click happens
        outside of that selection. Othervise the current selection is moved.
        """

        if self.currentQRubberBand:
            self.cancel_selection()
        self.currentQRubberBand = ResizableRubberBand(QRubberBand.Rectangle,
                                                      self)
        self.currentQRubberBand.setStyle(QStyleFactory.create("Fusion"))
        self.currentQRubberBand.setGeometry(pos.x(), pos.y(), 1, 1)
        self.currentQRubberBand.show()
        self.originQPoint = pos
        self.currentQRubberBand.installEventFilter(self)

    def cancel_selection(self):
        """Cancels the current selection and destroys the rubberband."""

        self.currentQRubberBand.hide()
        self.currentQRubberBand.deleteLater()
        self.currentQRubberBand = None
        self.originQPoint = None
        self.selectionActive.emit(False)

    def scale(self, fromResize: bool = False):
        """Handle picture and selection scaling caused by window resize.

        Parameters
        ----------
        fromResize: bool
            tells the type if event that requested scaling
        """

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
        """Update picture margins formouse event tracking.

        Whenever the rubberband rectangle geometry changes, create virtual
        rectangles for corners and sides to ease up mouse event checking.
        """
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

    def eventFilter(self, source, event: QEvent):
        """Filteres GUI events to call special method on resize event.

        Parameters
        ----------
        source
            source that caused the event
        event: QEvent
            type of event
        
        Returns
        -------
        Callable
            result of the superclass eventFilter
        """

        if event.type() in (QEvent.Resize, QEvent.Move):
            self.updateMargins()
        return super(SelectablePixmap, self).eventFilter(source, event)

    def mousePressEvent(self, event: QEvent):
        """Handles left mouse button cliks.

        If the clicked position is inside the current selection than that
        selection is moved. If it is outside tahn a new selection is created.
        If the click is in selection margins than the picture is resized by
        dragging one of the edges.

        Parameters
        ----------
        event: QEvent
            calling event

        See also
        --------
        :meth:`SelectablePixmap.updateMargins`
            method responsible for creating margins and keeping them up to date
        """

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
            self.originQPoint = (
                self.currentQRubberBand.geometry().bottomRight())
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
            self.rubberBandOffset = pos - self.currentQRubberBand.pos()

    def mouseMoveEvent(self, event: QEvent):
        """Handles mouse movement events concerning the rubberband.

        The movement after mouse button is clicked and held can cause
        two actions. If the click occured in the margins than the selection is
        resized by dragging the edge. If it is inside the selection rectangle
        then the selection rubberband is moved by drgging.

        Parameters
        ----------
        event: QEvent
            the calling event
        """

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
            if self.rubberBandOffset:
                target = pos - self.rubberBandOffset
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

    def mouseReleaseEvent(self, event: QEvent):
        """Handles mouse release events and cleans up the data afterwards.
        
        Resets: rubberBandOffset, originQPoint, moveDirection
        """

        self.rubberBandOffset = None
        self.originQPoint = None
        self.moveDirection = 0


class RememberDir:
    """Context manager for remembering last opened directory.

    Parameters
    ----------
    window_instance: object
        reference to the window in which the context was initialized to center
        the directory selection dialog

    Attributes
    ----------
    _start_dir: str
        remembered directory if it could be read from file
    """

    _start_dir: str

    def __init__(self, window_instance: object) -> None:

        # keep reference to main window for dialog centering
        self.window_instance = window_instance

        # ensure directory for storing file exists
        makedirs(path.dirname(DIR_FILE), exist_ok=True)

    def get_dir(self) -> Tuple[str, bool]:
        """Shows a folder selection dialog with the last visited dir as root.

        After the user has selected directory it is remenbered, returned to
        user and upon context exit saved to file.

        Returns
        -------
        str
            string with directory name
        bool
            True if some directory was selected, False if dialog was canceled
        """
        self._start_dir = QFileDialog.getExistingDirectory(
            self.window_instance, "Open Folder", self._start_dir)

        return self._start_dir, bool(self._start_dir)

    def __enter__(self):
        """Load last visited directory from file.

        If the file could not be read, try to get music path on local PC
        """

        # load last opened dir
        try:
            f = open(DIR_FILE, "r")
        except FileNotFoundError:
            self._start_dir = get_music_path()
        else:
            self._start_dir = f.readline().strip()
            f.close()

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """On context exit try to save opened directory to file"""

        with open(DIR_FILE, "w") as f:
            f.write(self._start_dir)
