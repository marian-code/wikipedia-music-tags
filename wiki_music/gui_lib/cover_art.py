from os import path
from threading import Thread
from typing import Iterable, Optional, Tuple

from wiki_music.external_libraries.google_images_download import (  # lazy loaded
    google_images_download, google_images_download_offline)
from wiki_music.gui_lib import BaseGui, ImageTable, SelectablePixmap
from wiki_music.gui_lib.qt_importer import (QDialog, QHBoxLayout, QIcon,
                                            QMessageBox, QSize, Qt, QTimer,
                                            QWidget, Signal)
from wiki_music.ui import Ui_cover_art_search, Ui_dialog
from wiki_music.utilities import (
    MultiLog, SharedVars, comp_res, exception, get_icon, get_image,
    get_image_size, log_gui, send_to_clipboard)

log_gui.debug("coverart imports done")


class CustomPixmap(SelectablePixmap):

    bytes_image_orig: bytearray
    bytes_image_edit: bytearray
    bytes_image_crop: Optional[bytearray]
    bytes_image_resz: Optional[bytearray]
    log: MultiLog

    disksizeChanged: Signal = Signal(str)
    dimensionsChanged: Signal = Signal(int, int)

    def __init__(self, bytes_image: bytearray) -> None:

        super().__init__(bytes_image)

        self.bytes_image_orig = bytes_image
        self.bytes_image_edit = bytes_image
        self.bytes_image_crop = None
        self.bytes_image_resz = None

        self.resize(800, 800)
        self.log = MultiLog(log_gui)

    @property
    def current_image_c(self) -> bytearray:

        if self.bytes_image_crop:
            return self.bytes_image_crop
        elif self.bytes_image_resz:
            return self.bytes_image_resz
        else:
            return self.bytes_image_orig

    @property
    def current_image_r(self) -> bytearray:

        if self.bytes_image_crop:
            return self.bytes_image_crop
        else:
            return self.bytes_image_orig

    def compress_image(self, quality: int):

        self.bytes_image_edit = comp_res(self.current_image_c, quality)
        self.update_pixmap(self.bytes_image_edit)

        size = get_image_size(self.bytes_image_edit)
        self.disksizeChanged.emit(size)

        self.log.info(f"Compressed cover art  to: {size}Kb")

    def resize_image(self, x: int, y: int, quality: int):

        self.bytes_image_edit = comp_res(self.current_image_r, quality, x, y)
        self.bytes_image_resz = self.bytes_image_edit
        self.update_pixmap(self.bytes_image_resz)

        self.log.info(f"Cover art resized to: {x}x{y}")
        self.disksizeChanged.emit(get_image_size(self.bytes_image_edit))

    def crop_image(self, quality: int):

        # TODO wrong image part displayed after crop
        crop_pixmap = self.pixmap().copy(self.currentQRubberBand.geometry())
        self.bytes_image_crop = self._pixmap2bytes(crop_pixmap)
        self.compress_image(quality)
        self.cancel_selection()
        self.update_pixmap(self.bytes_image_crop)

        self.dimensionsChanged.emit(*self.image_dims)

        self.log.info("Cover art cropped to: {}x{}".format(*self.image_dims))

    def save_image(self, path: str):

        with open(path, 'wb') as f:
            f.write(self.bytes_image_edit)

    def send2clipboard(self):
        send_to_clipboard(self.bytes_image_edit)


class SearchDialog(QDialog, Ui_cover_art_search):

    table: ImageTable

    cellClicked: Signal = Signal(int, int)

    def __init__(self, query: str) -> None:

        # QDialog init
        super().__init__()
        # setup ui from template
        super().setupUi(self)

        self.setWindowTitle("Wiki Music - Cover Art search")
        self.setWindowIcon(QIcon(get_icon()))

        # set initial values
        self.progressBar.setRange(0, 100)
        self.query.setText(query)

        # create table for image thumbnails
        self.table = ImageTable()
        self.verticalLayout.insertWidget(0, self.table)

        # forward table signal
        self.table.cellClicked.connect(self.table_cell_clicked)

    def table_cell_clicked(self, row: int, col: int):
        self.cellClicked.emit(row, col)

    @property
    def max_columns(self) -> int:
        return self.table.max_columns

    def add_pic(self, dimension: str, thumbnail: bytearray):
        self.table.add_pic(dimension, thumbnail)


