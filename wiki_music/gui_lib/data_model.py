"""Module that manages GUI data model and interacion with parser.

Warnings
--------
All parser interaciton should be hanhled by this class. Parser methods and
attributes should not be accesed directly in GUI.
"""

import logging
from pathlib import Path
from typing import Iterable, List, Optional, Union

from wiki_music.constants import GUI_HEADERS, SPLIT_HEADERS, STR_TAGS
from wiki_music.gui_lib import (BaseGui, CustomQStandardItem,
                                CustomQStandardItemModel, NumberSortModel,
                                ResizablePixmap)
from wiki_music.gui_lib.qt_importer import (QImage, QLabel, QMessageBox,
                                            QModelIndex, QPixmap,
                                            QStandardItemModel, QTimer)
from wiki_music.library.parser import WikipediaRunner
from wiki_music.utilities import exception

log = logging.getLogger(__name__)
log.debug("data model imports done")


class ParserInteract(BaseGui):
    """Class that represents comunication chanel between parser and GUI.

    Warnings
    --------
    This class is not ment to be instantiated, only inherited.

    Attributes
    ----------
    _parser: :class:`wiki_music.library.parser.WikipediaRunner`
        parser instance doing all the heavy lifting
    """

    def __init__(self) -> None:

        self._parser = WikipediaRunner(GUI=True)
        super().__init__()

        # TODO needs QThreads to work
        # self._parser.selectedGenreChanged.connect(self.genre_entry.setText)
        # self._parser.releaseDateChanged.connect(self.year_entry.setText)
        # self._parser.bandChanged.connect(self.band_entry)
        # self._parser.bandChanged.connect(self.band_entry_input)
        # self._parser.albumChanged.connect(self.album_entry)
        # self._parser.albumChanged.connect(self.album_entry_input)

    @property
    def GENRE(self) -> str:
        """Found genre.

        See also
        --------
        :attr:`wiki_music.library.parser.base.ParserBase.GENRE`
            parser attribute tied to this property
        :class:`BaseGui.genre_entry`
            Qt entry field tied to this property

        :type: str
        """
        return self._parser.GENRE

    @GENRE.setter
    def GENRE(self, value: str):
        self._parser.GENRE = value
        self.genre_entry.setText(value)

    @property
    def DATE(self) -> str:
        """Found release date.

        See also
        --------
        :attr:`wiki_music.library.parser.base.ParserBase.DATE`
            parser attribute tied to this property
        :class:`BaseGui.year_entry`
            Qt entry field tied to this property

        :type: str
        """
        return self._parser.DATE

    @DATE.setter
    def DATE(self, value: str):
        self._parser.DATE = value
        self.year_entry.setText(value)

    @property
    def ALBUM(self) -> str:
        """Found album name.

        See also
        --------
        :attr:`wiki_music.library.parser.base.ParserBase.ALBUM`
            parser attribute tied to this property
        :class:`BaseGui.album_entry`
            Qt entry field tied to this property
        :class:`BaseGui.album_entry_input`
            Qt entry field tied to this property

        :type: str
        """
        return self._parser.ALBUM

    @ALBUM.setter
    def ALBUM(self, value: str):
        self._parser.ALBUM = value
        self.album_entry.setText(value)
        self.album_entry_input.setText(value)

    @property
    def ALBUMARTIST(self) -> str:
        """Found album artist name.

        See also
        --------
        :attr:`wiki_music.library.parser.base.ParserBase.ALBUMARTIST`
            parser attribute tied to this property
        :class:`BaseGui.band_entry`
            Qt entry field tied to this property
        :class:`BaseGui.band_entry_input`
            Qt entry field tied to this property

        :type: str
        """
        return self._parser.ALBUMARTIST

    @ALBUMARTIST.setter
    def ALBUMARTIST(self, value: str):
        self._parser.ALBUMARTIST = value
        self.band_entry.setText(value)
        self.band_entry_input.setText(value)

    @property
    def url(self) -> str:
        """Wikipedia url address of the downloaded page.

        See also
        --------
        :attr:`wiki_music.library.parser.preload.WikiCooker.url`
            parser attribute tied to this property

        :type: str
        """
        return str(self._parser.url)

    @property
    def offline_debug(self) -> bool:
        """Toogle offline debugging mmode for parser.

        See also
        --------
        :attr:`wiki_music.library.parser.preload.WikiCooker.offline_debug`
            parser attribute tied to this property

        :type: bool
        """
        return self._parser.offline_debug

    @offline_debug.setter
    def offline_debug(self, value: bool):
        self._parser.offline_debug = value

    @property  # type: ignore
    def work_dir(self) -> str:  # type: ignore
        """Current working directory.

        See also
        --------
        :attr:`wiki_music.library.parser.base.ParserBase.work_dir`
            parser attribute tied to this property

        :type: str
        """
        return str(self._parser.work_dir.resolve())

    @work_dir.setter
    def work_dir(self, value: str):
        self._parser.work_dir = Path(value)
        if value:
            self.setWindowTitle(f"Wiki Music - {value}")

    @property
    def COVERART(self):
        """Album coverart.

        See also
        --------
        :attr:`wiki_music.library.parser.base.ParserBase.COVERART`
            parser attribute tied to this property

        :type: str
        """
        return self._parser.COVERART

    @COVERART.setter
    def COVERART(self, value: bytes):
        self._parser.COVERART = value

    def stop_preload(self):
        """Stops running page preload.

        See also
        --------
        :class:`wiki_music.library.parser.preload.WikiCooker.Preload`
            parser inner class controlling preload
        """
        self._parser.stop_preload()

    def start_preload(self, delay: Optional[float] = None):
        """Starts page preload.

        See also
        --------
        :class:`wiki_music.library.parser.preload.WikiCooker.Preload`
            parser inner class controlling preload
        """
        self._parser.start_preload()

    def write_tags(self, indeces: Optional[List[int]]) -> bool:
        """Writes tags to music files.

        Parameters
        ----------
        indeces: Optional[List[int]]
            indeces of files to save

        See also
        --------
        :class:`wiki_music.library.parser.in_out.ParserInOut.write_tags`
            method that controls tag writing

        Returns
        -------
        bool
            truth if writing was successful
        """
        self._gui_to_parser()
        return self._parser.write_tags(indeces)

    def read_files(self):
        """Reads tags from music files.

        See also
        --------
        :class:`wiki_music.library.parser.in_out.ParserInOut.read_files`
            method for reading tags from files
        """
        self._parser.read_files()
        self._parser_to_gui()

    @property
    def number_of_tracks(self):
        """Number of found tracks.

        Number of tracks detected by parser on wikipedia or load from disk.

        :type: int
        """
        return len(self._parser)

    @property
    def save_ready(self) -> bool:
        """Tells if there are any writable files in working directory.

        :type: bool
        """
        return bool(self._parser)

    def reinit_parser(self):
        """Sets parser attributes to their default values.

        Reinitializes parser attributes so a new search can be performed.
        """
        # TODO non-atomic
        self._parser.reinit(protected_vars=False)


