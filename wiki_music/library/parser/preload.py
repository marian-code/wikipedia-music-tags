"""Module storing class that takes care of downolading wikipedia page."""

import collections  # lazy loaded
import logging
import pickle  # lazy loaded
import re  # lazy loaded
import sys
from queue import Queue
from threading import Event
from time import sleep
from typing import (
    TYPE_CHECKING, Any, Dict, Generator, List, Optional, Tuple, Type, Union)

import bs4  # lazy loaded
import rapidfuzz.fuzz as fuzz  # lazy loaded
import wikipedia as wiki  # lazy loaded

from wiki_music.constants import OUTPUT_FOLDER
from wiki_music.utilities import (Control, MultiLog, ThreadWithTrace,
                                  normalize_caseless)

from .base import ParserBase

if TYPE_CHECKING:
    from pathlib import Path
    from wikipedia import WikipediaPage
    from bs4 import BeautifulSoup
    from bs4.element import Tag

    Sections = Dict[str, List[Tag]]

log = logging.getLogger(__name__)
nc = normalize_caseless


class CircularDict(collections.OrderedDict):
    """Circular dict-like indexable stack with limited capacity.

    If maximum length is specified, the oldest item is discarded after adding
    a new one if stack reached its maximum dict capacity.

    Parameters
    ----------
    maxlen: Optional[int]
        maximum stack capacity
    """

    def __init__(self, maxlen=Optional[int]) -> None:

        super().__init__()

        self._maxlen = maxlen

    def __setitem__(self, key: str, value: Any):

        if self._maxlen and self._maxlen <= len(self):
            self.popitem(last=False)

        super().__setitem__(key, value)


