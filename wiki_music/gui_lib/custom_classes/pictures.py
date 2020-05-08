"""Module providing custom image handling classes implementations to GUI."""

import logging
from typing import Optional, Tuple

from wiki_music.gui_lib.qt_importer import (
    QBuffer, QByteArray, QEvent, QImage, QIODevice, QLabel, QPixmap, QPoint,
    QRect, QRubberBand, QSize, QSizePolicy, QStyleFactory, Qt, Signal)

logging.getLogger(__name__)

__all__ = ["ResizablePixmap", "SelectablePixmap"]


class _ResizableRubberBand(QRubberBand):
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
        """Sets forced aspect ratio for rubberband.

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
    bytes_image_edit: bytes
        image that is displayed
    """

    bytes_image_edit: bytes

    def __init__(self, bytes_image: bytes, stretch: bool = True) -> None:

        QLabel.__init__(self)

        if stretch:
            self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        else:
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Ignored)

        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #ffffff;")

        self.update_pixmap(bytes_image)

    def update_pixmap(self, bytes_image: bytes):
        """Changes displayed image for a new one.

        Parameters
        ----------
        bytes_image: bytes
            new image to display in bytes format
        """
        self.bytes_image_edit = bytes_image
        self.current_pixmap = self._bytes2pixmap(bytes_image)
        #self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
    def _bytes2pixmap(raw_image: bytes) -> QPixmap:
        """Convert bytes image to `QPixmap`.

        Parameters
        ----------
        raw_image: bytes
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
    def _pixmap2bytes(pixmap: QPixmap) -> bytes:
        """Convert `QPixmap` to bytes image.

        Parameters
        ----------
        pixmap: QPixmap
            Qt QPixmap to be converted

        Returns
        -------
        bytes
            bytes image
        """
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, 'PNG')
        return byte_array.data()

    @property
    def image_dims(self) -> Tuple[int, int]:
        """Actual image dimensions.

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
    currentQRubberBand: Optional[_ResizableRubberBand]
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

    currentQRubberBand: Optional[_ResizableRubberBand]
    rubberBandOffset: Optional[QPoint]
    moveDirection: Optional[Qt.Orientation]
    rubberBandRatio: Optional[float]
    pixmapRect: QRect

    selectionActive: Signal = Signal(bool)

    def __init__(self, bytes_image: bytes) -> None:
        super().__init__(bytes_image)

        # activate mouse tracking to change cursor on rubberband hover
        self.setMouseTracking(True)
        self.currentQRubberBand = None
        self.rubberBandOffset = None
        self.moveDirection = 0
        self.rubberBandRatio = None

    def set_aspect_ratio(self, ratio: Optional[float]):
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
        """Create new rubberband selection.

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
        self.currentQRubberBand = _ResizableRubberBand(QRubberBand.Rectangle,
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
            pos not in self.currentQRubberBand.geometry()):  # noqa E129
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
            if self.rubberBandOffset and self.currentQRubberBand:
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
            elif self.originQPoint and self.currentQRubberBand:
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
