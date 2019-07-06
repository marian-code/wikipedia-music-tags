import logging

from .__info__ import *
from .manager import LyricsManager
from .models import *

log = logging.getLogger(__name__)

extract_lyrics = LyricsManager.extract_lyrics
search_lyrics = LyricsManager.search_lyrics

LyricsManager.setup()
log.debug("LyricsFinder loaded")
