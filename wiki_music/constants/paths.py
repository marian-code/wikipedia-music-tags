"""Module defininng all path constants that are used in package."""

import sys
from pathlib import Path

from appdirs import user_data_dir, user_log_dir

__all__ = ["ROOT_DIR", "LOG_DIR", "OUTPUT_FOLDER", "OFFLINE_DEBUG_IMAGES",
           "FILES_DIR", "GOOGLE_API_URL", "API_KEY_FILE", "module_path",
           "SETTINGS_YML"]


def _dir_writable(dir_name: Path) -> bool:
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
    test_write = dir_name / "TEST_WRITE"

    try:
        f = test_write.open("w")
    except IOError:
        return False
    else:
        f.close()
        test_write.unlink()
        return True


def module_path() -> Path:
    """Outputs root path of the module.

    Acounts for changes in path when app is frozen.

    Returns
    -------
    str
        string with root module path

    See also
    --------
    :func:`we_are_frozen`
    """
    if hasattr(sys, "frozen"):
        return Path(sys.executable).resolve().parent
    else:
        return (Path(__file__) / "..").resolve().parent


#: toplevel directory for file saving
ROOT_DIR: Path = module_path()
#: directory containing logs, profiling log and dir with parser output
LOG_DIR: Path = Path(ROOT_DIR, "logs")
#: directory containing images used for offline debugging of image search
OFFLINE_DEBUG_IMAGES: Path = Path(ROOT_DIR, "..", "tests",
                                  "offline_debug").resolve()
#: directory containing package files like icons etc.
FILES_DIR: Path = Path(ROOT_DIR, "files")

# get platform specific data dirs if root package dir is not writable
if not _dir_writable(ROOT_DIR):
    ROOT_DIR = Path(user_data_dir(appname="wiki_music", appauthor=None))
    LOG_DIR = Path(user_log_dir(appname="wiki_music", appauthor=None))
    OFFLINE_DEBUG_IMAGES = Path("")

    ROOT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

#: folder containing human readable text output, of processed wiki page
#: and also pickled version of wikipedia.WikipediaPage
OUTPUT_FOLDER: Path = Path(LOG_DIR, "output")
#: Google API key file
API_KEY_FILE: Path = Path(ROOT_DIR, "files", "google_api_key.txt")
#: Google API url
GOOGLE_API_URL: str = ("https://console.developers.google.com/projectselector/"
                       "apis/library/customsearch.googleapis.com")
#: dictionary with package settings
SETTINGS_YML: Path = Path(ROOT_DIR, "files", "settings.yml")
