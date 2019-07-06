import logging
import re
from datetime import datetime

from aiohttp import ClientResponseError

from lyricsfinder import Lyrics
from lyricsfinder.extractor import LyricsExtractor
from lyricsfinder.utils import Request
from ..models import exceptions

log = logging.getLogger(__name__)

ORDINAL_MATCHER = re.compile(r"(\d{1,2})(st|nd|rd|th)")


class MusixMatch(LyricsExtractor):
    name = "MusixMatch"
    url = "https://www.musixmatch.com/"
    display_url = "musixmatch.com"

    @classmethod
    async def extract_lyrics(cls, request: Request) -> Lyrics:
        request.headers = {"user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1"}
        try:
            (await request.resp).raise_for_status()
        except ClientResponseError:
            raise exceptions.NotAllowedError
        bs = await request.bs

        if bs.find_all("div", attrs={"class": "mxm-empty-state", "data-reactid": "87"}):
            raise exceptions.NoLyrics

        lyrics_frame = bs.find_all("div", {"class": "mxm-lyrics"})

        if not lyrics_frame:
            raise exceptions.NoLyrics

        lyrics_window = lyrics_frame[0].find_all("div", {"class": "mxm-lyrics"})

        if not lyrics_window:
            raise exceptions.NoLyrics

        lyrics_window = lyrics_window[0].span

        for garbage in bs.find_all("script"):
            garbage.replace_with(2 * "\n")

        lyrics = lyrics_window.text
        title = bs.find("h1", attrs={"class": "mxm-track-title__track"}).contents[-1].strip()
        artist = bs.select_one("a.mxm-track-title__artist").string
        release_date = None
        date_str = bs.select_one("div.mxm-track-footer__album h3.mui-cell__subtitle")
        if date_str:
            date_str = ORDINAL_MATCHER.sub(lambda m: m.group(1).zfill(2), date_str.string)
            release_date = datetime.strptime(date_str, "%b %d %Y")

        return Lyrics(title, lyrics, artist=artist, release_date=release_date)
