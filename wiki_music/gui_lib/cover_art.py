"""Module with classes for cover art picture search and download."""

import logging
import queue
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Tuple, Union

from wiki_music.constants import (ASPECT_RATIOS, COVER_ART_EDIT_UI,
                                  COVER_ART_SEARCH_UI)
from wiki_music.external_libraries.google_images_download import (  # lazy loaded
    google_images_download, google_images_download_offline)
from wiki_music.gui_lib import BaseGui, ImageTable, SelectablePixmap
from wiki_music.gui_lib.qt_importer import (QDialog, QHBoxLayout, QIcon,
                                            QMessageBox, QSize, Qt, QTimer,
                                            QWidget, Signal, uic)
from wiki_music.utilities import (MultiLog, comp_res, exception, get_icon,
                                  get_image, get_image_size)

if TYPE_CHECKING:
    from typing_extensions import TypedDict

    RespDict = TypedDict("RespDict", {"thumb": bytes,
                                      "dim": Tuple[int, Tuple[int, int]],
                                      "url": Union[Path, str]})


log = logging.getLogger(__name__)
log.debug("coverart imports done")


class PictureContainer(SelectablePixmap):
    """Holds the selected picture that is being edited.

    The raw picture is stored in bytes data. Which are the loaded by `PIL`
    for manipulation or by GUI to display.

    Warnings
    --------
    This class has the ability to select parts of picture with a rubberband
    so it should be used only for editing pictures.

    Parameters
    ----------
    bytes_image: bytes
        the picture that will be edited in bytes format
    log: :class:`wiki_music.utilities.util.MultiLog`
        logger instance of creating class

    Attributes
    ----------
    bytes_image_orig: bytes
        original image in byres format
    bytes_image_edit: bytes
        original image with applied compession
    bytes_image_crop: Optional[bytes]
        cropped version of original image without compression
    bytes_image_resz: Optional[bytes]
        resized version of original image without compression
    log: :class:`wiki_music.utilities.util.MultiLog`
        class logger
    disksizeChanged: Signal(str)
        signal that is emited whenever the disk size of image changes by
        compresion, resize or crop
    dimensionsChanged: Signal(int, int)
        signal emited on picture resize or crop

    See also
    --------
    :class:`wiki_music.gui_lib.custom_classes.SelectablePixmap`
        inhereted class which implements the ability to select with rubberband
    """

    bytes_image_orig: bytes
    bytes_image_edit: bytes
    bytes_image_crop: Optional[bytes]
    bytes_image_resz: Optional[bytes]
    log: MultiLog

    disksizeChanged: Signal = Signal(str)
    dimensionsChanged: Signal = Signal(int, int)

    def __init__(self, bytes_image: bytes, log: MultiLog) -> None:

        super().__init__(bytes_image)

        self.bytes_image_orig = bytes_image
        self.bytes_image_edit = bytes_image
        self.bytes_image_crop = None
        self.bytes_image_resz = None

        self.resize(800, 800)
        self._log = log

    @property
    def current_image_c(self) -> bytes:
        """Get image to compress.

        Returns
        -------
        bytes
            the appropriate image version
        """
        # if we have cropped image, use that
        if self.bytes_image_crop:
            return self.bytes_image_crop
        # if no cropped image is present use resized
        elif self.bytes_image_resz:
            return self.bytes_image_resz
        # is we have none of those use the original
        else:
            return self.bytes_image_orig

    @property
    def current_image_r(self) -> bytes:
        """Get image to resize.

        Returns
        -------
        bytes
            the appropriate image version
        """
        # if some resized version is present use that, otherwise use original
        if self.bytes_image_crop:
            return self.bytes_image_crop
        else:
            return self.bytes_image_orig

    def compress_image(self, quality: int):
        """Apply defined compresion to image and show result.

        Parameters
        ----------
        quaility: int
            value between 1 and 99 setting the compresion level

        See also
        --------
        :func:`wiki_music.utilitie.gui_utils.comp_res`
            compresses image using PIL
        """
        self.bytes_image_edit = comp_res(self.current_image_c, quality)
        self.update_pixmap(self.bytes_image_edit)

        size = get_image_size(self.bytes_image_edit)
        self.disksizeChanged.emit(size)

        self._log.info(f"Compressed cover art  to: {size}Kb")

    def resize_image(self, x: int, y: int, quality: int):
        """Resize image to set dimensions, apply defined compresion.

        Parameters
        ----------
        quaility: int
            value between 1 and 99 setting the compresion level
        x: int
            horizontal image dimension in pixels
        y: int
            vertical image dimension in pixels

        See also
        --------
        :func:`wiki_music.utilitie.gui_utils.comp_res`
            compresses and resizes image using PIL
        """
        self.bytes_image_edit = comp_res(self.current_image_r, quality, x, y)
        self.bytes_image_resz = self.bytes_image_edit
        self.update_pixmap(self.bytes_image_resz)

        self._log.info(f"Cover art resized to: {x}x{y}")
        self.disksizeChanged.emit(get_image_size(self.bytes_image_edit))

    def crop_image(self, quality: int):
        """Crops image to part selected by rubberband.

        After cropping appliy set level of compresin and shows image in GUI.

        Parameters
        ----------
        quaility: int
            value between 1 and 99 setting the compresion level

        See also
        --------
        :func:`wiki_music.utilitie.gui_utils.comp_res`
            compresses image using PIL
        """
        # TODO wrong image part displayed after crop
        # TODO image dimensions are not updated
        if self.currentQRubberBand:
            crop_pix = self.pixmap().copy(self.currentQRubberBand.geometry())
            self.bytes_image_crop = self._pixmap2bytes(crop_pix)
            self.compress_image(quality)
            self.cancel_selection()
            self.update_pixmap(self.bytes_image_crop)

            self.dimensionsChanged.emit(*self.image_dims)

            self._log.info("Cover art cropped to: "
                           "{}x{}".format(*self.image_dims))
        else:
            self._log.warning("No selection to crop.")

    def save_image(self, path: Path):
        """Save current version of the image to file with name Folder.jpg."""
        path.write_bytes(self.bytes_image_edit)

    # TODO currently not used
    # def send2clipboard(self):
    #    """Copies the image to clipboard """
    #    send_to_clipboard(self.bytes_image_edit)


