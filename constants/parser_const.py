__all__ = ["CONTENTS_IDS", "DEF_TYPES", "DELIMITERS", "HEADER_CATEGORY",
           "TO_DELETE", "UNWANTED"]

DEF_TYPES = ("Instrumental", "Acoustic", "Acoustic Version", "Orchestral",
             "Live", "Piano Version", "Acoustic Folk Medley")
UNWANTED = ("featuring", "feat.", "feat", "narration by", "narration")
TO_DELETE = ("bonus track", "bonus")
DELIMITERS = ("written by", "composed by", "lyrics by", "music by",
              "arrangements by", "vocal lines by")
CONTENTS_IDS = ("Track_listing", "Personnel", "Credits", "References")
HEADER_CATEGORY = ("lyrics", "text", "music", "compose")
