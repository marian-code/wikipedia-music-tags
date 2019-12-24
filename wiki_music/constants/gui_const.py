"""Constants used by :mod:`wiki_music.gui_lib`."""
from typing import Tuple

from .paths import module_path

__all__ = ["GUI_HEADERS", "ASPECT_RATIOS", "SPLIT_HEADERS", "MAIN_WINDOW_UI",
           "COVER_ART_SEARCH_UI", "COVER_ART_EDIT_UI", "API_KEY_MESSAGE",
           "NLTK_DOWNLOAD_MESSAGE"]

#: defines headers for tracklist table in GUI
GUI_HEADERS: Tuple[str, ...] = ("TRACKNUMBER", "TITLE", "TYPE", "ARTIST",
                                "COMPOSER", "DISCNUMBER", "LYRICS", "FILE")
#: tuple of permited aspect ratios for cover art cropping
ASPECT_RATIOS: Tuple[str, ...] = ("Free", "Preserve", "16:9", "4:3", "3:2",
                                  "1:1")
#: define table columns that should be splited because they are list types in
#: parser
SPLIT_HEADERS: Tuple[str, ...] = ("TYPE", "ARTIST", "COMPOSER")
#: path to Main window Ui file
MAIN_WINDOW_UI: str = str(module_path() / "ui" / "MainWindow.ui")
#: path to Cover art search dialog Ui file
COVER_ART_SEARCH_UI: str = str(module_path() / "ui" / "CoverArtSearch.ui")
#: path to Cover art editor Ui file
COVER_ART_EDIT_UI: str = str(module_path() / "ui" / "CoverArtEdit.ui")
#: description text for google api key getting
API_KEY_MESSAGE: str = (
    "To enhance lyrics searching capabilities Wiki Music uses google\n"
    "custom search. To use it you have to get your own API key. It is\n"
    "recomended but not necessary. You will be redirected to page in\n"
    "browser where you will log in with your google account and create\n"
    "a new project. After that go to the API section, search for\n"
    "Custom Search API and enable it. Finally go to credentials\n"
    "section and create new API key.\n"
)
#: message to show before nltk download
NLTK_DOWNLOAD_MESSAGE: str = (
    "\nThe package requires downloading of NLTK data to function to its\n"
    "full potential. It will work without the data, but the extraction\n"
    "will not be as effective. Final size is ~32MB.\n"
)
