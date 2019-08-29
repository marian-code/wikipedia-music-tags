import sys
from .wiki_parse import WikipediaParser
from .ID3_tags import write_tags, read_tags

_version = sys.version_info
if _version.major == 3:
    #if _version.minor == 6:
    #    from .lyrics import save_lyrics
    if _version.minor == 7:
        #from .lyrics_aio import save_lyrics
        from .lyrics import save_lyrics
else:
    raise NotImplementedError("Wikimusic only supports python "
                              "versions=(3.6, 3.7)")

__all__ = ["WikipediaParser", "write_tags", "read_tags", "save_lyrics"]
