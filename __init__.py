import package_setup
import os
from sys import argv

ROOT_DIR = package_setup.module_path()
DIR_FILE = os.path.join(ROOT_DIR, "data", "last_opened.txt")
MP3_TAG = r"C:\Program Files (x86)\Mp3tag\Mp3tag.exe"
TAGS = ("ALBUM","ALBUMARTIST", "ARTIST", "COMPOSER", "DATE", "DISCNUMBER",
        "GENRE", "LYRICS", "TITLE", "TRACKNUMBER")
GUI_HEADERS = ("TRACKNUMBER", "TITLE", "TYPE", "ARTIST", "COMPOSER",
               "DISCNUMBER", "LYRICS", "FILE")
EXTENDED_TAGS = TAGS + ("FILE", "TYPE")
STR_TAGS = ["GENRE", "ALBUM", "ALBUMARTIST", "DATE"]

if "gui" in argv[0]:
    GUI_RUNNING = True
else:
    GUI_RUNNING = False

from library import WikipediaParser  # noqa E402
parser = WikipediaParser()
