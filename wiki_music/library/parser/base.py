"""Base module for all parser classes."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from wiki_music.utilities import MultiLog

__all__ = ["ParserBase"]

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from bs4 import BeautifulSoup
    Bs4Soup = Optional["BeautifulSoup"]

SList = List[str]  # list of strings
PList = List[Path]  # list of strings
IList = List[int]  # list of ints
NSList = List[SList]  # nested list
NIList = List[IList]  # nested list


class ParserBase:
    """The base clas for all :mod:`wiki_music.parser` subclasses.

    Defines the necessary attributes. The uppercased attributes correspond to
    tag names for easier access.

    Warnings
    --------
    This class is not ment to be instantiated, only inherited.

    Note
    ----
    Uppercased propertie corespond with TAG names so we can easilly use getattr
    and setattr methods

    Attributes
    ----------
    offline_debug: bool
        determines if app will run in offline debug mode
    write_json: bool
        determines if tracklist in  format will be output
    multi_threaded: bool
        whether to run parts of the code in parallel
    _contents: List[str]
        stores the wikipedia page contents
    _disk_sep: List[int]
        list of tracks separating disks e.g. if CD 1 = (1, 13) and
        CD 2 = (14, 20), _disk_sep = [0, 12, 19] the offset by one if because
        of zero first index
    _disks: List[list]
        holds album disks titles
    genres: List[str]
        list of genres found in wikipedia page
    _header: List[str]
        tracklist table headers
    NLTK_names: List[str]
        list of Person Named Entities extracted from wikipedia page by nltk.
        See :attr:`wiki_music.library.parser.process_page.WikipediaParser.NLTK_names`
        for details on how and from which parts of test the names are extracted
    _personnel: List[str]
        list holding adittional personnel participating on album
    _appearences: List[List[int]]
        list coresponding to personnel holding for each person list of tracks
        that the said person has appeared on
    _subtracks: List[List[str]]
        each entry holds list of subtracks for one track
    _subtypes: List[List[str]]
        each entry holds list of types for each subtrack
    work_dir: Path
        string with path to directory with music files, this variable can be
        protected from reseting in __init__ method
    log: :class:`wiki_music.utilities.utils.MultiLog`
        instance of MUltiLog which sends messages to logger and GUI
    _sections: Dict[str, List[Bs4Soup]]
        dictionary of lists of BeautifulSoup objects each entry in the
        dict contains one whole section of the page and is indexed by that
        section title
    """

    files: PList
    bracketed_types: SList
    _sections: Dict[str, List["Bs4Soup"]]

    def __init__(self, protected_vars: bool) -> None:

        log.debug("parser base")

        # lists 1D
        self._contents: SList = []
        self._tracks: SList = []
        self._types: SList = []
        self._disc_num: IList = []
        self._disk_sep: IList = []
        self._disks: List[list] = []
        self.genres: SList = []
        self._header: SList = []
        self._lyrics: SList = []
        self._NLTK_names: SList = []
        self._numbers: SList = []
        self._personnel: SList = []
        self._bracketed_types: SList = []
        self._files: PList = []

        # lists 2D
        self._appearences: NIList = []
        self._artists: NSList = []
        self._composers: NSList = []
        self._subtypes: NSList = []
        self._subtracks: NSList = []

        # bytes
        self._cover_art: bytes = bytes()

        # strings
        self._release_date: str = ""
        self._selected_genre: str = ""

        # atributes protected from GUIs reinit method
        # when new search is started
        if protected_vars:
            self._album: str = ""
            self._band: str = ""
            self.offline_debug = False
            self.write_json = False
            self.multi_threaded= True
            self.work_dir: Path = Path("")
            self._log: MultiLog = MultiLog(log)
            self._GUI = False

        self._log.debug("parser base done")

    def reinit(self, protected_vars: bool):
        """Reinitializes parser variables."""
        ParserBase.__init__(self, protected_vars=protected_vars)

    def __len__(self):
        """Return parser number of tracks."""
        return len(self._numbers)

    def __bool__(self):
        """Return True if parser has at least one track."""
        return bool(self.__len__())

    @property
    def ALBUM(self) -> str:
        """String with album name.

        This attribute can be protected from reseting in __init__ method.

        :type: str
        """
        return self._album

    @ALBUM.setter
    def ALBUM(self, value: str):
        self._album = value

    @property
    def ALBUMARTIST(self) -> str:
        """String with band name.

        This attribute can be protected from reseting in __init__ method.

        :type: str
        """
        return self._band

    @ALBUMARTIST.setter
    def ALBUMARTIST(self, value: str):
        self._band = value

    @property
    def ARTIST(self) -> NSList:
        """Each entry in list holds list of artists for one track.

        :type: List[List[str]]
        """
        return self._artists

    @ARTIST.setter
    def ARTIST(self, value: NSList):
        self._artists = value

    @property
    def COMPOSER(self) -> NSList:
        """Each entry in list holds list of composers for one track.

        :type: List[List[str]]
        """
        return self._composers

    @COMPOSER.setter
    def COMPOSER(self, value: NSList):
        self._composers = value

    @property
    def COVERART(self) -> bytes:
        """Holds cover art read into memory as a bytes object.

        :type: bytes
        """
        return self._cover_art

    @COVERART.setter
    def COVERART(self, value: bytes):
        self._cover_art = value

    @property
    def DATE(self) -> str:
        """Album release date.

        :type: str
        """
        return self._release_date

    @DATE.setter
    def DATE(self, value: str):
        self._release_date = value

    @property
    def DISCNUMBER(self) -> IList:
        """List containing dicsnumber for every track.

        :type: List[int]
        """
        return self._disc_num

    @DISCNUMBER.setter
    def DISCNUMBER(self, value: IList):
        self._disc_num = value

    @property
    def GENRE(self) -> str:
        """Holds the album genre selected automatically or by user.

        If :attr:`genres` is a list with one item, than it is that item,
        otherwise user input is required to select from genres list.

        :type: str
        """
        return self._selected_genre

    @GENRE.setter
    def GENRE(self, value: str):
        self._selected_genre = value

    @property
    def LYRICS(self) -> SList:
        """List of lyrics coresponding to each track.

        :type: List[str]
        """
        return self._lyrics

    @LYRICS.setter
    def LYRICS(self, value: SList):
        self._lyrics = value

    @property
    def TITLE(self) -> SList:
        """List of track names.

        :type: List[str]
        """
        return self._tracks

    @TITLE.setter
    def TITLE(self, value: SList):
        self._tracks = value

    @property
    def TRACKNUMBER(self) -> SList:
        """List of numbers for each track.

        :type: List[str]
        """
        return self._numbers

    @TRACKNUMBER.setter
    def TRACKNUMBER(self, value: SList):
        self._numbers = value

    @property
    def FILE(self) -> SList:
        """List of files on local disk corresponding to each track.

        :type: List[str]
        """
        return [str(f) if f else f for f in self.files]

    @FILE.setter
    def FILE(self, value: SList):
        self._files = [Path(v) if v.strip() else None for v in value]

    @property
    def TYPE(self) -> SList:
        """List of track types.

        :type: List[str]
        """
        return self.bracketed_types

    @TYPE.setter
    def TYPE(self, value: SList):
        self._bracketed_types = value


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
