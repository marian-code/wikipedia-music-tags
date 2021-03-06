"""Holds constants that are used in parser."""

import re  # lazy loaded
from typing import Tuple, Pattern, Dict

__all__ = ["CONTENTS_IDS", "DEF_TYPES", "DELIMITERS", "COMPOSER_HEADER",
           "TO_DELETE", "UNWANTED", "NO_LYRIS", "ORDER_NUMBER", "WIKI_GENRES",
           "TIME", "PERSONNEL_SECTIONS"]

#: defines possible types of tracks that parser is able to extract
DEF_TYPES: Tuple[str, ...] = ("Instrumental", "Acoustic", "Orchestral", "Live",
                              "Piano", "Acoustic Folk Medley")
#: these tracks usually have no lyrics so no attempt to download them is made
NO_LYRIS: Tuple[str, str] = ("Instrumental", "Orchestral")
#: defines unwanted strings that will be deleted from track title, also helps
#: in extracting artists in brackets from track title
UNWANTED: Dict[str, Pattern] = {
    "artist": re.compile(r" ?feat\.?(uring)? ?|narration( by)?:? ?", flags=re.I),
    "composer": re.compile(r"lyrics( and)?,? music:? ?|music( and)?,? lyrics:? ?|music:? ?|lyrics:? ?", flags=re.I)
}
#: regex expressions that are deleted from track title
TO_DELETE: Dict[str, Pattern] = {
    "bonus_track": re.compile(r"\( ?bonus ?(track)? ?\)", flags=re.I),
    "from_album": re.compile(r"\( ?from (.*?)(;|,|\||\)) ?", flags=re.I)
}
#: regex expresion that matches number with/out dot and any muber of spaces
ORDER_NUMBER: Pattern = re.compile(r"^ *\d+\.? *")
#: tuple with section headers from which personnel are extracted
PERSONNEL_SECTIONS: Tuple[str, ...] = ("personnel", "credits", "guests")
#: regex expression that matches wikipedia genres
WIKI_GENRES: Pattern = re.compile(r"/wiki/(?!Music_genre)", flags=re.I)
#: regex expression that matches time format e.g. (12:45)
TIME: Pattern = re.compile(r"\( *\d+\:\d+ *\)")
#: strings that are are used to extract composer name
DELIMITERS: Tuple[str, ...] = ("written by", "composed by", "lyrics by",
                               "music by", "arrangements by", "vocal lines by",
                               "arranged by")
#: strings used to identify section headers in text and page contents
CONTENTS_IDS: Tuple[str, ...] = ("Track_listing", "Personnel", "Credits",
                                 "References")
#: table headers that are used to assign personnel to composers or to artists
#: list
COMPOSER_HEADER: Tuple[str, ...] = ("lyrics", "text", "music", "compose")
