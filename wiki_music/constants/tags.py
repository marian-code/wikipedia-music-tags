from typing import Tuple

__all__ = ["TAGS", "GUI_HEADERS", "EXTENDED_TAGS", "STR_TAGS"]

#: enumeration of tags that we are able to read and write to music files
TAGS: Tuple[str, ...] = ("ALBUM", "ALBUMARTIST", "ARTIST", "COMPOSER",
                         "COVERART", "DATE", "DISCNUMBER", "GENRE", "LYRICS",
                         "TITLE", "TRACKNUMBER")
#: defines headers for tracklist table in GUI
GUI_HEADERS: Tuple[str, ...] = ("TRACKNUMBER", "TITLE", "TYPE", "ARTIST",
                                "COMPOSER", "DISCNUMBER", "LYRICS", "FILE")
#: tags extended with file path and track type which is not directly
#: writen into file tags
EXTENDED_TAGS: Tuple[str, ...] = TAGS + ("FILE", "TYPE")
#: marks tags which have separate entry fields in gui and are not displayed
#: in tracklist table
STR_TAGS: Tuple[str, ...] = ("GENRE", "ALBUM", "ALBUMARTIST", "DATE")
