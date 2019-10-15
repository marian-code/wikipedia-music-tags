"""Module which does the backgroung heavy lifting. Can obtain and parse
Wikipedia page, search and download lyrics, read and write music tags """

import logging

from .lyrics import save_lyrics
from .parser import WikipediaRunner
from .tags_io import read_tags, write_tags

__all__ = ["WikipediaRunner", "write_tags", "read_tags", "save_lyrics"]

logging.getLogger(__name__)
