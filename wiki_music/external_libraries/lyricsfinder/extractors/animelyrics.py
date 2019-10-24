"""Extractor for animelyrics.com."""

import logging
import re

import requests

from ..extractor import LyricsExtractor
from ..models import exceptions
from ..models.lyrics import Lyrics

log = logging.getLogger(__name__)

ARTIST_MATCHER = re.compile(r"^Performed by ([\w' ]+)\b", re.MULTILINE)


class Animelyrics(LyricsExtractor):
    """Class for extracting lyrics."""

    name = "Animelyrics"
    url = "http://www.animelyrics.com/"
    display_url = "animelyrics.com"

    @classmethod
    def extract_lyrics(cls, url_data, song, artist):
        """Extract lyrics."""
        bs = url_data.bs
        title = bs.select_one("div ~ h1").string
        artist = bs.find(text=ARTIST_MATCHER)
        artist = ARTIST_MATCHER.match(artist).group(1)

        lyrics_window = bs.find("table", attrs={"cellspacing": "0",
                                                "border": "0"})

        if lyrics_window:  # shit's been translated
            log.info("these lyrics have been translated... sighs...")

            lines = lyrics_window.find_all("tr")
            lyrics = ""
            for line in lines:
                p = line.td
                if p:
                    p.span.dt.replace_with("")
                    for br in p.span.find_all("br"):
                        br.replace_with("\n")

                    lyrics += p.span.text
            lyrics = lyrics.strip()
        else:
            raw = requests.get(re.sub(r"\.html?", ".txt", url_data.url),
                               allow_redirects=False)
            content = raw.text.strip()
            match = re.search(r"-{10,}(.+?)-{10,}", content, flags=re.DOTALL)
            if match:
                lyrics = match.group(1).strip()
            else:
                raise exceptions.NoLyrics

        lyrics = lyrics.replace("\xa0", " ").replace("\r", "")

        return Lyrics(title, lyrics, artist=artist)
