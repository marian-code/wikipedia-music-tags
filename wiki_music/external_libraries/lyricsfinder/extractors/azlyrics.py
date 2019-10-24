"""Extractor for azlyrics.com."""

import logging
import re

from ..extractor import LyricsExtractor
from ..models.lyrics import Lyrics
from ..models import exceptions

log = logging.getLogger(__name__)


class AZLyrics(LyricsExtractor):
    """Class for extracting lyrics."""

    name = "AZLyrics"
    url = "https://www.azlyrics.com/"
    display_url = "azlyrics.com"

    @classmethod
    def extract_lyrics(cls, url_data, song, artist):
        """Extract lyrics."""
        url_data.headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; "
                                          "Win64; x64; rv:59.0) "
                                          "Gecko/20100101 Firefox/59.0"}
        bs = url_data.bs

        center = bs.body.find("div",
                              {"class": "col-xs-12 col-lg-8 text-center"})

        if not center:
            # 503 Service Temporarily Unavailable
            if re.search(r"50[0-9]", bs.find("title").text):
                raise exceptions.NotAllowedError
            # if song is not present AZLyrics returns title page
            elif bs.find("title").text == "AZLyrics - Song Lyrics from A to Z":
                raise exceptions.NoLyrics
            # if we get to the album page instead of song page
            else:
                # find tracklist
                tracklist = bs.find("div", {"id", "listAlbum"})
                # find song url
                url_data.url = tracklist.find("a", text=song.title())["href"]
                # call method again
                return AZLyrics.extract_lyrics(url_data, song, artist)

        lyrics = center.find("div", {"class": None}).text

        lyrics = re.sub(r"<br>", " ", lyrics)
        lyrics = re.sub(r"<i?>\W*", "[", lyrics)
        lyrics = re.sub(r"\W*</i>", "]", lyrics)
        lyrics = re.sub(r"\&quot\;", "\"", lyrics)
        lyrics = re.sub(r"</div>", "", lyrics)

        title = center.find("h1").text.strip()[1:-8]
        artist = bs.select_one("div.lyricsh h2 b").string[:-7]
        lyrics = lyrics.strip()

        return Lyrics(title, lyrics, artist=artist)
