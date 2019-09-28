"""Extractor for genius.com."""

import logging
from datetime import datetime

from ..extractor import LyricsExtractor
from ..models.lyrics import Lyrics

log = logging.getLogger(__name__)


class Genius(LyricsExtractor):
    """Class for extracting lyrics."""

    name = "Genius"
    url = "https://genius.com/"
    display_url = "genius.com"

    @staticmethod
    def extract_lyrics(url_data, song, artist):
        """Extract lyrics."""
        bs = url_data.bs

        lyrics_window = bs.find_all("div", {"class": "lyrics"})[0]
        lyrics = lyrics_window.text.strip()

        title = bs.find("h1", attrs={"class": "header_with_cover_art-primary_info-title"}).text
        artist = bs.select_one("a.header_with_cover_art-primary_info-primary_artist").string
        date_str = bs.find(text="Release Date").parent.find_next_sibling("span").string
        release_date = datetime.strptime(date_str, "%B %d, %Y")

        return Lyrics(title, lyrics, artist=artist, release_date=release_date)
