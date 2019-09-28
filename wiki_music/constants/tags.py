from typing import Tuple

__all__ = ["TAGS", "GUI_HEADERS", "EXTENDED_TAGS", "STR_TAGS"]

TAGS: Tuple[str, ...] = ("ALBUM", "ALBUMARTIST", "ARTIST", "COMPOSER",
                         "COVERART", "DATE", "DISCNUMBER", "GENRE", "LYRICS",
                         "TITLE", "TRACKNUMBER")
GUI_HEADERS: Tuple[str, ...] = ("TRACKNUMBER", "TITLE", "TYPE", "ARTIST",
                                "COMPOSER", "DISCNUMBER", "LYRICS", "FILE")
EXTENDED_TAGS: Tuple[str, ...] = TAGS + ("FILE", "TYPE")
STR_TAGS: Tuple[str, ...] = ("GENRE", "ALBUM", "ALBUMARTIST", "DATE")