class SearchDialog(QDialog):
    """Manages the search dialog window.

    Displays found picture thumbnails and houses some basic search controls.

    Parameters
    ----------
    query: str
        search phrase passed to google images download

    Attributes
    ----------
    table: :class:`wiki_music.gui_lib.custom_classes.ImageTable`
        special subclass of Qt ImageTable that can hold pictures in cells and
        can add new pictures on the fly
    pictureClicked: Signal(int)
        signal emited when table cell is clicked

    See also
    --------
    :class:`wiki_music.ui.cover_art_base.Ui_cover_art_search`
        this is the template class for this class layout
    :class:`wiki_music.gui_lib.custom_classes.ImageTable`
        this is the class that manages the table itself
    """

    table: ImageTable
    pictureClicked: Signal = Signal(int)

    def __init__(self, query: str) -> None:

        # QDialog init
        super().__init__()
        # setup ui from template
        uic.loadUi(COVER_ART_SEARCH_UI, self)

        self.setWindowTitle("Wiki Music - Cover Art search")
        self.setWindowIcon(QIcon(get_icon()))

        # set initial values
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.query.setText(query)

        # create table for image thumbnails
        self.table = ImageTable()
        self.verticalLayout.insertWidget(0, self.table)

        # forward table signal
        self.table.cellClicked.connect(self.table_cell_clicked)

        # connect cancel button
        self.cancel_button.clicked.connect(self.done)

    def table_cell_clicked(self, row: int, col: int):
        """Emits signal when cell in table is clicked with picture list index.

        Position index in list is calculated from rom the row and column.

        Parameters
        ----------
        row: int
            row pocition of clicked cell
        col: int
            column position of clicked cell
        """
        self.pictureClicked.emit((self.max_columns + 1) * row + col)

    @property
    def max_columns(self) -> int:
        """Get fixed predefined number of row columns.

        Returns
        -------
        int:
            predefined number of table columns
        """
        return self.table.MAX_COLUMNS

    def add_pic(self, dimension: str, thumbnail: bytes):
        """Add new picture to the table.

        Parameters
        ----------
        dimension: str
            formated string with image dimension and size in Kb
        thumbnail: bytes
            raw image thumbnail in bytes format
        """
        self.table.add_pic(dimension, thumbnail)