class PictureEdit(QDialog, Ui_dialog):

    log: MultiLog
    picture: CustomPixmap
    cancel: bool
    original_ratio: float

    def __init__(self, dimensions: tuple, clicked_image: bytearray) -> None:

        # QDialog init
        super().__init__()
        # setup ui from template
        super().setupUi(self)

        self.log = MultiLog(log_gui)

        self.setWindowTitle("Edit cover art")
        self.setWindowIcon(QIcon(get_icon()))
        self.picture = CustomPixmap(clicked_image)

        # variables
        self.cancel = False
        self.original_ratio = dimensions[0] / dimensions[1]

        self.ca_dropdown.insertItems(1, ["Free", "Preserve", "16:9", "4:3",
                                         "3:2", "1:1"])
        self.size_box.setReadOnly(True)
        self.cancel_crop.setEnabled(False)

        self.size_spinbox_X.setValue(dimensions[0])
        self.size_spinbox_Y.setValue(dimensions[1])
        self.compresion_spinbox.setValue(95)
        self.compresion_slider.setValue(95)
        self.size_box.setText(get_image_size(clicked_image))
        self.picture_frame.addWidget(self.picture)

        self.__setup_overlay__()

    def __setup_overlay__(self):

        # connect to dialog signals
        self.buttonBox.rejected.connect(self._dialog_cancel)
        self.rejected.connect(self._dialog_cancel)

        # editor signals
        self.picture.selectionActive.connect(self.cancel_crop.setEnabled)
        self.picture.disksizeChanged.connect(self.size_box.setText)
        self.picture.dimensionsChanged.connect(self.set_image_dims)

        # crop signals
        self.apply_crop.clicked.connect(
            lambda x: self.picture.crop_image(self.compresion))
        self.cancel_crop.clicked.connect(
            lambda x: self.picture.cancel_selection())
        self.ca_dropdown.editTextChanged.connect(self._get_crop_ratio)

        # resize signals
        self.size_spinbox_X.valueChanged.connect(
            lambda size: self._aspect_ratio_set(size, "x"))
        self.size_spinbox_Y.valueChanged.connect(
            lambda size: self._aspect_ratio_set(size, "y"))
        self.apply_ratio.clicked.connect(
            lambda x: self.picture.resize_image(*self.image_dims,
                                                self.compresion))

        # compression signals
        self.compresion_spinbox.valueChanged.connect(
            lambda comp_value: self._get_compressed(comp_value, "spinbox"))
        self.compresion_slider.valueChanged.connect(
            lambda comp_value: self._get_compressed(comp_value, "slider"))

    @property
    def image_dims(self) -> Tuple[int, int]:
        return self.size_spinbox_X.value(), self.size_spinbox_Y.value()

    def set_image_dims(self, x: int, y: int):
        self.size_spinbox_X.setValue(x)
        self.size_spinbox_Y.setValue(y)

    @property
    def clipboard(self) -> bool:
        return self.ca_clipboard.isChecked()

    @property
    def save_file(self) -> bool:
        return self.ca_file.isChecked()

    @property
    def preserve_ratio(self) -> bool:
        return self.ca_ratio.isChecked()

    @property
    def compresion(self) -> int:
        return self.compresion_spinbox.value()

    def _dialog_cancel(self):
        self.cancel = True

    def _get_crop_ratio(self, value: str):
        crop_ratio: Optional[Iterable[float]]

        if value.lower() == "preserve":
            crop_ratio = (self.original_ratio, 1)
        elif value.lower() == "free":
            crop_ratio = None
        else:
            try:
                crop_ratio = [int(i) for i in value.split(":")]
            except ValueError:
                raise ValueError(f"{value} is not a valid ratio format")

        self.picture.set_aspect_ratio(crop_ratio)

    def _aspect_ratio_set(self, dim: int, activated: str):

        x, y = self.image_dims

        if self.preserve_ratio:
            # TODO find some nicer way to avoid recursion
            if activated == "x":
                if int(self.original_ratio * y) == x:
                    return
                y = int((1 / self.original_ratio) * dim)
                self.size_spinbox_Y.setValue(y)
            elif activated == "y":
                if int((1 / self.original_ratio) * x) == y:
                    return
                x = int(self.original_ratio * dim)
                self.size_spinbox_X.setValue(x)
            else:
                raise NotImplementedError
        else:
            self.original_ratio = x / y

    def _get_compressed(self, comp_value: int, activated: str):

        if activated == "spinbox":
            self.compresion_slider.setValue(comp_value)
        elif activated == "slider":
            self.compresion_spinbox.setValue(comp_value)
        else:
            raise NotImplementedError

        self.picture.compress_image(comp_value)

    def execute(self, save_dir: str):

        if self.save_file:
            self.log.info("Cover art saved to file")
            self.picture.save_image(path.join(save_dir, "Folder.jpg"))
        if self.clipboard:
            self.log.info("Cover art copied to clipboard")
            self.picture.send2clipboard()


