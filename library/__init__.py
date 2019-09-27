from .ID3_tags import write_tags, read_tags, TAGS
from .parser import WikipediaRunner
from .lyrics import save_lyrics

__all__ = ["WikipediaRunner", "write_tags", "read_tags", "save_lyrics", "TAGS"]
