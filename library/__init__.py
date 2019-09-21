from .ID3_tags import write_tags, read_tags, TAGS
from .parser.process_page import WikipediaParser
from .lyrics import save_lyrics

__all__ = ["WikipediaParser", "write_tags", "read_tags", "save_lyrics", "TAGS"]
