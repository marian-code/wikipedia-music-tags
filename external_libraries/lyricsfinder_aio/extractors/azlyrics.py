import logging
import re

from lyricsfinder import Lyrics, NoLyrics
from lyricsfinder.extractor import LyricsExtractor
from lyricsfinder.utils import Request

log = logging.getLogger(__name__)


class AZLyrics(LyricsExtractor):
    name = "AZLyrics"
    url = "https://www.azlyrics.com/"
    display_url = "azlyrics.com"

    @classmethod
    async def extract_lyrics(cls, request: Request) -> Lyrics:
        request.headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0"}
        bs = await request.bs

        center = bs.body.find("div", {"class": "col-xs-12 col-lg-8 text-center"})
        if not center:
            raise NoLyrics

        lyrics = center.find("div", {"class": None}).text

        lyrics = re.sub(r"<br>", " ", lyrics)
        lyrics = re.sub(r"<i?>\W*", "[", lyrics)
        lyrics = re.sub(r"\W*</i>", "]", lyrics)
        lyrics = re.sub(r"&quot;", "\"", lyrics)
        lyrics = re.sub(r"</div>", "", lyrics)

        title = center.find("h1").text.strip()[1:-8]
        artist = bs.select_one("div.lyricsh h2 b").string[:-7]
        lyrics = lyrics.strip()

        return Lyrics(title, lyrics, artist=artist)
