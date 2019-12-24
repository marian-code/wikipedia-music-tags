"""Store classes that retrieve data."""

import logging
import sys
import webbrowser  # lazy loaded
from pathlib import Path
from threading import RLock, Thread
from time import sleep
from typing import TYPE_CHECKING, Optional, Type, Union

from wiki_music.constants import (API_KEY_FILE, API_KEY_MESSAGE,
                                  GOOGLE_API_URL, NLTK_DOWNLOAD_MESSAGE)

from .parser_utils import ThreadPool
from .sync import Action, YmlSettings
from .utils import MultiLog, limited_input

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    import nltk
    Nltk = Type[nltk]

__all__ = ["GoogleApiKey", "NLTK"]


class GoogleApiKey:
    """Class that reads and stores google API key.

    If the key is not found, show prompt to download.
    """

    _log: MultiLog = MultiLog(log)
    _api_key: Optional[str] = None

    @classmethod
    def value(cls, GUI: bool) -> Optional[str]:
        """Reads google api key needed by lyricsfinder from file.

        Returns
        -------
        Optional[str]
            google API key
        """
        if not cls._api_key:
            # load google api key for lyrics search
            try:
                cls._api_key = API_KEY_FILE.read_text("r").strip()
            except Exception:
                cls._log.debug("api key not present in file")
                if YmlSettings.read("api_key_dont_bother", False):
                    cls._log.debug("will try to obtain api key from internet")
                    cls._api_key = cls.get(GUI)
                else:
                    cls._log.debug("don't bother with api key in settings")
                    cls._api_key = None

        return cls._api_key

    @classmethod
    def get(cls, GUI: bool, in_thread: bool = True) -> Optional[str]:
        """Prompt user to input google API key.

        Asks user through GUI or CLI if he wants to get Google API key. Three
        options are available: yes, no and don't bother me again.

        Parameters
        ----------
        GUI: bool
            if we are running in GUI or CLI mode
        in_thread: bool
            when running from GUI create a separate thread,
            so GUI is not halted

        Returns
        -------
        Optional[str]
            key in string format or none if key was not retrieved

        Note
        ----
        If the method is called with in_thread=True then a new thread is
        spawned and download runs in it. This is for use in GUI so the main
        thread is not halted.
        """
        if in_thread:
            cls._log.debug("api key download started from GUI, "
                           "spawning new background thread")
            Thread(target=cls.get, args=(GUI, False),
                   name="API-key-getter", daemon=True).start()
            return None

        # ask user if he wants to get the google API key
        cls._log.debug("show api key prompt")
        if GUI:
            a = Action("api_key", API_KEY_MESSAGE.replace("\n", " "))
            inpt = a.response
        else:
            print(API_KEY_MESSAGE)
            inpt = limited_input(dont_bother=True)

        if inpt == "d":
            cls._log.debug("answer is don't bother")
            YmlSettings.write("api_key_dont_bother", True)
            return None
        elif inpt:
            cls._log.debug("opening browser page")
            # open page in browser
            webbrowser.open_new_tab(GOOGLE_API_URL)

            cls._log.debug("waiting for api key input")
            if GUI:
                api_key = Action("load_api_key").response
            else:
                # wait for key input
                api_key = str(input("Paste the key here: ")).strip()

            cls._log.debug("saving api key file to file")
            # delete don't bother setting
            YmlSettings.delete("api_key_dont_bother")
            # write key to file
            API_KEY_FILE.write_text(api_key)

            return api_key
        else:
            return None


class _NltkMeta(type):
    """Metaclass which defines thread safe nltk property for NLTK class.

    See Also
    --------
    :class:`NLTK`

    References
    ----------
    https://stackoverflow.com/questions/128573/using-property-on-classmethods
    """

    _lock: RLock = RLock()
    _nltk: "Nltk"

    @property
    def nltk(cls) -> "Nltk":
        """Thread safe property which holds reference to nltk lib.

        :type: nltk
        """
        with cls._lock:
            return cls._nltk


