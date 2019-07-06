import logging
from datetime import datetime

from lyricsfinder import Lyrics, NoLyrics
from lyricsfinder.extractor import LyricsExtractor
from lyricsfinder.utils import Request

log = logging.getLogger(__name__)


class Genius(LyricsExtractor):
    name = "Genius"
    url = "https://genius.com/"
    display_url = "genius.com"

    @classmethod
    async def extract_lyrics(cls, request: Request) -> Lyrics:
        bs = await request.bs

        lyrics_window = bs.find_all("div", {"class": "lyrics"})
        if not lyrics_window:
            raise NoLyrics

        lyrics_window = lyrics_window[0]
        lyrics = lyrics_window.text.strip()

        title = bs.find("h1", attrs={"class": "header_with_cover_art-primary_info-title"}).text
        artist = bs.select_one("a.header_with_cover_art-primary_info-primary_artist").string
        release_date = None
        date_str = bs.find(text="Release Date")
        if date_str:
            date_str = date_str.parent.find_next_sibling("span").string
            release_date = datetime.strptime(date_str, "%B %d, %Y")

        return Lyrics(title, lyrics, artist=artist, release_date=release_date)
