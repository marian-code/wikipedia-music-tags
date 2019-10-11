""" Constants used by :mod:`wiki_music.gui_lib` """
from os import path
from typing import Tuple

from .paths import ROOT_DIR

__all__ = ["GUI_HEADERS", "ASPECT_RATIOS", "SPLIT_HEADERS", "MAIN_WINDOW_UI",
           "COVER_ART_SEARCH_UI", "COVER_ART_EDIT_UI"]

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
MAIN_WINDOW_UI: str = path.join(ROOT_DIR, "ui", "MainWindow.ui")
#: path to Cover art search dialog Ui file
COVER_ART_SEARCH_UI: str = path.join(ROOT_DIR, "ui", "CoverArtSearch.ui")
#: path to Cover art editor Ui file
COVER_ART_EDIT_UI: str = path.join(ROOT_DIR, "ui", "CoverArtEdit.ui")
