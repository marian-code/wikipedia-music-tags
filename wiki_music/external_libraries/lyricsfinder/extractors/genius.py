"""Extractor for genius.com."""

import logging
from datetime import datetime

from ..extractor import LyricsExtractor
from ..models.lyrics import Lyrics
from ..models import exceptions

log = logging.getLogger(__name__)


class Genius(LyricsExtractor):
    """Class for extracting lyrics."""

    name = "Genius"
    url = "https://genius.com/"
    display_url = "genius.com"

    @classmethod
    def extract_lyrics(cls, url_data, song, artist):
        """Extract lyrics."""
        bs = url_data.bs

        try:
            lyrics_window = bs.find_all("div", {"class": "lyrics"})[0]
        except IndexError:
            # Oops! Page not found message
            if bs.find("h1", {"class": "render_404-headline"}):
                raise exceptions.NoLyrics
            # if album name == song name and we end up in album page
            else:
                # find tracklist
                tracklist = bs.find(
                    "div", {"class": "track_listing track_listing--columns"})
                # extract new url
                url_data.url = tracklist.find("a", {"title": song})["href"]
                # call extraction method again
                return Genius.extract_lyrics(url_data, song, artist)

        lyrics = lyrics_window.text.strip()

        title = bs.find("h1", attrs={"class":
                                     "header_with_cover_art-"
                                     "primary_info-title"}).text
        artist = bs.select_one(
            "a.header_with_cover_art-primary_info-primary_artist").string
        try:
            date_str = bs.find(text="Release Date")
            date_str = date_str.parent.find_next_sibling("span").string
        except AttributeError:
            date_str = "January 1, 2000"
        release_date = datetime.strptime(date_str, "%B %d, %Y")

        return Lyrics(title, lyrics, artist=artist, release_date=release_date)
