"""Searches lyrics."""

import logging

from .lyrics import LyricsManager
from .models import *

logging.getLogger(__name__)

extract_lyrics = LyricsManager.extract_lyrics
search_lyrics = LyricsManager.search_lyrics
