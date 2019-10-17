"""This module defines all path constants that are used in package."""

import sys
from os import path, remove, makedirs
from appdirs import user_data_dir, user_log_dir


__all__ = ["ROOT_DIR", "DIR_FILE", "LOG_DIR", "MP3_TAG", "OUTPUT_FOLDER",
           "OFFLINE_DEBUG_IMAGES", "FILES_DIR", "DONT_BOTHER_API",
           "GOOGLE_API_URL", "API_KEY_FILE", "module_path"]


def _dir_writable(dir_name: str) -> bool:
    """Test if inpu directory is writable.

    Parameters
    ----------
    dir_name: str
        path to tested directory

    Returns
    -------
    bool
        true if files can be  writen to directory
    """

    test_write = path.join(dir_name, "TEST_WRITE")

    try:
        f = open(test_write, "w")
    except IOError:
        return False
    else:
        f.close()
        remove(test_write)
        return True


def module_path() -> str:
    """Outputs root path of the module. Acounts for changes in path when
    app is frozen.

    Returns
    -------
    str
        string with root module path

    See also
    --------
    :func:`we_are_frozen`
    """

    if hasattr(sys, "frozen"):
        return path.abspath(path.dirname(sys.executable))
    else:
        return path.abspath(path.join(path.dirname(__file__), ".."))


#: toplevel directory for file saving
ROOT_DIR: str = module_path()
#: directory containing logs, profiling log and dir with parser output
LOG_DIR: str = path.join(ROOT_DIR, "logs")
#: directory containing images used for offline debugging of image search
OFFLINE_DEBUG_IMAGES: str = path.join(ROOT_DIR, "..", "tests", "offline_debug")
#: directory containing package files like icons etc.
FILES_DIR: str = path.join(ROOT_DIR, "files")
#: path to Mp3tag executable
MP3_TAG: str = r"C:\Program Files (x86)\Mp3tag\Mp3tag.exe"

# get platform specific data dirs if root package dir is not writable
if not _dir_writable(ROOT_DIR):
    ROOT_DIR = user_data_dir(appname="wiki_music", appauthor=None)
    LOG_DIR = user_log_dir(appname="wiki_music", appauthor=None)
    OFFLINE_DEBUG_IMAGES = ""

#: file containing record of last openede directory in gui
DIR_FILE: str = path.join(ROOT_DIR, "data", "last_opened.txt")
#: folder containing human readable text output, of processed wiki page
#: and also pickled version of wikipedia.WikipediaPage
OUTPUT_FOLDER: str = path.join(LOG_DIR, "output")
#: Google API key file
API_KEY_FILE: str = path.join(ROOT_DIR, "files", "google_api_key.txt")
#: file that says if user should be asked to get google API key
DONT_BOTHER_API: str = path.join(ROOT_DIR, "files", "DONT_BOTHER_API")
#: Google API url
GOOGLE_API_URL: str = ("https://console.developers.google.com/projectselector/"
                       "apis/library/customsearch.googleapis.com")