class DataModel(ParserInteract):
    """Transfer data between GUI and parser and manage GUI data model.

    This class reads data from parser to be displayed in GUI and on save or
    other action that requires parser it collects data in GUI and writes it to
    parser.

    Warnings
    --------
    This class is not ment to be instantiated, only inherited.

    Attributes
    ----------
    cover_art: Optional[ResizablePixmap]
        Qt class that displays the found cover art picture
    table: CustomQStandardItemModel
        Qt table for displaying parser data
    proxy: NumberSortModel
        table model for data sorting
    """

    cover_art: Optional[ResizablePixmap]
    table: CustomQStandardItemModel
    proxy: NumberSortModel

    def __init__(self) -> None:

        log.debug("init data model")

        super().__init__()

        self.cover_art = None

        # create table with headers
        self.table = CustomQStandardItemModel()
        self.table.setHorizontalHeaderLabels(GUI_HEADERS)

        self.proxy = NumberSortModel()
        self.proxy.setSourceModel(self.table)

        log.debug("init data model done")

    def _input_is_present(self, with_warn=False) -> bool:
        """Check if apropriate input to conduct search is present.

        Returns
        -------
        bool
            true if all requested inputs are present
        """
        group = [self.ALBUMARTIST, self.ALBUM, self.work_dir]
        if all(group):
            return True
        else:
            alb, bnd, wkd, inp, com, _and = [""] * 6
            if not self.ALBUM:
                alb = " album"
            if not self.ALBUMARTIST:
                bnd = " band"
            if str(self.work_dir) == ".":
                wkd = " select working directory"

            if any([alb, bnd]):
                inp = "input"
            if all([alb, bnd, wkd]):
                com = ","
            elif all([alb, bnd]):
                com = " and"
            if all([alb, wkd]) or all([wkd, bnd]):
                _and = " and"

            msg = f"You must {inp}{alb}{com}{bnd}{_and}{wkd}"

            if with_warn:
                message = QMessageBox()
                message.setIcon(QMessageBox.Information)
                message.setWindowTitle("Message")
                message.setText(msg)
                message.exec_()
                self._log.warning(msg)

            return False

    def _gui_to_parser(self):
        """Transfers data from GUI to parser.

        Warnings
        --------
        This operation is non-atomic, as of now it still does not have a proper
        locking mechanism. We rely on the fact that only GUI or the parser
        are trying to access data at a given time.
        """
        # TODO non-atomic
        for h in GUI_HEADERS:
            setattr(self._parser, h,
                    self.table.getColumn(h, split=(h in SPLIT_HEADERS)))

    def _display_image(self, image: Optional[bytes] = None):
        """Shows cover art image preview in main window.

        See also
        --------
        :class:`wiki_music.gui_lib.custom_classes.ResizablePixmap`

        Parameters
        ----------
        image: bytes
            force displaying of the input image instead of the one contained in
            parser. Also the input image is saved to parser.
        """
        if image:
            self.COVERART = image

        if self.cover_art:
            self.cover_art.update_pixmap(self.COVERART)
        else:
            self.cover_art = ResizablePixmap(self.COVERART, stretch=False)
            self.picture_layout.addWidget(self.cover_art)

    @exception(log)
    def _parser_to_gui(self):
        """Transfers data from parser GUI.

        Warnings
        --------
        This operation is non-atomic, as of now it still does not have a proper
        locking mechanism. We rely on the fact that only GUI or the parser
        are trying to access data at a given time.
        """
        if self.number_of_tracks:

            log.debug("init table entries")

            self.table.setRowCount(self.number_of_tracks)

            # TODO until QThreads are implemented and these can be passed
            # with signals
            for s in STR_TAGS:
                setattr(self, s, getattr(self._parser, s))

            # TODO non-atomic
            for h in GUI_HEADERS:
                self.table.setColumn(h, getattr(self._parser, h))

                # do not resize lyrics column, it is too wide
                if h != "LYRICS":
                    self.tableView.resizeColumnToContents(self.table[h])

            self.tableView.update()

            log.debug("show cover art")
            self._display_image()

            log.debug("init table entries done")
        else:
            QTimer.singleShot(100, self._parser_to_gui)

    @exception(log)
    def _detail(self, proxy_index: QModelIndex):
        """Display detail of the row that is clicked and sync changes to table.

        Parameters
        ----------
        proxy_index: QModelIndex
            index of the proxy model cell, needs to be translated to real table
            cell index
        """
        # proxy_index is QModelIndex proxyIndex Class type
        # it is index of data mapping as shown in gui
        # real indeces are different
        row = self.proxy.mapToSource(proxy_index).row()

        # maintain row highlight
        for i in self.tableView.selectionModel().selectedRows():
            self.tableView.selectRow(i.row())

        entries = [
            (0, self.number_detail),
            (1, self.title_detail),
            (3, self.artist_detail),
            (4, self.composer_detail),
            (6, self.lyrics_detail),
            (7, self.file_detail)
        ]

        log.debug("connect detail function")

        for col, ent in entries:
            ent.disconnect()
            ent.setText(self.table.item(row, col).text())
            # c = col is a hack to change the
            # scope of col otherwise lambda will refer
            # to actual value of col since it is in
            # outer scope
            # None is the default argument for text since QTextEdit
            # signal doesn´t retutn text
            ent.textChanged.connect(
                lambda text=None, c=col: self._text_check(row, c, text))

    def _text_check(self, row: int, col: int, text: Optional[str]):
        """Writes changed text in detail tab to table.

        Parameters
        ----------
        row: int
            table row
        col: int
            table column
        text: Optional[str]
            text put in cell, if None read it from :attr:`lyrics_detail`
        """
        if text is None:
            text = self.lyrics_detail.toPlainText()

        self.table.setItem(row, col, CustomQStandardItem(text))