class Preload:
    """Contoling the preload of wikipedia page.

    It is totally self-contained exposes only start, stop and pause methods.
    Aborts automatically when no album or band is specified. After preload is
    complete, results are available in :attr:`results`

    Attributes
    ----------
    message: :class:`Queue`
        caches preload progress messages
    """

    _preload_thread: ThreadWithTrace
    _url: Union["Path", str]
    _page: "WikipediaPage"
    _soup: "BeautifulSoup"
    _sections: "Sections"
    _pause: Event
    _done: Event
    _error: str
    message: Queue

    def __init__(self, album: str, band: str, offline_debug: bool) -> None:

        # preload variables
        self._album = album
        self._band = band
        self._offline_debug = offline_debug

        # control
        self._log = MultiLog(log)
        self._pause = Event()
        self._done = Event()

        # progress info
        self.message = Queue()

        # set wait flag to true, default state is false so event will be waited
        self._pause.set()

        self._preload_thread = ThreadWithTrace(target=self._preload_run,
            name=f"Preload-{'-'.join(self._preload_id)}", daemon=True)
        self._preload_thread.start()

    @property
    def _check_band(self) -> bool:
        """Check if artist from input is the same as the one on wikipedia page.

        If the artist is not the same issues warning about mismatch and asks
        user if he wants to continue.

        See also
        --------
        :meth:`terminate`
            method that takes care of ending the app execution
        """
        try:
            album_artist = self._sections["infobox"][0].find(
                href=re.compile(r"/wiki/Album(#Live)?", re.I))  # type: ignore
        except IndexError:
            # infobox was not found so probably we didn't get album page
            self._log.exception(f"The wikipedia page: {self._url} probably "
                                f"does not belong to album: {self._album}")
            return False

        if album_artist:
            album_artist = album_artist.parent.get_text()

            if fuzz.token_set_ratio(self._band, album_artist, score_cutoff=90):
                return True
            else:
                b = re.sub(r"[Bb]y|[Ss]tudio album", "", album_artist).strip()
                m = (f"The Wikipedia entry for album: {self._album} belongs to"
                     f" band: {b}\nThis probably means that entry for: "
                     f"{self._album} by {self._band} does not exist.")
                self._log.exception(m)

                return False
        else:
            return False

    @property
    def _preload_id(self) -> Tuple[str, str, str]:
        return self._album, self._band, f"offline: {self._offline_debug}"

    def _preload_run(self):
        """Organizes the preload thread and calls other methods.

        Based on input decides how to load and parse the wikipedia page.

        See also
        --------
        :meth:`_from_web`
            method to retrieve wikipedia page from internet
        :meth:`_from_disk`
            method to retrieve pickled wikipedia page from disk
        :meth:`_cook_soup`
            method to parse the page
        """
        log.debug("getting wiki")
        if self._offline_debug:
            self.message.put("Using offline cached page insted of web page")
            error = self._from_disk()
        else:
            self.message.put(f"Searching for: {self._album} by {self._band}")
            error = self._from_web()

        # here thread can be paused
        self._pause.wait()

        if not error:
            self.message.put(f"Found at: {self._url}")
            self.message.put("Cooking Soup")
            error = self._cook_soup()

            if not error:
                self.message.put("Soup ready")

                # file path can be too long to show in GUI
                if isinstance(self._url, str):
                    url = self._url
                else:
                    url = "..." + str(self._url).rsplit("wiki_music", 1)[1]

                self._log.info(f"Found: {url}")

        if error:
            self._page = None
            self._soup = None
            self._url = None
            self._error = error
            self._log.info(f"Preload unsucessfull: {error}")
        else:
            self._error = None

        # stop the progress message generator
        self.message.put(None)

        # anounce, preload is finished
        self._done.set()

    def _from_web(self) -> Optional[str]:
        """Guesses the right wikipedia page from input and downloads it.

        Returns
        -------
        Optional[str]
            if some error occured return string with its description
        """
        log.debug("from web")

        searches = [f"{self._album} ({self._band} album)",
                    f"{self._album} (album)",
                    self._album]

        try:
            for query in searches:
                log.debug(f"trying query: {query}")
                page = wiki.page(title=query, auto_suggest=True)

                responses = dict()

                http_album = page.url.rsplit("/", 1)[1].replace("_", " ")
                probability = fuzz.token_sort_ratio(http_album, self._album)
                if probability > 90:
                    self._page = page
                    self._url = self._page.url
                    return None
                else:
                    responses[probability] = page
            else:
                self._page = responses[max(responses.keys())]
                self._url = self._page.url
                return None
            """
                # TODO this might be overkill
                summ = nc(self._page.summary)
                if nc(self._band) in summ and nc(self._album) in summ:
                    self._url = self._page.url
                    return None
                else:
                    log.debug(f"couldn't find {self._album} and/or "
                              f"{self._band} in {self._page.url} summary")
                
            else:
                return "Could not get wikipedia page."
            """
        except wiki.exceptions.DisambiguationError as e:
            # TODO if the propper page cannot be found we could show a dialog
            # TODO with a list of possible matches for user to choose from
            log.debug(f"Found entries: {', '.join(e.options[:3])}...")
            for option in e.options:
                if self._band in option:
                    log.debug(f"\nSelecting: {option}\n")
                    self._page = wiki.page(option)
                    self._url = self._page.url
                    return None
            else:
                return "Couldn't select best album entry from wikipedia"
        except wiki.exceptions.PageError:
            return "Album was not found on wikipedia"
        except wiki.exceptions.HTTPTimeoutError as e:
            return "Search failed probably due to poor internet connetion"
        except Exception as e:
            return f"Search failed with unspecified exception: {e}"

    def _from_disk(self) -> Optional[str]:
        """Load wikipedia page from pickle file on disk.

        Returns
        -------
        Optional[str]
            if some error occured return string with its description
        """
        path = OUTPUT_FOLDER / self._album / "page.pkl"
        log.debug(f"loading pickle file {path}")

        # TODO pickle probably cannot handle some complex pages
        if path.is_file():
            try:
                with path.open('rb') as f:
                    self._page = pickle.load(f)
            except pickle.UnpicklingError as e:
                log.exception(e)
                return "Error when unpickling offline page"
            else:
                self._url = path
                return None
        else:
            return "Cannot find offline cached version of the page."

    def _cook_soup(self) -> Optional[str]:
        """Parse downloaded wikipedia page with bs4 to BeautifulSoup object.

        Then splits the page to dictionary of sections, where each section
        is indexed by its name.

        Returns
        -------
        Optional[str]
            if some error occured return string with its description
        """
        log.debug("building BeautifulSoup parse tree")
        # make BeautifulSoup black magic
        self._soup = bs4.BeautifulSoup(self._page.html(),
                                       features="lxml")  # type: ignore

        log.debug("splitting page to sections")
        # split page to sections
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
                if s.name == "h2" and h2.find("span", class_="mw-headline",
                                              id=True):
                    break
                else:
                    value.append(s)

            self._sections[name] = value

        # add infobox to the sections
        self._sections["infobox"] = self._soup.find_all(
            "table", class_="infobox vevent haudio")

        # check if the album belongs to band that was requested
        if self._check_band:
            return None
        else:
            return "Album doesnt't belong to the input band"

    def stop(self):
        """Method that stops currently running preload."""
        self.unpause()  # must be unpaused otherwise stop does not work
        self._preload_thread.kill()
        self._preload_thread.join()

    def pause(self):
        """Pause the preload thread."""
        if not self._done.is_set():
            log.debug(f"pausing preload: {self._preload_id}")
            self._pause.clear()
        else:
            log.debug(f"preload already finshed: {self._preload_id}")

    def unpause(self):
        """Unpause the preload thread."""
        if not self._pause.is_set():
            log.debug(f"unpausing preload: {self._preload_id}")
            self._pause.set()
        if self._done.is_set():
            self.message.put(None)

    @property
    def results(self) -> Tuple["WikipediaPage", "BeautifulSoup", "Sections",
                               Union[str, "Path"], Optional[str]]:
        """Returns downloaded and preprocessed wikipedia page.

        Waits until results are available, only then returns.

        Returns
        -------
        WikipediaPage
            wikipedia page object
        bs4.BeautifulSoup
            html parsed tree
        Dict[List[bs4.element.Tags]]
            sections of the page split into dict indexed by section names
        Union[str, Path]
            url address of the page or Path to offline pickle file
        str
            error string, or none if no exceptions occured
        """
        # wait until preload is finished
        self._done.wait()
        log.debug("preload done, returning results")
        return self._page, self._soup, self._sections, self._url, self._error


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
    _page: wikipedia.WikipediaPage
        downloaded page to be parsed by BeautifulSoup
    _soup: bs4.BeautifulSoup
        BeautibulSoup object representing the whole page
    _sections: Dict[str, List["Tag"]]
        the :attr:`_soup` split to page sections indexed by their titles
    _url: Union["Path", str]
        the page url or path to pickle file for offline debug
    """

    _url: Union["Path", str]
    _page: "WikipediaPage"
    _soup: "BeautifulSoup"
    _sections: Dict[str, List["Tag"]]
    _preload_cache: Dict[Tuple[str, str, str], Preload]
    _preload_in_thread: bool

    def __init__(self, protected_vars: bool) -> None:

        super().__init__(protected_vars=protected_vars)

        self._log.debug("cooker setup")

        # fixed length circular dictionary, oldest items are discarded
        # when maximum length is reached
        self._preload_cache = CircularDict(maxlen=10)

    @property
    def _preload_id(self) -> Tuple[str, str, str]:
        """Get unique id for each preload instance.

        Id is a three tuple of album, band and offline_debug flag

        :type: Tuple[str, str, str]
        """
        return (self._album, self._band, f"offline: {self.offline_debug}")

    def start_preload(self):
        """Starts preload instance and caches its reference under unique id.

        Other running preloads are paused. Maximum number of preloads is 10,
        1 running and 9 paused. If new preload is added to cache, the the
        oldest one is destroyed.
        """
        if not all([self._album, self._band]):
            log.warning("No input!")
            return

        pid = self._preload_id

        # if preload config does not exist in cache, run it
        if pid not in self._preload_cache:
            log.debug(f"starting preload for: {pid}")
            p = Preload(self._album, self._band, self.offline_debug)
            self._preload_cache[pid] = p

            log.debug("pausing other preloads")
            # pause other running preloads
            for i, preload in self._preload_cache.items():
                if i != pid:
                    preload.pause()
        # if preload is already in cahce, run it
        else:
            log.debug(f"preload already present {pid}")
            self._preload_cache[pid].unpause()

    def stop_preload(self):
        """Stops all running preloads and delete reference from cache."""
        while len(self._preload_cache) > 0:
            preload_id, preload = self._preload_cache.popitem()
            log.debug(f"stopping {preload_id}")
            preload.stop()

        log.debug("preloads stopped")

    def _get_preload_progress(self) -> Generator[str, None, None]:
        """Generator, outputs preload progress messages.

        Yields
        ------
        str
            progress messages of preload instance
        """
        log.debug("yielding preload progress messages")
        # start preload, will be skipped if it is already done
        self.start_preload()

        while True:
            msg = self._preload_cache[self._preload_id].message.get()
            if msg:
                yield msg
            else:
                return

    def get_wiki(self) -> Optional[str]:
        """Wait until preload is finished, then return downloaded data.

        Returns
        -------
        Optional[str]
            error string if some error occured
        """
        # start preload, will be skipped if it is already done
        self.start_preload()

        log.debug("waiting, on preload results")

        # get page for actual album and artist
        self._page, self._soup, self._sections, self.url, error = (
            self._preload_cache[self._preload_id].results)

        # stop all preloads
        self.stop_preload()

        # if wrong wikipedia page was found ask to exit
        if error == "Album doesnt't belong to the input band":
            self.terminate(error)

        return error

    # TODO doesn't work without GUI
    def terminate(self, message: str):
        """Send message to GUI to ask user if he wishes to terminate the app.

        If the answer if yes than parser is destroyed and GUI terminated.

        See also
        --------
        :meth:`wiki_music.gui_lib.main_window.Checkers._exception_check`
            this method handles displaying the message to user
        :class:`wiki_music.utilities.sync.Control`
            serves to pass message from parser to GUI

        Parameters
        ----------
        message: str
            message to show user when asking if app should terminate
        """
        if Control("ask_to_exit", message).response:
            # TODO this is not enough need to del all references to the class
            self.stop_preload()
            del self
            if Control("deconstruct").response:
                sys.exit()