class CoverArtSearch(BaseGui):

    max_count: int
    old_count: int
    image_search_thread: Thread
    search_dialog: SearchDialog

    @exception(log_gui)
    def __cover_art_search__(self):

        if not all((self.ALBUMARTIST, self.ALBUM)):
            QMessageBox(QMessageBox.Information, "Message",
                        "You must input Artist and Album first").exec_()
            return

        import sys
        print(sys.modules["wiki_music.external_libraries.lyricsfinder"])

        if SharedVars.offline_debbug:
            self.gimd = google_images_download_offline.googleimagesdownload()
            self.max_count = self.gimd.get_max()
        else:
            self.gimd = google_images_download.googleimagesdownload()
            self.max_count = 20

        self.old_count = self.gimd.count

        query = f"{self.ALBUMARTIST} {self.ALBUM}"
        arguments = {
            "keywords": query,
            "limit": self.max_count,
            "size": "large",
            "no_download": True,
            "no_download_thumbs": True,
            "thumbnail": True
        }

        # init thread that preforms the search
        self.image_search_thread = Thread(target=self.gimd.download,
                                          args=(arguments, ),
                                          name="ImageSearch")
        self.image_search_thread.daemon = True
        self.image_search_thread.start()

        # setup dialog layout and connect to button signals
        self.search_dialog = SearchDialog(query)
        self.search_dialog.cellClicked.connect(self.__select_picture__)
        self.search_dialog.load_button.clicked.connect(self.__do_nothing__)
        self.search_dialog.search_button.clicked.connect(self.__do_nothing__)
        self.search_dialog.browser_button.clicked.connect(self.__do_nothing__)
        self.search_dialog.cancel_button.clicked.connect(self.__do_nothing__)

        self.search_dialog.show()

        QTimer.singleShot(0, self._async_search)

        self.log.info("Searching for Cover Art")

    @exception(log_gui)
    def _async_search(self):
        new_count: int
        t: bytearray
        s: Tuple[float, Tuple[int, int]]
        dim: str

        new_count = self.gimd.count
        if new_count > self.old_count:
            for i in range(self.old_count, new_count):
                s = self.gimd.fullsize_dim[i]
                t = self.gimd.thumbs[i]
                try:
                    dim = f"{s[1][0]}x{s[1][1]}\n{(s[0] / 1024):.2f}Kb"
                except TypeError:
                    continue
                self.search_dialog.add_pic(dim, t)
                self.search_dialog.progressBar.setValue(int(100 * new_count /
                                                            self.max_count))

            self.old_count = new_count

        if self.search_dialog.isVisible():
            QTimer.singleShot(50, self._async_search)
        else:
            self.gimd.close()

    @exception(log_gui)
    def __select_picture__(self, row: int, col: int):

        # position of clicked picture in list
        index: int = (self.search_dialog.max_columns + 1) * row + col

        # 0-th position is size in b, and 1-st position is tuple of dimensions
        dimensions: Tuple[int, int] = self.gimd.fullsize_dim[index][1]
        url: str = self.gimd.fullsize_url[index]
        thumbnail: bytearray = self.gimd.thumbs[index]

        self.log.info(f"Downloading full size cover art from: {url}")

        # create dialog to handle image editing
        self.image_dialog = PictureEdit(dimensions, get_image(url))
        self.image_dialog.exec_()

        if self.image_dialog.cancel:
            return

        self.search_dialog.close()
        self.gimd.close()
        self.__display_image__(thumbnail)
        self.image_dialog.execute(self.work_dir)