class NLTK(metaclass=_NltkMeta):
    """A thread safe nltk importer. Checks if nltk data is downloaded.

    Will make other threads wait if they want to access nltk
    until it is imported. If the data is not downloaded it will as to download
    it.

    Attributes
    ----------
    nltk: nltk
        thread safe attribute is provided by metaclass
    """

    _import_running: bool = False
    _GUI: bool = False
    _log: MultiLog = MultiLog(log)

    @classmethod
    def run_import(cls, GUI: bool = False, delay: float = 1):
        """Import nltk in separate thread and assign it to class attribute.

        Parameters
        ----------
        GUI: bool
            tells if we are running in GUI mode
        delay: float
            delays the start of import by specified amount of seconds
        """
        def imp(delay: float):

            if delay:
                sleep(delay)

            with cls._lock:
                cls._log.debug("import nltk")
                try:
                    import nltk
                    cls._nltk = nltk
                except ImportError as e:
                    cls._log.debug(f"failed to import nltk: {e}")
                else:
                    cls._log.debug("import nltk done, checking data...")
                    cls._check_nltk_data()

        cls._GUI = GUI

        if not cls._import_running:

            cls._import_running = True
            # load NLTK in separate thread
            Thread(target=imp, args=(delay, ), name="ImportNLTK").start()
        else:
            cls._log.debug("nltk import already running")

    @classmethod
    def _check_nltk_data(cls):

        # check if user rejected download previously
        if YmlSettings.read("nltk_dont_bother", False):
            cls._log.debug("do not bother with nltk data")
            return

        # try to read package defined path
        path = YmlSettings.read("nltk_data_path", "")
        if path:
            cls.nltk.data.path.append(path)

        # check if any of the paths exists
        for p in cls._nltk.data.path:
            if Path(p).exists():
                nltk_downloaded = True
                cls._log.debug("NLTK data present")
                break
        else:
            nltk_downloaded = False

        # if none exists ask user for download
        if not nltk_downloaded:

            if cls._GUI:
                a = Action("nltk_data",
                           NLTK_DOWNLOAD_MESSAGE.replace("\n", " "))
                inpt = a.response
            else:
                print(NLTK_DOWNLOAD_MESSAGE)
                inpt = limited_input(dont_bother=True)

            if inpt == "d":
                YmlSettings.write("nltk_dont_bother", True)
            elif inpt:
                cls.download_data()
            else:
                pass

    @classmethod
    def download_data(cls, in_thread: bool = False):
        """Get download path from GUI or CLI, then download data there.

        Parameters
        ----------
        in_thread: bool
            when running from GUI create a separate thread,
            so GUI is not halted

        Note
        ----
        If the method is called with in_thread=True then a new thread is
        spawned and download runs in it. This is for use in GUI so the main
        thread is not halted.
        """
        if in_thread:
            Thread(target=cls.download_data, args=(False,),
                   name="NLTK-downloader", daemon=True).start()
            return

        NLTK_DATA = cls._get_default_path()

        # get nltk path from CLI or GUI
        if cls._GUI:
            a = Action("download_nltk_data", str(NLTK_DATA))
            NLTK_DATA = Path(a.response)
        else:
            while True:
                inpt = str(input(f"({NLTK_DATA}[ENTER]): ")).strip()

                if not inpt and NLTK_DATA:
                    break
                else:
                    NLTK_DATA = Path(inpt)

        # check if the path is valid
        try:
            NLTK_DATA.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            cls._log.warning("Invalid path, a file with this name already "
                             "exists.")
            cls.download_data()
        except PermissionError:
            cls._log.warning("Invalid path, cannot write in this directory.")
            cls.download_data()

        # append path to defaults and save to settings so app may find it
        cls._nltk.data.path.append(NLTK_DATA)
        YmlSettings.write("nltk_data_path", str(NLTK_DATA))

        # delete don't bother setting
        YmlSettings.delete("nltk_dont_bother")

        # download data
        cls._log.info("Downloading nltk data")

        datas = ("words", "stopwords", "maxent_ne_chunker",
                 "averaged_perceptron_tagger", "punkt")

        ThreadPool(cls._nltk.download, [(d, NLTK_DATA) for d in datas]).run()

        # clear unnecessary files
        cls._download_postprocess(NLTK_DATA)

    @classmethod
    def _get_default_path(cls) -> Path:
        """Get platform specific nltk default data path.

        Raises
        ------
        Warn
            if running on unsupprted platform

        Returns
        -------
        Path
            default nltk data path for current platform
        """
        if sys.platform.startswith("win32"):
            return Path("C:/nltk_data")
        elif sys.platform.startswith("linux"):
            return Path("/usr/share/nltk_data")
        elif sys.platform.startswith("darwin"):
            return Path("/usr/local/share/nltk_data")
        else:
            msg = "Usupported platform! you must specify path manually."
            cls._log.warning(msg)
            return ""

    @classmethod
    def _download_postprocess(cls, path: Path):

        cls._log.info("Deleting unnecessary files...")

        for p in path.rglob("*"):
            if p.name.endswith((".zip", ".pickle", "README")):
                # avoid deletinng some files
                if ("english" not in p.name and
                    "_perceptron_tagger.p" not in p.name):  # noqa E129
                    p.unlink()

        cls._log.info("Done")
