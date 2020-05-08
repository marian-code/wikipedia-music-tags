"""Module providing custom implementation QWidget standard items."""

import logging
from pathlib import Path
from typing import Optional, Union, Iterable

from wiki_music.gui_lib.qt_importer import (QImage, QLabel, QPixmap, Property,
                                            QStandardItem, Qt, QVariant,
                                            QVBoxLayout, QWidget)

__all__ = ["CustomQStandardItem", "ImageItem"]

log = logging.getLogger(__name__)


class CustomQStandardItem(QStandardItem):
    """Overrides default methods so only the filename is "displayed".

    The object still stores the full path.

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
        """Show only filename instead of full file path.

        Reimplemented method, only Qt.DisplayRole is affected other roles
        are left untouched.

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
                if self._filtered == "":
                    pass
                else:
                    path = Path(self._filtered)
                    try:
                        if path.is_file():
                            self._filtered = path.name
                    except OSError as e:
                        log.warning(e)
                        # sometimes throws OSError
                        # when invalid path characters are present
                        pass

            return self._filtered

    def setData(self, value: QVariant, role: Qt.UserRole):
        """Reimplemented, sets new data for QStandardItem.

        Also sets the :attr:`_filtered` to None so the path for the new item
        can be filtered again.

        Parameters
        ----------
        value: QVariant
            new value to set
        role: Qt.UserRole
            Qt data role
        """
        self._filtered = ""
        super().setData(value, role)

    def real_data(self, role: Qt.ItemDataRole) -> str:
        """Workaround to show real contained data.

        Because the :meth:`QStandardItem.data` method is overridden.

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

    def text(self, split: bool = False) -> Union[str, list]:
        """Reimplemented, if the data is path than return full path.

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
            return [d.strip() for d in data.split(",") if d]
        else:
            return data


class ImageItem(QWidget):
    """Widget that displays image along with a short string underneath.

    Attributes
    ----------
    text: str
        test to show under picture
    img: bytes
        picture to show
    """

    def __init__(self, text: str, img: bytes,
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
        """Set the text and image to be visible."""
        image = QImage()
        image.loadFromData(self._img)
        self.lbPixmap.setPixmap(QPixmap(image).scaledToWidth(150))
        self.lbText.setText(self._text)

    @Property(bytes)
    def img(self) -> bytes:
        """Dispalyed image in bytes format.

        :type: bytes
        """
        return self._img

    @img.setter
    def ing_setter(self, value: bytes):
        """Dispalyed image in bytes format.

        :type: bytes
        """
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
        """Short text under the picture.

        :type: str
        """
        if self._text == value:
            return
        self._text = value
        self.initUi()
