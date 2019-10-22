"""Module storing class that takes care of downolading wikipedia page."""

import collections  # lazy loaded
import logging
import pickle  # lazy loaded
import queue
import re  # lazy loaded
import sys
import time  # lazy loaded
from threading import Lock
from typing import TYPE_CHECKING, Dict, Optional, Type, Union

import bs4  # lazy loaded
import fuzzywuzzy.fuzz as fuzz  # lazy loaded
import wikipedia as wiki  # lazy loaded

from wiki_music.constants import OUTPUT_FOLDER
from wiki_music.utilities import (Control, ThreadWithTrace, for_all_methods,
                                  normalize_caseless, time_methods)

from .base import ParserBase

if TYPE_CHECKING:
    from pathlib import Path
    from wikipedia import WikipediaPage
    from bs4 import BeautifulSoup

    Bs4Soup = Optional["BeautifulSoup"]
    WikiPage = Optional["WikipediaPage"]

log = logging.getLogger(__name__)
nc = normalize_caseless


@for_all_methods(time_methods, exclude=["Preload"])
class WikiCooker(ParserBase):
    """Downloades wikipedia page and convertes it to WikipediaPage object.

    Subsequently important parts of the page are extracted to class attributes.
    Class has the ability to run preload of the page in background tread as the
    user types input values in GUI.

    Warnings
    --------
    This class is not ment to be instantiated, only inherited.

    References
    ----------
    https://www.crummy.com/software/BeautifulSoup/bs4/doc/: used to parse the
    wikipedia page
    https://pypi.org/project/wikipedia/: used to get the wikipedia page

    Parameters
    ----------
    protected_vars: bool
        defines if certain variables should be initialized by __init__ method
        or not

    Attributes
    ----------
    page: wikipedia.WikipediaPage
        downloaded page to be parsed by BeautifulSoup
    _soup: bs4.BeautifulSoup
        BeautibulSoup object representing the whole page
    _sections: Dict[str, bs4.BeautifulSoup]
        the :attr:`_soup` split to page sections indexed by their titles
    """

    _page: "WikiPage"
    _soup: "Bs4Soup"

    def __init__(self, protected_vars: bool) -> None:

        super().__init__(protected_vars=protected_vars)

        self._log.debug("cooker imports")

        if protected_vars:
            self._sections = {}
            self._page = None
            self._soup = None

            # control download and cook status are indexed by na of album
            self._wiki_downloaded: queue.Queue = queue.Queue(maxsize=1)
            self._soup_ready: queue.Queue = queue.Queue(maxsize=1)

        # control
        self.preload_running: bool = False
        self.getter_lock: Lock = Lock()
        self.error_msg: Optional[str] = None

        self._url: Union["Path", str] = ""

        # pass reference of current class instance to subclass
        self.Preload.outer_instance = self

        self._log.debug("cooker imports done")

    # TODO maybe we can move needed methods from outer class to preload so we
    # can have more instances of preload running at once, the results of each
    # instance would then be saved to dictionary indexed by the search name
    # and the Preload would not need to have access to outer namespace which
    # is ugly and dangerous ffrom maintainability perspective
    class Preload:
        """Contolling the preload of wikipedia page.

        It is totally self-contained exposes only start and stop methods.
        Aborts automatically when no album or band is specified.

        Attributes
        ----------
        _preload_thread: :class:`wiki_music.utilities.parser_utils.ThreadWithTrace`
            stopable thread instance so we can kill preload
        outer_instance: :class:`wiki_music.library.process_page.WikipediaParser`
            instance of the outer class so the inner class can manipulate
            its attributes
        """

        _preload_thread: Optional[ThreadWithTrace] = None
        outer_instance: Optional[Type[ParserBase]] = None

        @classmethod
        def start(cls):
            """Starts running the preload, variables are read from outer class.

            Note
            ----
            Currently running preload is stopped before new one is started
            """
            cls.stop()

            # first empty records of previous download
            try:
                cls.outer_instance._wiki_downloaded.get(block=False)
            except queue.Empty:
                pass
            try:
                cls.outer_instance._wiki_downloaded.get(block=False)
            except queue.Empty:
                pass
            cls.outer_instance.error_msg = None

            if not all([cls.outer_instance._album, cls.outer_instance._band]):
                return

            log.debug(f"Starting wikipedia preload for: "
                      f"{cls.outer_instance._album} by "
                      f"{cls.outer_instance._band}")

            cls._preload_thread = ThreadWithTrace(
                target=cls.outer_instance._preload_run, name="WikiPreload")
            cls._preload_thread.start()

        @classmethod
        def stop(cls):
            """Method that stops currently running preload."""
            if cls.outer_instance.preload_running:

                log.debug(f"Stoping wikipedia preload for: "
                          f"{cls.outer_instance._album} by "
                          f"{cls.outer_instance._band}")
                cls._preload_thread.kill()
                cls._preload_thread.join()

                cls.outer_instance.preload_running = False

    @property
    def url(self) -> Union["Path", str]:
        """Holds url of the wikipedia page from which the data was downloaded.

        When offline debugging is enabled, this property holds path to the
        pickle page file.

        :type: str

        See also
        --------
        :meth:`wiki_music.parser.in_out.ParserInOut.basic_out`
            method responsible for saving the pickled page to disk
        :meth:`_from_disk`
            method for loading the pickle page from disk
        """
        if self.offline_debug:
            self._url = (OUTPUT_FOLDER / self._album / "page.pkl").resolve()
        else:
            self._url = str(self._page.url)

        return self._url

    # TODO doesn't work without GUI
    def terminate(self, message: str):
        """Send message to GUI to ask user if he wishes to terminate the app.

        If the answer if yes than parser is destroyed and GUI terminated.

        See also
        --------
        :meth:`wiki_music.gui_lib.main_window.Checkers._exception_check`
            this method handles displaying the message to user
        :class:`wiki_music.utilities.sync.SharedVars`
            serves to pass message from parser to GUI

        Parameters
        ----------
        message: str
            message to show user when asking if app should terminate
        """
        if Control("ask_to_exit", message).response:
            # TODO this is not enough need to del all references to the class
            self.Preload.stop()
            del self
            if Control("deconstruct").response:
                sys.exit()

    # TODO if the propper page cannot be found we could show a dialog with a
    # list of possible matches for user to choose from
    def _check_band(self) -> bool:
        """Check if artist from input is the same as the one on wikipedia page.

        If the artist is not the same issues warning about mismatch and asks
        user if he wants to continue.

        See also
        --------
        :meth:`terminate`
            method that takes care of ending the app execution
        """
        album_artist = self._sections["infobox"].find(
            href="/wiki/Album")  # type: ignore
        if album_artist:
            album_artist = album_artist.parent.get_text()

            if fuzz.token_set_ratio(nc(self._band), nc(album_artist)) > 90:
                return True
            else:
                b = re.sub(r"[Bb]y|[Ss]tudio album", "", album_artist).strip()
                m = (f"The Wikipedia entry for album: {self._album} belongs to"
                     f" band: {b}\nThis probably means that entry for: "
                     f"{self._album} by {self._band} does not exist.")
                self._log.exception(m)
                self.terminate(m)

                return False
        else:
            return False

    def _preload_run(self):
        """Organizes the preload thread and calls other methods.

        Based on input decides how to load and parse the wikipedia page.

        See also
        --------
        :meth:`get_wiki`
            method to retrieve wikipedia page
        :meth:`cook_soup`
            method to parse the page
        """
        self.preload_running = True

        self.get_wiki(preload=True)

        if not self.error_msg:
            self.cook_soup()

            if not self.error_msg:
                # file path can be too long to show in GUI
                if isinstance(self.url, str):
                    url = self.url
                else:
                    url = "..." + str(self.url).rsplit("wiki_music", 1)[1]

                self._log.info(f"Found: {url}")

        if self.error_msg:
            self._log.info(f"Preload unsucessfull: {self.error_msg}")

        self.preload_running = False

    def get_wiki(self, preload=False) -> Optional[str]:
        """Gets wikipedia page uses offline or online version.

        Parameters
        ----------
        preload: bool
            tells the method if it is part of a running preload for GUI or not

        See also
        --------
        :attr:`wiki_music.utilities.sync.self.offline_debug`
            defines if online version is downloaded or offline pickle version
        :meth:`_from_disk`
            fetches the offline version of page
        :meth:`_from_web`
            fetches the online version of page
        """
        # when function is called from application,
        # wait until all preloads are finished and then continue
        if not preload:
            while self.preload_running:
                time.sleep(0.05)

        try:
            downloaded = self._wiki_downloaded.get(block=False) == self.ALBUM
        except queue.Empty:
            downloaded = False
        finally:
            if downloaded:
                return self.error_msg

        self._log.debug("getting wiki")

        if self.offline_debug:
            return self._from_disk()
        else:
            return self._from_web()

    def _from_web(self) -> Optional[str]:
        """Guesses the right wikipedia page from input and downloads it.

        Returns
        -------
        Optional[str]
            if some error occured return string with its description
        """
        self._log.debug("from web")

        searches = [
            f"{self._album} ({self._band} album)", f"{self._album} (album)",
            self._album
        ]

        try:
            for query in searches:
                self._log.debug(f"trying query: {query}")
                self._page = wiki.page(title=query, auto_suggest=True)
                summ = nc(self._page.summary)
                if nc(self._band) in summ and nc(self._album) in summ:
                    break
            else:
                self.error_msg = "Could not get wikipedia page."

        except wiki.exceptions.DisambiguationError as e:
            print("Found entries: {}\n...".format("\n".join(e.options[:3])))
            for option in e.options:
                if self._band in option:
                    print(f"\nSelecting: {option}\n")
                    self._page = wiki.page(option)
                    break
            else:
                self.error_msg = ("Couldn't select best album entry "
                                  "from wikipedia")

        except wiki.exceptions.PageError:
            try:
                self._page = wiki.page(f"{self._album} {self._band}")
            except wiki.exceptions.PageError as e:
                self.error_msg = "Album was not found on wikipedia"

        except wiki.exceptions.HTTPTimeoutError as e:
            self.error_msg = ("Search failed probably due to "
                              "poor internet connetion:")
        except Exception as e:
            self.error_msg = (f"Search failed with unspecified exception: {e}")
        else:
            self.error_msg = None
            self._wiki_downloaded.put(self.ALBUM)

        return self.error_msg

    def _from_disk(self) -> Optional[str]:
        """Load wikipedia page from pickle file on disk.

        Returns
        -------
        Optional[str]
            if some error occured return string with its description
        """
        # TODO pickle probably cannot handle some complex pages
        self._log.debug(f"loading pickle file {self.url}")
        if self.url.is_file():
            with self.url.open('rb') as f:
                self._log.debug("loading ...")
                self._page = pickle.load(f)
            self._log.debug("done")
            self.error_msg = None
            self._wiki_downloaded.put(self.ALBUM)
        else:
            self.error_msg = "Cannot find cached offline version of page."

        return self.error_msg

    def cook_soup(self) -> Optional[str]:
        """Parse downloaded wikipedia page with bs4 to BeautifulSoup object.

        Then splits the page to dictionary of sections, where each section
        is indexed by its name.

        Returns
        -------
        Optional[str]
            if some error occured return string with its description
        """
        try:
            cooked = self._soup_ready.get(block=False) == self.ALBUM
        except queue.Empty:
            cooked = False
        finally:
            if cooked:
                return self.error_msg

        # make BeautifulSoup black magic
        self._soup = bs4.BeautifulSoup(self._page.html(),
                                       features="lxml")  # type: ignore

        # split page to parts
        self._sections = collections.OrderedDict()

        # h2 mark the main haedings in document
        for h2 in self._soup.find_all("h2"):

            # heading should have a name marked by css class mw-headline
            # if not skip it
            name = h2.find("span", class_="mw-headline", id=True)
            if name:
                name = name["id"].lower()
            else:
                continue

            # the text belonging to each section is at the same level as
            # headings, so iterate over h2 siblings until we come across next
            # section title in document with a name
            value = []
            for s in h2.find_next_siblings():
                if s.name == "h2" and h2.find(
                        "span", class_="mw-headline", id=True):
                    break
                else:
                    value.append(s)

            self._sections[name] = value

        # add infobox to the sections
        self._sections["infobox"] = self._soup.find(
            "table", class_="infobox vevent haudio")

        # check if the album belongs to band that was requested
        if self._check_band():
            self._soup_ready.put(self.ALBUM)
            self.error_msg = None
        else:
            self.error_msg = "Album doesnt't belong to the requested band"

        return self.error_msg
