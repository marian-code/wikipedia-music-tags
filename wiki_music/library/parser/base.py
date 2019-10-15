""" Base module for all parser classes from which they import ParserBase
class that sets all the default attributes.
"""

import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from wiki_music.utilities import MultiLog

__all__ = ["ParserBase"]

log = logging.getLogger(__name__)

# only for static typechecker, is False at runtime
if TYPE_CHECKING:
    from wikipedia import WikipediaPage
    from bs4 import BeautifulSoup

    Bs4Soup = Optional["BeautifulSoup"]
    WikiPage = Optional["WikipediaPage"]

SList = List[str]  # list of strings
IList = List[int]  # list of ints
NSList = List[SList]  # nested list
NIList = List[IList]  # nested list


class ParserBase:
    """The base clas for all :mod:`wiki_music.parser` subclasses. Defines the
    necessary attributes. The uppercased attributes correspond to tag names
    for easier access.

    Warnings
    --------
    This class is not ment to be instantiated, only inherited.

    Note
    ----
    Uppercased propertie corespond with TAG names so we can easilly use getattr
    and setattr methods

    Attributes
    ----------
    contents: List[str]
        stores the wikipedia page contents
    disk_sep: List[int]
        list of tracks separating disks e.g. if CD 1 = (1, 13) and
        CD 2 = (14, 20), disk_sep = [0, 12, 19] the offset by one if because of
        zero first index
    disks: List[list]
        holds album disks titles
    genres: List[str]
        list of genres found in wikipedia page
    header: List[str]
        tracklist table headers
    NLTK_names: List[str]
        list of Person Named Entities extracted from wikipedia page by nltk.
        See :meth:`wiki_music.library.parser.process_page.WikipediaParser.extract_names`
        for details on how and from which parts of test the names are extracted
    personnel: List[str]
        list holding adittional personnel participating on album
    appearences: List[List[int]]
        list coresponding to personnel holding for each person list of tracks
        that the said person has appeared on
    subtracks: List[List[str]]
        each entry holds list of subtracks for one track
    sub_types: List[List[str]]
        each entry holds list of types for each subtrack
    work_dir: str
        string with path to directory with music files, this variable can be
        protected from reseting in __init__ method
    log: :class:`wiki_music.utilities.utils.MultiLog`
        instance of MUltiLog which sends messages to logger and
        :class:`wiki_music.utilities.sync.SharedVars`
    sections: Dict[str, List[Bs4Soup]]
        dictionary of lists of BeautifulSoup objects each entry in the
        dict contains one whole section of the page and is indexed by that
        section title
    """

    files: SList
    bracketed_types: SList
    sections: Dict[str, List["Bs4Soup"]]
    page: "WikiPage"
    soup: "Bs4Soup"

    def __init__(self, protected_vars: bool) -> None:

        log.debug("parser base")

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
        self.appearences: NIList = []
        self.artists: NSList = []
        self.composers: NSList = []
        self.sub_types: NSList = []
        self.subtracks: NSList = []

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
            self.log: MultiLog = MultiLog(log)
            self.GUI = False

        self.log.debug("parser base done")

    def __len__(self):
        return len(self.numbers)

    def __bool__(self):
        return bool(self.__len__())

    @property
    def ALBUM(self) -> str:
        """ string with album name, this variable can be protected from
        reseting in __init__ method.
        
        :type: str
        """
        return self.album

    @ALBUM.setter
    def ALBUM(self, value: str):
        self.album = value

    @property
    def ALBUMARTIST(self) -> str:
        """ string with band name, this variable can be protected from reseting
        in __init__ method.

        :type: str
        """
        return self.band

    @ALBUMARTIST.setter
    def ALBUMARTIST(self, value: str):
        self.band = value

    @property
    def ARTIST(self) -> NSList:
        """ Each entry in list holds list of artists for one track.

        :type: List[List[str]]
        """
        return self.artists

    @ARTIST.setter
    def ARTIST(self, value: NSList):
        self.artists = value

    @property
    def COMPOSER(self) -> NSList:
        """ Each entry in list holds list of composers for one track.

        :type: List[List[str]]
        """
        return self.composers

    @COMPOSER.setter
    def COMPOSER(self, value: NSList):
        self.composers = value

    @property
    def COVERART(self) -> bytearray:
        """ Holds coverart read into memory as a bytes object. 

        :type: bytearray
        """
        return self.cover_art

    @COVERART.setter
    def COVERART(self, value: bytearray):
        self.cover_art = value

    @property
    def DATE(self) -> str:
        """ Album release date.

        :type: str
        """
        return self.release_date

    @DATE.setter
    def DATE(self, value: str):
        self.release_date = value

    @property
    def DISCNUMBER(self) -> IList:
        """List containing dicsnumber for every track.

        :type: List[int]
        """
        return self.disc_num

    @DISCNUMBER.setter
    def DISCNUMBER(self, value: IList):
        self.disc_num = value

    @property
    def GENRE(self) -> str:
        """If :attr:`genres` is a list with one item, than it is that item,
        otherwise user input is required to select from genres list.

        :type: str
        """
        return self.selected_genre

    @GENRE.setter
    def GENRE(self, value: str):
        self.selected_genre = value

    @property
    def LYRICS(self) -> SList:
        """List of lyrics coresponding to each track.

        :type: List[str]
        """
        return self.lyrics

    @LYRICS.setter
    def LYRICS(self, value: SList):
        self.lyrics = value

    @property
    def TITLE(self) -> SList:
        """ List of track names.

        :type: List[str]
        """
        return self.tracks

    @TITLE.setter
    def TITLE(self, value: SList):
        self.tracks = value

    @property
    def TRACKNUMBER(self) -> SList:
        """ List of numbers for each track.

        :type: List[str]
        """
        return self.numbers

    @TRACKNUMBER.setter
    def TRACKNUMBER(self, value: SList):
        self.numbers = value

    @property
    def FILE(self) -> SList:
        """ List of files on local disk corresponding to each track.

        :type: List[str]
        """
        return self.files

    @FILE.setter
    def FILE(self, value: SList):
        self.files = value

    @property
    def TYPE(self) -> SList:
        """ List of track types.

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
