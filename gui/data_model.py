from typing import Iterable, List, Optional, Union

from wiki_music.constants.tags import GUI_HEADERS, STR_TAGS
from wiki_music.gui import (BaseGui, CustomQStandardItem,
                            CustomQStandardItemModel, ResizablePixmap)
from wiki_music.gui.qt_importer import (QImage, QLabel, QPixmap,
                                        QStandardItemModel, QTimer)
from wiki_music.library.parser import WikipediaRunner
from wiki_music.utilities import SharedVars, exception, log_gui


class ParserInteract(BaseGui):

    def __init__(self) -> None:

        self.parser = WikipediaRunner(GUI=True)
        super().__init__()

        # TODO needs QThreads to work
        """
        self.parser.selectedGenreChanged.connect(self.genre_entry.setText)
        self.parser.releaseDateChanged.connect(self.year_entry.setText)
        self.parser.bandChanged.connect(self.band_entry)
        self.parser.bandChanged.connect(self.band_entry_input)
        self.parser.albumChanged.connect(self.album_entry)
        self.parser.albumChanged.connect(self.album_entry_input)
        """

    @property
    def GENRE(self) -> str:
        return self.parser.selected_genre

    @GENRE.setter
    def GENRE(self, value: str):
        self.parser.selected_genre = value
        self.genre_entry.setText(value)

    @property
    def DATE(self) -> str:
        return self.parser.release_date

    @DATE.setter
    def DATE(self, value: str):
        self.parser.release_date = value
        self.year_entry.setText(value)

    @property
    def ALBUM(self) -> str:
        return self.parser.album

    @ALBUM.setter
    def ALBUM(self, value: str):
        self.parser.album = value
        self.album_entry.setText(value)
        self.album_entry_input.setText(value)

    @property
    def ALBUMARTIST(self) -> str:
        return self.parser.band

    @ALBUMARTIST.setter
    def ALBUMARTIST(self, value: str):
        self.parser.band = value
        self.band_entry.setText(value)
        self.band_entry_input.setText(value)

    @property
    def url(self) -> str:
        return self.parser.url

    @property
    def genres(self) -> List[str]:
        return self.parser.genres

    @property
    def work_dir(self) -> str:
        return self.parser.work_dir

    @work_dir.setter
    def work_dir(self, value: str):
        self.display_dir.setText(value)
        self.parser.work_dir = value

    def stop_preload(self):
        self.parser.Preload.stop()

    def start_preload(self):
        self.parser.Preload.start()

    def write_tags(self, lyrics_only: bool = False) -> bool:
        return self.parser.write_tags(lyrics_only=lyrics_only)

    def read_files(self):
        self.parser.read_files()

    def save_ready(self) -> bool:
        return bool(self.parser)

    def set_cover_art(self, value: bytearray):
        self.parser.cover_art = value


class DataModel(ParserInteract):
    """ Transfer data between GUI and parser and manage GUI data model. """

    cover_art: Optional[ResizablePixmap]
    table: CustomQStandardItemModel

    def __init__(self) -> None:

        super().__init__()

        self.cover_art = None

        # create table with headers
        self.table = CustomQStandardItemModel()
        self.table.setHorizontalHeaderLabels(GUI_HEADERS)

    def __init_parser__(self):
        # TODO non-atomic
        self.parser.__init__(protected_vars=False)
        self.parser.list_files()
        SharedVars.re_init()

    @staticmethod
    def _parser_to_gui(data: Union[str, float, Iterable]) -> str:

        if isinstance(data, str):
            return data
        elif isinstance(data, (int, float)):
            return str(data)
        elif isinstance(data, (list, tuple)):
            return ", ".join(sorted(data))
        else:
            return ""

    def _gui_to_parser(self):
        col: int

        # TODO non-atomic
        for h in GUI_HEADERS:

            col = self.table.col_index(h)

            temp = []
            for row in range(self.table.rowCount()):
                temp.append(self.table.item(row, col).text())
                # split data in columns: TYPE, ARTIST, COMPOSER
                if "," in temp[row] and col in (2, 3, 4):
                    temp[row] = [x.strip() for x in temp[row].split(",")]

            setattr(self.parser, h, temp)

    def __display_image__(self, image: Optional[bytearray] = None):
        """ shows cover art image preview in main window. """

        if image:
            _img = image
            self.set_cover_art(image)
        else:
            _img = self.parser.cover_art

        if self.cover_art:
            self.cover_art.update_pixmap(_img)
        else:
            self.cover_art = ResizablePixmap(_img)
            self.picture_layout.addWidget(self.cover_art)

    # methods for managing gui data model
    @exception(log_gui)
    def __update_model__(self):
        """ Synchronizes the parser and Gui table. """
        col: int

        if len(self.parser):

            log_gui.debug("init entries")

            self.table.setRowCount(len(self.parser))

            # TODO until QThreads are implemented
            for s in STR_TAGS:
                setattr(self, s, getattr(self.parser, s))

            # TODO non-atomic
            for idx, h in enumerate(GUI_HEADERS):
                col = self.table.col_index(h)
                for row, value in enumerate(getattr(self.parser, h)):
                    value = self._parser_to_gui(value)
                    self.table.setItem(row, col, CustomQStandardItem(value))

                if idx != len(GUI_HEADERS) - 2:
                    self.tableView.resizeColumnToContents(col)

            self.tableView.update()

            log_gui.debug("init entries done")
        else:
            QTimer.singleShot(100, self.__update_model__)

    @exception(log_gui)
    def __detail__(self, proxy_index):
        """
        Display detail of the row that is clicked
        """

        # proxy_index is QModelIndex proxyIndex Class type
        # it is index of data mapping as shown in gui
        # real indeces are different
        row = self.proxy.mapToSource(proxy_index).row()

        # maintain row highlight
        index = self.tableView.selectionModel().selectedRows()
        self.tableView.selectRow(index[0].row())

        entries = [
            (0, self.number_detail),
            (1, self.title_detail),
            (3, self.artist_detail),
            (4, self.composer_detail),
            (6, self.lyrics_detail),
            (7, self.file_detail)
        ]

        log_gui.debug("connect detail function")

        for col, ent in entries:
            ent.disconnect()
            ent.setText(self.table.item(row, col).text())
            # col_inner = col is a hack to change the
            # scope of col otherwise lambda will refer
            # to actual value of col since it is in
            # outer scope
            # None is the default argument for text since QTextEdit
            # signal doesn´t retutn text
            ent.textChanged.connect(
                lambda text=None, c=col: self.__text_check__(row, c, text))

    def __text_check__(self, row: int, col: int, text: Optional[str]):
        """ Watch text changes in detail entry fields and
            sync them back to table"""

        if text is None:
            item = CustomQStandardItem(self.lyrics_detail.toPlainText())
        else:
            item = CustomQStandardItem(text)

        self.table.setItem(row, col, item)
