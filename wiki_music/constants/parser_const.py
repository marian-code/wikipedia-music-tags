from typing import Tuple

__all__ = ["CONTENTS_IDS", "DEF_TYPES", "DELIMITERS", "HEADER_CATEGORY",
           "TO_DELETE", "UNWANTED"]

DEF_TYPES: Tuple[str, ...] = ("Instrumental", "Acoustic", "Acoustic Version",
                              "Orchestral", "Live", "Piano Version",
                              "Acoustic Folk Medley")
UNWANTED: Tuple[str, ...] = ("featuring", "feat.", "feat", "narration by",
                             "narration")
TO_DELETE: Tuple[str, ...] = ("bonus track", "bonus")
DELIMITERS: Tuple[str, ...] = ("written by", "composed by", "lyrics by",
                               "music by", "arrangements by", "vocal lines by")
CONTENTS_IDS: Tuple[str, ...] = ("Track_listing", "Personnel", "Credits",
                                 "References")
HEADER_CATEGORY: Tuple[str, ...] = ("lyrics", "text", "music", "compose")
