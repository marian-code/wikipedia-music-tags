import logging
import re
from typing import Pattern

from lyricsfinder import Lyrics
from lyricsfinder.extractor import LyricsExtractor
from lyricsfinder.utils import Request

log = logging.getLogger(__name__)

RE_SPLIT_ARTIST_TITLE: Pattern = re.compile(r"(?P<artist>.+?)\s+–\s+(?P<title>.+) (?:lyrics)?")


class Lyricsmode(LyricsExtractor):
    name = "Lyricsmode"
    url = "http://www.lyricsmode.com/"
    display_url = "lyricsmode.com"

    @classmethod
    async def extract_lyrics(cls, request: Request) -> Lyrics:
        bs = await request.bs
        lyrics_window = bs.find_all("p", {"id": "lyrics_text", "class": "ui-annotatable"})[0]
        lyrics = lyrics_window.text.strip()

        heading = bs.find("h1", attrs={"class": "song_name fs32"}).text.strip()

        match = RE_SPLIT_ARTIST_TITLE.search(heading)

        artist = match.group("artist")
        title = match.group("title")

        return Lyrics(title, lyrics, artist)
