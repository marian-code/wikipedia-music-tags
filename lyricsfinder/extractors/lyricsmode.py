"""Extractor for lyricsmode.com."""

import logging

from ..extractor import LyricsExtractor
from ..models.lyrics import Lyrics

log = logging.getLogger(__name__)


class Lyricsmode(LyricsExtractor):
    """Class for extracting lyrics."""

    name = "Lyricsmode"
    url = "http://www.lyricsmode.com/"
    display_url = "lyricsmode.com"

    @classmethod
    def extract_lyrics(cls, url_data, song, artist):
        """Extract lyrics."""
        bs = url_data.bs
        lyrics_window = bs.find_all("p", {"id": "lyrics_text", "class": "ui-annotatable"})[0]
        lyrics = lyrics_window.text

        title = bs.find("h1", attrs={"class": "song_name fs32"}).text[:-7]

        return Lyrics(title, lyrics)
