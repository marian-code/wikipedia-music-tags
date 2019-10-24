"""Extractor for lyrical-nonsense.com."""

import logging

from .. import utils
from ..extractor import LyricsExtractor
from ..models.lyrics import Lyrics
from ..utils import UrlData

log = logging.getLogger(__name__)


class LyricalNonsense(LyricsExtractor):
    """Class for extracting lyrics."""

    name = "Lyrical Nonsense"
    url = "http://www.lyrical-nonsense.com/"
    display_url = "lyrical-nonsense.com"

    @classmethod
    def extract_lyrics(cls, url_data: UrlData, song, artist) -> Lyrics:
        """Extract lyrics."""
        bs = url_data.bs
        title = bs.select_one("div.titletext2new h3").text
        artist = bs.select_one("div.artisttext1new h2 a").text

        lyrics_window = (bs.select_one("div#Romaji div.olyrictext") or
                         bs.select_one("div#Lyrics div.olyrictext"))
        lyrics = utils.clean_lyrics(lyrics_window.text)

        return Lyrics(title, lyrics, artist=artist)
