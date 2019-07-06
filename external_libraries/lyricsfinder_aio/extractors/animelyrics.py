import logging
import re

from lyricsfinder import Lyrics, NoLyrics
from lyricsfinder.extractor import LyricsExtractor
from lyricsfinder.utils import Request

log = logging.getLogger(__name__)

ARTIST_MATCHER = re.compile(r"^Performed by ([\w' ]+)\b", re.MULTILINE)


class Animelyrics(LyricsExtractor):
    name = "Animelyrics"
    url = "http://www.animelyrics.com/"
    display_url = "animelyrics.com"

    @classmethod
    async def extract_lyrics(cls, request: Request) -> Lyrics:
        bs = await request.bs
        title = next(bs.select_one("div ~ h1").children).string.strip()
        artist = bs.find(text=ARTIST_MATCHER)
        if artist:
            artist = ARTIST_MATCHER.match(artist).group(1)

        lyrics_window = bs.find("table", attrs={"cellspacing": "0", "border": "0"})

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
            text_url = re.sub(r"\.html?", ".txt", request.url)
            request.url = text_url
            request.resp_kwargs["allow_redirects"] = False
            text = await request.text
            content = text.strip()
            match = re.search(r"-{10,}(.+?)-{10,}", content, flags=re.DOTALL)
            if match:
                lyrics = match.group(1).strip()
            else:
                raise NoLyrics

        lyrics = lyrics.replace("\xa0", " ").replace("\r", "")

        return Lyrics(title, lyrics, artist=artist)
