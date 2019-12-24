"""Constants used by whole :mod:`wiki_music` module."""
from typing import Tuple

__all__ = ["TAGS", "EXTENDED_TAGS", "STR_TAGS", "LIST_TAGS"]

#: enumeration of tags that we are able to read and write to music files
TAGS: Tuple[str, ...] = ("ALBUM", "ALBUMARTIST", "ARTIST", "COMPOSER",
                         "COVERART", "DATE", "DISCNUMBER", "GENRE", "LYRICS",
                         "TITLE", "TRACKNUMBER")
#: tags extended with file path and track type which is not directly
#: writen into file tags
EXTENDED_TAGS: Tuple[str, ...] = TAGS + ("FILE", "TYPE")
#: marks tags which have separate entry fields in gui and are not displayed
#: in tracklist table
STR_TAGS: Tuple[str, ...] = ("GENRE", "ALBUM", "ALBUMARTIST", "DATE")
#: marks tags that consist of list of values for each entry
LIST_TAGS: Tuple[str, ...] = ("ARTIST", "COMPOSER")
