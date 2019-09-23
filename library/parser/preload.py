import os
from time import sleep

from lazy_import import lazy_callable, lazy_module

from wiki_music.utilities import (
    SharedVars, ThreadWithTrace, for_all_methods, log_parser, module_path,
    normalize_caseless, time_methods)

nc = normalize_caseless

fuzz = lazy_callable("fuzzywuzzy.fuzz")
Lock = lazy_callable("threading.Lock")
BeautifulSoup = lazy_callable("bs4.BeautifulSoup")
wiki = lazy_module("wikipedia")
pickle = lazy_module("pickle")
sys = lazy_module("sys")
re = lazy_module("re")


# TODO doesn't work without GUI
def terminate(message: str):
    SharedVars.ask_exit = message
    SharedVars.wait_exit = True

    while SharedVars.wait_exit:
        sleep(0.05)

    if SharedVars.terminate_app:
        sys.exit()


@for_all_methods(time_methods, exclude=["Preload"])
class WikiCooker:

    def __init__(self, protected_vars=True):

        # control
        self.wiki_downloaded = False
        self.soup_ready = False
        self.preload_running = False
        self.getter_lock = Lock()
        self.error_msg = None

        self._url = None

        # pass reference of current class instance to subclass
        self.Preload.outer_instance = self

        if protected_vars:
            # variables
            self.album = ""
            self.band = ""
            self.formated_html = None
            self.info_box_html = None
            self.page = None
            self.soup = None

    class Preload:

        _preload_thread = None
        outer_instance = None

        @classmethod
        def start(cls):
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

            if cls.outer_instance.preload_running:

                log_parser.debug(f"Stoping wikipedia preload for: "
                                 f"{cls.outer_instance.album} by "
                                 f"{cls.outer_instance.band}")
                cls._preload_thread.kill()
                cls._preload_thread.join()

                cls.outer_instance.preload_running = False

    @property
    def url(self):
        if self._url is None:
            try:
                self._url = str(self.page.url)
            except AttributeError:
                self._url = os.path.join(module_path(), "output", self.album,
                                         'page.pkl')
        return self._url

    def _check_band(self) -> bool:

        try:
            for child in self.info_box_html.children:
                if child.find(href="/wiki/Album") is not None:
                    album_artist = (child
                                    .find(href="/wiki/Album")
                                    .parent.get_text())
                    break

        except AttributeError as e:
            return False
        else:
            if fuzz.token_set_ratio(nc(self.band),
               nc(album_artist)) < 90:
                b = re.sub(r"[Bb]y|[Ss]tudio album", "", album_artist).strip()
                e = (f"The Wikipedia entry for album: {self.album} belongs to "
                     f"band: {b}\nThis probably means that entry for: "
                     f"{self.album} by {self.band} does not exist.")
                print(e)
                log_parser.exception(e)
                terminate(e)

                return False
            else:
                return True  # band found on page matches input

    def _preload_run(self):

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

    def get_wiki(self, preload=False) -> str:

        # when function is called from application,
        # wait until all preloads are finished and then continue
        if not preload:
            while self.preload_running:
                sleep(0.05)

        if self.wiki_downloaded:
            return self.error_msg

        if SharedVars.offline_debbug:
            return self._from_disk()
        else:
            return self._from_web()

    def _from_web(self) -> str:

        searches = [f"{self.album} ({self.band} album)",
                    f"{self.album} (album)",
                    self.album]

        try:
            for query in searches:
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

        except (wiki.exceptions.HTTPTimeoutError, Exception) as e:
            self.error_msg = ("Search failed probably due to "
                              "poor internet connetion.")
        else:
            self.error_msg = None
            self.wiki_downloaded = True

        return self.error_msg

    def _from_disk(self) -> str:

        fname = os.path.join(module_path(), "output", self.album, 'page.pkl')
        if os.path.isfile(fname):
            with open(fname, 'rb') as infile:
                self.page = pickle.load(infile)
            self.error_msg = None
            self.wiki_downloaded = True
        else:
            self.error_msg = "Cannot find cached offline version of page."

        return self.error_msg

    def cook_soup(self) -> str:

        if self.soup_ready:
            return self.error_msg

        # make BeautifulSoup black magic
        self.soup = BeautifulSoup(self.page.html(), features="lxml")
        self.formated_html = self.soup.get_text()
        self.info_box_html = self.soup.find("table",
                                            class_="infobox vevent haudio")

        # check if the album belongs to band that was requested
        if self._check_band():
            self.soup_ready = True
            self.error_msg = None
        else:
            self.error_msg = "Album doesnt't belong to the requested band"

        return self.error_msg
