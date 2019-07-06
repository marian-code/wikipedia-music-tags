import logging

from lyricsfinder import Lyrics
from lyricsfinder.extractor import LyricsExtractor
from lyricsfinder.utils import Request, clean_lyrics

log = logging.getLogger(__name__)


class LyricalNonsense(LyricsExtractor):
    name = "Lyrical Nonsense"
    url = "http://www.lyrical-nonsense.com/"
    display_url = "lyrical-nonsense.com"

    @classmethod
    async def extract_lyrics(cls, url_data: Request) -> Lyrics:
        bs = await url_data.bs
        title_el = bs.select_one("span.titletext2new")
        if not title_el:
            title_el = bs.select_one("div.titlelyricblocknew h1")
        title = title_el.text

        artist = bs.select_one("div.artistcontainer span.artisttext2new")
        if not artist:
            artist = bs.select_one("div.artistcontainer h2")

        artist = artist.text

        lyrics_window = bs.select_one("div#Romaji div.olyrictext") or bs.select_one("div#Lyrics div.olyrictext")
        text = "\n\n".join(tag.text for tag in lyrics_window.find_all("p"))
        lyrics = clean_lyrics(text)

        return Lyrics(title, lyrics, artist=artist)