class PictureEdit(QDialog):
    """Manages picture editor window.

    Takes care of cropping, resizing and compressing abilities.

    Parameters
    ----------
    dimensions: Tuple[int, int]
        dimensions of the image being edited
    clicked_image: bytes
        the image to edit in bytes format
    log: :class:`wiki_music.utilities.utils.MultiLog`
        main GUI class logger
    save_dir: str
        directory in which the edited image will be saved if the option is
        chosen

    Attributes
    ----------
    picture: PictureContainer
        class holding the picture and its metods
    original_ratio: float
        save original ratio of the picture
    editingFinished: Signal
        signal to emit the edited picture when choice is accepted
    """

    picture: PictureContainer
    original_ratio: float

    editingFinished: Signal = Signal(bytes)

    def __init__(self, dimensions: Tuple[int, int], clicked_image: bytes,
                 log: MultiLog, save_dir: str) -> None:

        # QDialog init
        super().__init__()
        # setup ui from template
        uic.loadUi(COVER_ART_EDIT_UI, self)

        self._log = log
        self.save_dir = Path(save_dir)

        self.setWindowTitle("Edit cover art")
        self.setWindowIcon(QIcon(get_icon()))
        self.picture = PictureContainer(clicked_image, self._log)

        # variables
        self.original_ratio = dimensions[0] / dimensions[1]

        self.ca_dropdown.insertItems(1, ASPECT_RATIOS)
        self.size_box.setReadOnly(True)
        self.cancel_crop.setEnabled(False)

        self.size_spinbox_X.setValue(dimensions[0])
        self.size_spinbox_Y.setValue(dimensions[1])
        self.compresion_spinbox.setValue(95)
        self.compresion_slider.setValue(95)
        self.size_box.setText(get_image_size(clicked_image))
        self.picture_frame.addWidget(self.picture)

        self._setup_overlay()

    def _setup_overlay(self):
        """Connect all the dialog elements to coresponding signals."""
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
            lambda size: self._aspect_ratio_sync(size, "x"))
        self.size_spinbox_Y.valueChanged.connect(
            lambda size: self._aspect_ratio_sync(size, "y"))
        self.apply_ratio.clicked.connect(
            lambda x: self.picture.resize_image(*self.image_dims,
                                                self.compresion))

        # compression signals
        self.compresion_spinbox.valueChanged.connect(
            lambda comp_value: self._get_compressed(comp_value, "spinbox"))
        self.compresion_slider.valueChanged.connect(
            lambda comp_value: self._get_compressed(comp_value, "slider"))

        # on finished editing emit signal with edited image
        self.accepted.connect(
            lambda: self.editingFinished.emit(self.picture.bytes_image_edit))

    @property
    def image_dims(self) -> Tuple[int, int]:
        """Edited image dimensions.

        :type: Tuple[int, int]
        """
        return self.size_spinbox_X.value(), self.size_spinbox_Y.value()

    def set_image_dims(self, x: int, y: int):
        """Passes current image dimension to spinboxes.

        Parameters
        ----------
        x: int
            horizontal dimension in pixels
        y: int
            vertical dimension in pixels
        """
        self.size_spinbox_X.setValue(x)
        self.size_spinbox_Y.setValue(y)

    @property
    def clipboard(self) -> bool:
        """Clipboard checkbox state.

        :type: bool
        """
        return self.ca_clipboard.isChecked()

    @property
    def save_file(self) -> bool:
        """Save to disk checkbox state.

        :type: bool
        """
        return self.ca_file.isChecked()

    @property
    def preserve_ratio(self) -> bool:
        """Preserve ration checkbox state.

        :type: bool
        """
        return self.ca_ratio.isChecked()

    @property
    def compresion(self) -> int:
        """Current compresion slider and spinbox value.

        :type: int
        """
        return self.compresion_spinbox.value()

    @exception(log)
    def _get_crop_ratio(self, value: str):
        """Sets the desired aspect ratio for cropping.

        See also
        --------
        :meth:`PictureContainer.set_aspect_ratio`
            method activated to apply the aspect ratio to picture

        Paremeters
        ----------
        value: str
            ratio value can be one of:
            :const:`wiki_music.constants.gui_const.ASPECT_RATIOS`

        Raises
        ------
        ValueError
            if the passed `value` is not a valid ratio format
        """
        crop_ratio: Optional[float]

        if value.lower() == "preserve":
            crop_ratio = self.original_ratio
        elif value.lower() == "free":
            crop_ratio = None
        else:
            try:
                ar = [int(i) for i in value.split(":")]
            except ValueError:
                raise ValueError(f"{value} is not a valid ratio format")
            else:
                crop_ratio = ar[1] / ar[2]

        self.picture.set_aspect_ratio(crop_ratio)

    def _aspect_ratio_sync(self, dim: int, activated: str):
        """Synchronize the aspect ratio spinboxes.

        Parameters
        ----------
        dim: int
            the current value in spinbox which activated this method
        activated: str
            x or y the spinbox which activated this methos
        """
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
            self.original_ratio = x / y

    def _get_compressed(self, comp_value: int, activated: str):
        """Compresses the image to desired value.

        Parameters
        ----------
        comp_value: int
            compression value from interval (1, 99)
        activated: str
            where to get the value from, spinbox or slider

        See also
        --------
        :meth:`PictureContainer.compress_image`
            method activated to apply the compression to picture
        """
        if activated == "spinbox":
            self.compresion_slider.setValue(comp_value)
        elif activated == "slider":
            self.compresion_spinbox.setValue(comp_value)

        self.picture.compress_image(comp_value)

    def picture_save(self):
        """Saves picture to Folder.jpg in directory with edited music files.

        Warnings
        --------
        Copying to clipboard is disabled for now

        See also
        --------
        :meth:`PictureContainer.save_image`
            method activated to save picture to file
        :meth:`PictureContainer.send2clipboard`
            method activated to paste picture to clipboard
        """
        if self.save_file:
            self._log.info("Cover art saved to file")
            self.picture.save_image(self.save_dir / "Folder.jpg")
        if self.clipboard:
            self._log.info("Cover art copied to clipboard")
            # TODO this is not used for now see discussion in gui_utils module
            # self.picture.send2clipboard()


