from typing import List

from wiki_music.utilities import MultiLog, log_parser

__all__ = ["ParserBase"]

SList = List[str]  # list of strings
IList = List[int]  # list of ints
NList = List[SList]  # nested list


class ParserBase:
    """ Properties with same names as tags act as a proxy to parser variables
        for convenient access."""

    files: SList
    bracketed_types: SList

    def __init__(self, protected_vars: bool) -> None:

        # lists 1D
        self.contents: SList = []
        self.tracks: SList = []
        self.types: SList = []
        self.disc_num: IList = []
        self.disk_sep: IList = []
        self.disks: List[list] = []
        self.genres: SList = []
        self.header: SList = []
        self.lyrics: SList = []
        self.NLTK_names: SList = []
        self.numbers: SList = []
        self.personnel: SList = []
        self._bracketed_types: SList = []
        self._files: SList = []

        # lists 2D
        self.appearences: NList = []
        self.artists: NList = []
        self.composers: NList = []
        self.sub_types: NList = []
        self.subtracks: NList = []

        # bytearray
        self.cover_art: bytearray = bytearray()

        # strings
        self.release_date: str = ""
        self.selected_genre: str = ""

        # atributes protected from GUIs reinit method
        # when new search is started
        if protected_vars:
            self.album: str = ""
            self.band: str = ""
            self.work_dir: str = ""
            self.log: MultiLog = MultiLog(log_parser)
    
    def __len__(self):
        return len(self.numbers)

    def __bool__(self):
        return self.__len__()

    @property
    def ALBUM(self) -> str:
        return self.album

    @ALBUM.setter
    def ALBUM(self, value: str):
        self.album = value

    @property
    def ALBUMARTIST(self) -> str:
        return self.band

    @ALBUMARTIST.setter
    def ALBUMARTIST(self, value: str):
        self.band = value

    @property
    def ARTIST(self) -> NList:
        return self.artists

    @ARTIST.setter
    def ARTIST(self, value: NList):
        self.artists = value

    @property
    def COMPOSER(self) -> NList:
        return self.composers

    @COMPOSER.setter
    def COMPOSER(self, value: NList):
        self.composers = value

    @property
    def COVERART(self) -> bytearray:
        return self.cover_art

    @COVERART.setter
    def COVERART(self, value: bytearray):
        self.cover_art = value

    @property
    def DATE(self) -> str:
        return self.release_date

    @DATE.setter
    def DATE(self, value: str):
        self.release_date = value

    @property
    def DISCNUMBER(self) -> IList:
        return self.disc_num

    @DISCNUMBER.setter
    def DISCNUMBER(self, value: IList):
        self.disc_num = value

    @property
    def GENRE(self) -> str:
        return self.selected_genre

    @GENRE.setter
    def GENRE(self, value: str):
        self.selected_genre = value

    @property
    def LYRICS(self) -> SList:
        return self.lyrics

    @LYRICS.setter
    def LYRICS(self, value: SList):
        self.lyrics = value

    @property
    def UNSYNCEDLYRICS(self) -> SList:
        return self.lyrics

    @UNSYNCEDLYRICS.setter
    def UNSYNCEDLYRICS(self, value: SList):
        self.lyrics = value

    @property
    def TITLE(self) -> SList:
        return self.tracks

    @TITLE.setter
    def TITLE(self, value: SList):
        self.tracks = value

    @property
    def TRACKNUMBER(self) -> SList:
        return self.numbers

    @TRACKNUMBER.setter
    def TRACKNUMBER(self, value: SList):
        self.numbers = value

    @property
    def FILE(self) -> SList:
        return self.files

    @FILE.setter
    def FILE(self, value: SList):
        self.files = value

    @property
    def TYPE(self) -> SList:
        return self.bracketed_types

    @TYPE.setter
    def TYPE(self, value: SList):
        self.bracketed_types = value


# TODO needs QThreads
"""
from wiki_music.gui.qt_importer import Signal, QObject


class GuiInOut(ParserInOut, QObject):

    selectedGenreChanged = Signal(str)
    releaseDateChanged = Signal(str)
    bandChanged = Signal(str)
    albumChanged = Signal(str)

    def __init__(self):

        QObject.__init__(self)
        self._selected_genre = ""
        self._release_date = ""
        self._album = ""
        self._band = ""

    @property
    def selected_genre(self):
        return self._selected_genre

    @selected_genre.setter
    def selected_genre(self, value):
        self._selected_genre = value
        self.selectedGenreChanged.emit(value)

    @property
    def release_date(self):
        return self._release_date

    @release_date.setter
    def release_date(self, value):
        self._release_date = value
        self.releaseDateChanged.emit(value)

    @property
    def band(self):
        return self._band

    @band.setter
    def band(self, value):
        self._band = value
        self.selectedGenreChanged.emit(value)

    @property
    def album(self):
        return self._album

    @album.setter
    def album(self, value):
        self._album = value
        self.selectedGenreChanged.emit(value)
"""
