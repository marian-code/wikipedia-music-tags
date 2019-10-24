"""Extractor for Musixmatch.com."""

import logging
import re
from datetime import datetime

from requests.exceptions import HTTPError

from ..extractor import LyricsExtractor
from ..models import exceptions
from ..models.lyrics import Lyrics

log = logging.getLogger(__name__)

ORDINAL_MATCHER = re.compile(r"(\d{1,2})(st|nd|rd|th)")


class MusixMatch(LyricsExtractor):
    """Class for extracting lyrics."""

    name = "MusixMatch"
    url = "https://www.musixmatch.com/"
    display_url = "musixmatch.com"

    @classmethod
    def extract_lyrics(cls, url_data, song, artist):
        """Extract lyrics."""
        url_data.headers = {"user-agent": "Mozilla/5.0 (Windows NT 6.1; "
                                          "WOW64; rv:40.0) Gecko/20100101 "
                                          "Firefox/40.1"}
        try:
            url_data.resp.raise_for_status()
        except HTTPError:
            raise exceptions.NotAllowedError
        bs = url_data.bs

        if bs.find_all("div", attrs={"class": "mxm-empty-state",
                                     "data-reactid": "87"}):
            raise exceptions.NoLyrics

        lyrics_frame = bs.find_all("div", {"class": "mxm-lyrics"})

        if not lyrics_frame:
            raise exceptions.NoLyrics

        lyrics_window = lyrics_frame[0].find_all("div", {"class":
                                                         "mxm-lyrics"})

        if not lyrics_window:
            raise exceptions.NoLyrics

        lyrics_window = lyrics_window[0].span

        for garbage in bs.find_all("script"):
            garbage.replace_with(2 * "\n")

        lyrics = lyrics_window.text
        title = bs.find("h1", attrs={"class": "mxm-track-title__track"}).contents[-1].strip()
        artist = bs.select_one("a.mxm-track-title__artist").string
        release_date = None
        date_str = bs.select_one("div.mxm-track-footer__album "
                                 "h3.mui-cell__subtitle")
        if date_str:
            date_str = ORDINAL_MATCHER.sub(lambda m: m.group(1).zfill(2),
                                           date_str.string)
            release_date = datetime.strptime(date_str, "%b %d %Y")

        return Lyrics(title, lyrics, artist=artist, release_date=release_date)
