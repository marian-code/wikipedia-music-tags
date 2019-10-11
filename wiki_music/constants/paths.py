""" This module defines all path constants that are used in package. """

from wiki_music.package_setup import module_path
from os.path import join

__all__ = ["ROOT_DIR", "DIR_FILE", "LOG_DIR", "MP3_TAG", "OUTPUT_FOLDER",
           "OFFLINE_DEBUG_IMAGES", "FILES_DIR"]

#: toplevel directory containing whole package
ROOT_DIR: str = module_path()
#: file containing record of last openede directory in gui
DIR_FILE: str = join(ROOT_DIR, "data", "last_opened.txt")
#: directory containing logs, profiling log and dir with parser output
LOG_DIR: str = join(ROOT_DIR, "logs")
#: path to Mp3tag executable
MP3_TAG: str = r"C:\Program Files (x86)\Mp3tag\Mp3tag.exe"
#: folder containing human readable text output, of processed wiki page
#: and also pickled version of wikipedia.WikipediaPage
OUTPUT_FOLDER: str = join(LOG_DIR, "output")
#: directory containing images used for offline debugging of image search
OFFLINE_DEBUG_IMAGES: str = join(ROOT_DIR, "..", "tests", "offline_debug")
#: directory containing package files like icons etc.
FILES_DIR: str = join(ROOT_DIR, "files")