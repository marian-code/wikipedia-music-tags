class VariableProxy:
    """ Properties with same names as tags act as a proxy to parser variables
        for convenient access."""

    def __init__(self):
        pass

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
    def ARTIST(self) -> list:
        return self.artists

    @ARTIST.setter
    def ARTIST(self, value: list):
        self.artists = value

    @property
    def COMPOSER(self) -> list:
        return self.composers

    @COMPOSER.setter
    def COMPOSER(self, value: list):
        self.composers = value

    @property
    def DATE(self) -> str:
        return self.release_date

    @DATE.setter
    def DATE(self, value: str):
        self.release_date = value

    @property
    def DISCNUMBER(self) -> list:
        return self.disc_num

    @DISCNUMBER.setter
    def DISCNUMBER(self, value: list):
        self.disc_num = value

    @property
    def GENRE(self) -> str:
        return self.selected_genre

    @GENRE.setter
    def GENRE(self, value: str):
        self.selected_genre = value

    @property
    def LYRICS(self) -> list:
        return self.lyrics

    @LYRICS.setter
    def LYRICS(self, value: list):
        self.lyrics = value

    @property
    def UNSYNCEDLYRICS(self) -> list:
        return self.lyrics

    @UNSYNCEDLYRICS.setter
    def UNSYNCEDLYRICS(self, value: list):
        self.lyrics = value

    @property
    def TITLE(self) -> list:
        return self.tracks

    @TITLE.setter
    def TITLE(self, value: list):
        self.tracks = value

    @property
    def TRACKNUMBER(self) -> list:
        return self.numbers

    @TRACKNUMBER.setter
    def TRACKNUMBER(self, value: list):
        self.numbers = value

    @property
    def FILE(self) -> list:
        return self.files

    @FILE.setter
    def FILE(self, value: list):
        self.files = value

    @property
    def TYPE(self) -> list:
        return self.bracketed_types

    @TYPE.setter
    def TYPE(self, value: list):
        self.bracketed_types = value


# TODO needs QThreads
"""
from wiki_music.gui.qt_importer import Signal, QObject


class GuiVariableProxy(VariableProxy, QObject):

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