class CoverArtSearch(BaseGui):
    """Main class that handles cover art search.

    Calls all the apropriate methods. First initialize google_images_download
    in a separate thread, then initializes Search dialog window. After that it
    reads downloaded image thumbnails and displays them inn the dialog.

    Attributes
    ----------
    image_search_thread: Thread
        thread that runs the goolgle_images download in the background
    search_dialog: SearchDialog
        reference to dialog window showing the downloaded pictures in table
    picture_editor: PictureEdit
        reference to dialog window that handles selected image editing

    See also
    --------
    :mod:`wiki_music.external_libraries.google_images_download`
        submodule that handles downloading cover art images
    :class:`wiki_music.gui_lib.cover_art.SearchDialog`
        class that shows dialog downloaded cover art images and some basic
        search controls
    :class:`wiki_music.gui_lib.cover_art.PictureEdit`
        handles editing of downloaded pictures
    """

    _max_count: int
    images: List["RespDict"]
    image_search_thread: Thread
    search_dialog: SearchDialog
    picture_editor: PictureEdit

    @exception(log)
    def cover_art_search(self):
        """Method that takes care of cover art search, download and edit.

        See also
        --------
        :meth:`_async_loader`
            method that loads results to GUI
        :meth:`_select_picture`
            method that stats picture edit dialog
        """
        self.images = []

        if self.offline_debug:
            self.gimd = google_images_download_offline.googleimagesdownload()
            self._max_count = 5
        else:
            if not all((self.ALBUMARTIST, self.ALBUM)):
                QMessageBox(QMessageBox.Information, "Message",
                            "You must input Artist and Album first").exec_()
                return
            self.gimd = google_images_download.googleimagesdownload()
            self._max_count = 20

        query = f"{self.ALBUMARTIST} {self.ALBUM}"

        # limit can be no more than 100, otherwise chromedriver and selenium
        # are needed, because other download method is used
        arguments = {
            "keywords": query,
            "limit": 100,
            "size": "large",
            "no_download": True,
            "no_download_thumbs": True,
            "thumbnail": True
        }

        # init thread that preforms the search
        self.image_search_thread = Thread(target=self.gimd.download,
                                          args=(arguments, ), daemon=True,
                                          name="ImageSearch")
        self.image_search_thread.start()

        # setup dialog layout and connect to button signals
        self.search_dialog = SearchDialog(query)
        self.search_dialog.pictureClicked.connect(self._select_picture)
        self.search_dialog.load_button.clicked.connect(self._load_more)
        # stop image download on dialog close
        self.search_dialog.finished.connect(self.gimd.close)
        # TODO unreliable
        # on search dialog exit remove message from progressbar
        self.search_dialog.destroyed.connect(lambda: self._log.info(""))
        # TODO connect
        self.search_dialog.search_button.clicked.connect(self._do_nothing)
        self.search_dialog.browser_button.clicked.connect(self._do_nothing)

        self.search_dialog.show()

        QTimer.singleShot(0, self._async_loader)

        self._log.info("Searching for Cover Art")

    def _load_more(self):
        """Method that raises the maximum number of images to download."""
        # raise the limit of max downloaded images
        self._max_count += 20

        # check if there is enough images to load
        # if not adjust the limit accordingly
        if len(self.images) >= self.gimd.max:
            QMessageBox(QMessageBox.Information, "Message",
                        "No more images to load").exec_()
            self._log.debug("No more images to load")
            return

        if self._max_count > self.gimd.max:
            self._max_count = self.gimd.max

        # continue loading images
        QTimer.singleShot(0, self._async_loader)

    @exception(log)
    def _async_loader(self):
        """Periodically checks background thread for new downloaded images.

        When a new image is found it is loaded and passed to GUI dialog to
        display. Chceck is scheduled every 50ms.

        See also
        --------
        :class:`wiki_music.gui_lib.cover_art.PictureEdit`
            dialog window that displays the downloaded images
        """
        dim: str

        def continue_load(flip: bool = False) -> Tuple[bool, bool]:
            """Decides if more images should be loaded from background thread.

            Returns
            -------
            Tuple[bool, bool]
                first coresponds to ImageSearch window being visible and the
                other reports if enough images has been loaded
            """
            if flip:
                cl1, cl2 = continue_load()
                return not cl1, not cl2
            else:
                return (self.search_dialog.isVisible(),
                        len(self.images) < self._max_count)

        # in one singleShot of the timer we load as mmuch images as available
        while True:
            try:
                image = self.gimd.stack.get(block=False)
            except queue.Empty:
                # if stack is empty break the loop
                break
            else:
                # if item is present try to red it
                try:
                    dim = (f"{image['dim'][1][0]}x{image['dim'][1][1]}\n"
                           f"{(image['dim'][0] / 1024):.2f}Kb")
                except TypeError as e:
                    # if we couldnat load image parameters, don't show it
                    self._log.debug(e)
                    pass
                else:
                    # show and store image
                    self.search_dialog.add_pic(dim, image["thumb"])
                    self.images.append(image)
                    # update progress bar
                    self.search_dialog.progressBar.setValue(
                        int(100 * len(self.images) / self._max_count))

                # indicate that the item is processed
                self.gimd.stack.task_done()

            # don't load more images than allowed
            if any(continue_load(flip=True)):
                break

        # if not enough images were loaded and search window was not destroyed
        # schedule another run
        if all(continue_load()):
            QTimer.singleShot(50, self._async_loader)

    @exception(log)
    def _select_picture(self, index: int):
        """Method that initializes classes for selected picture editing.

        Parameters
        ----------
        index: int
            position of the picture in downloade pictures list
        """
        # 0-th position is size in KB, and 1-st position is tuple of dimensions
        dimensions: Tuple[int, int] = self.images[index]["dim"][1]
        url: Union[Path, str] = self.images[index]["url"]

        self._log.info(f"Downloading full size cover art from: {url}")

        # create dialog to handle image editing
        self.picture_editor = PictureEdit(dimensions, get_image(url),
                                          self._log, self.work_dir)
        # if choice was accepted close download, show selected image in gui
        # close search dialog, and save picture
        self.picture_editor.accepted.connect(self.gimd.close)
        self.picture_editor.editingFinished.connect(self._display_image)
        self.picture_editor.accepted.connect(self.search_dialog.close)
        self.picture_editor.accepted.connect(self.picture_editor.picture_save)

        # TODO see discusion in gui utils module
        # clipboard pasting is disabled for now !!!
        self.picture_editor.ca_clipboard.stateChanged.connect(
            self._do_nothing)
        ###########################################
        self.picture_editor.show()
