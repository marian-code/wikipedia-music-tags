""" Module which does the backgroung heavy lifting. Can obtain and parse
Wikipedia page, search and download lyrics, read and write music tags """

from .ID3_tags import write_tags, read_tags
from .parser import WikipediaRunner
from .lyrics import save_lyrics

__all__ = ["WikipediaRunner", "write_tags", "read_tags", "save_lyrics"]
