""" This module stores class hat takes care of downolading wikipedia page. """

import collections  # lazy loaded
import pickle  # lazy loaded
import re  # lazy loaded
import sys
import time  # lazy loaded
from os import path
from threading import Lock
from typing import Optional, Type

import bs4  # lazy loaded
import fuzzywuzzy.fuzz as fuzz  # lazy loaded
import wikipedia as wiki  # lazy loaded

from wiki_music.constants import OUTPUT_FOLDER
from wiki_music.utilities import (
    SharedVars, ThreadWithTrace, for_all_methods, log_parser,
    normalize_caseless, time_methods)

from .base import ParserBase

nc = normalize_caseless

log_parser.debug("cooker imports done")


@for_all_methods(time_methods, exclude=["Preload"])
class WikiCooker(ParserBase):
    """ Class for downloading wikipedia page which is then converted to
    WikipediaPage object. Subsequently important parts of the page are
    extracted to class attributes. Class has the ability to run preload of the
    page in background tread as the user types input values in GUI.

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
    soup: bs4.BeautifulSoup
        BeautibulSoup object representing the whole page
    sections: Dict[str, bs4.BeautifulSoup]
        the :attr:`soup` split to page sections indexed by their titles
    """   

    def __init__(self, protected_vars: bool) -> None:

        super().__init__(protected_vars=protected_vars)

        log_parser.debug("cooker imports")

        if protected_vars:
            self.sections = {}
            self.page = None
            self.soup = None

        # control
        self.wiki_downloaded: bool = False
        self.soup_ready: bool = False
        self.preload_running: bool = False
        self.getter_lock: Lock = Lock()
        self.error_msg: Optional[str] = None

        self._url = ""

        # pass reference of current class instance to subclass
        self.Preload.outer_instance = self

        log_parser.debug("cooker imports done")

    # TODO maybe we can move needed methods from outer class to preload so we
    # can have more instances of preload running at once, the results of each
    # instance would then be saved to dictionary indexed by the search name
    # and the Preload would not need to have access to outer namespace which
    # is ugly and dangerous ffrom maintainability perspective
    class Preload:
        """ Class for contolling the preload of wikipedia page. It is totally
        self-contained exposes only start and stop methods.

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
            """ Method which starts running the preload, needed variables are
            read from outer class.
            
            Note
            ----
            Currently running preload is stopped before new one is started
            """

            cls.stop()

            cls.outer_instance.wiki_downloaded = False
            cls.outer_instance.soup_ready = False
            cls.outer_instance.error_msg = None

            log_parser.debug(f"Starting wikipedia preload for: "
                             f"{cls.outer_instance.album} by "
                             f"{cls.outer_instance.band}")

            cls._preload_thread = ThreadWithTrace(
                target=cls.outer_instance._preload_run,
                name="WikiPreload")
            cls._preload_thread.start()

        @classmethod
        def stop(cls):
            """ Method that stops currently running preload. """

            if cls.outer_instance.preload_running:

                log_parser.debug(f"Stoping wikipedia preload for: "
                                 f"{cls.outer_instance.album} by "
                                 f"{cls.outer_instance.band}")
                cls._preload_thread.kill()
                cls._preload_thread.join()

                cls.outer_instance.preload_running = False

    @property
    def url(self) -> str:
        """ Holds url of the wikipedia page from which the data was downloaded.
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

        if not self._url:
            try:
                self._url = str(self.page.url)  # type: ignore
            except AttributeError:
                self._url = path.join(OUTPUT_FOLDER, self.album, "page.pkl")
        return self._url

    # TODO doesn't work without GUI
    def terminate(self, message: str):
        """ Method that send message to GUI which than asks user if he wishes
        to terminate the app. If the answer if yes than parser is destroyed
        and GUI terminated.

        See also
        --------
        :meth:`wiki_music.gui_lib.main_window.Checkers.__exception_check__`
            this method handles displaying the message to user
        :class:`wiki_music.utilities.sync.SharedVars`
            serves to pass message from parser to GUI

        Parameters
        ----------
        message: str
            message to show user when asking if app should terminate
        """

        SharedVars.ask_exit = message
        SharedVars.wait_exit = True

        while SharedVars.wait_exit:
            time.sleep(0.05)

        if SharedVars.terminate_app:
            # TODO this is not enough need to del all references to the class
            self.Preload.stop()
            del self
            sys.exit()

    # TODO if the propper page cannot be found we could show a dialog with a
    # list of possible matches for user to choose from
    def _check_band(self) -> bool:
        """ Check if the artist hat was input in search is the same as the one
        found on wikipedia page. If not issues warning about mismatch and asks
        user if he wants to continue.

        See also
        --------
        :meth:`terminate`
            method that takes care of ending the app execution
        """

        album_artist = self.sections["infobox"].find(href="/wiki/Album")  # type: ignore
        if album_artist:
            album_artist = album_artist.parent.get_text()
            
            if fuzz.token_set_ratio(nc(self.band), nc(album_artist)) > 90:
                return True
            else:
                b = re.sub(r"[Bb]y|[Ss]tudio album", "", album_artist).strip()
                m = (f"The Wikipedia entry for album: {self.album} belongs to "
                     f"band: {b}\nThis probably means that entry for: "
                     f"{self.album} by {self.band} does not exist.")
                log_parser.exception(m)
                self.terminate(m)

                return False
        else:
            return False

    def _preload_run(self):
        """ The main method which runs in the preload thread and calls other
        methods based on input to load and parse the wikipedia page.

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
                log_parser.info(f"Preload finished successfully, "
                                f"found: {self.url}")

        if self.error_msg:
            log_parser.info(f"Preload unsucessfull: {self.error_msg}")

        self.preload_running = False

    def get_wiki(self, preload=False) -> Optional[str]:
        """ Gets wikipedia page uses offline or online version.

        Parameters
        ----------
        preload: bool
            tells the method if it is part of a running preload for GUI or not

        See also
        --------
        :attr:`wiki_music.utilities.sync.SharedVars.offline_debbug`
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

        if self.wiki_downloaded:
            return self.error_msg

        self.log.debug("getting wiki")

        if SharedVars.offline_debbug:
            return self._from_disk()
        else:
            return self._from_web()

    def _from_web(self) -> Optional[str]:
        """ Guesses the right wikipedia page from innput artist and album name
        and downloads it.

        Returns
        -------
        Optional[str]
            if some error occured return string with its description
        """

        self.log.debug("from web")

        searches = [f"{self.album} ({self.band} album)",
                    f"{self.album} (album)",
                    self.album]

        try:
            for query in searches:
                self.log.debug(f"trying query: {query}")
                self.page = wiki.page(title=query, auto_suggest=True)
                summ = nc(self.page.summary)
                if nc(self.band) in summ and nc(self.album) in summ:
                    break
            else:
                self.error_msg = "Could not get wikipedia page."

        except wiki.exceptions.DisambiguationError as e:
            print("Found entries: {}\n...".format("\n".join(e.options[:3])))
            for option in e.options:
                if self.band in option:
                    print(f"\nSelecting: {option}\n")
                    self.page = wiki.page(option)
                    break
            else:
                self.error_msg = ("Couldn't select best album entry "
                                  "from wikipedia")

        except wiki.exceptions.PageError:
            try:
                self.page = wiki.page(f"{self.album} {self.band}")
            except wiki.exceptions.PageError as e:
                self.error_msg = "Album was not found on wikipedia"

        # TODO this is dangerous, can hide other types of exceptions
        except (wiki.exceptions.HTTPTimeoutError, Exception) as e:
            self.error_msg = ("Search failed probably due to "
                              "poor internet connetion.")
        else:
            self.error_msg = None
            self.wiki_downloaded = True

        

        return self.error_msg

    def _from_disk(self) -> Optional[str]:
        """ Loads wikipedia page from pickle file on disk.

        Returns
        -------
        Optional[str]
            if some error occured return string with its description
        """

        # TODO pickle probably cannot handle some complex pages
        self.log.debug(f"loading pickle file {self.url}")
        if path.isfile(self.url):
            with open(self.url, 'rb') as f:
                self.log.debug("loading ...")
                self.page = pickle.load(f)
            self.log.debug("done")
            self.error_msg = None
            self.wiki_downloaded = True
        else:
            self.error_msg = "Cannot find cached offline version of page."

        return self.error_msg

    def cook_soup(self) -> Optional[str]:
        """ Takes page downloaded from wikipedia and and parses it with use
        of bs4. Then splits the page to dictionary of sections each section
        is indexed by its name.

        Returns
        -------
        Optional[str]
            if some error occured return string with its description
        """

        if self.soup_ready:
            return self.error_msg

        # make BeautifulSoup black magic
        self.soup = bs4.BeautifulSoup(self.page.html(), features="lxml")  # type: ignore

        # split page to parts
        self.sections = collections.OrderedDict()

        # h2 mark the main haedings in document
        for h2 in self.soup.find_all("h2"):

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

            self.sections[name] = value

        # add infobox to the sections
        self.sections["infobox"] = self.soup.find(
            "table", class_="infobox vevent haudio")

        # check if the album belongs to band that was requested
        if self._check_band():
            self.soup_ready = True
            self.error_msg = None
        else:
            self.error_msg = "Album doesnt't belong to the requested band"

        return self.error_msg
