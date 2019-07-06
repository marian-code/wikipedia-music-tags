import logging
import re
from typing import AsyncIterator, NamedTuple

from aiohttp import ClientResponse, ClientSession
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


class Request:
    def __init__(self, session: ClientSession, url: str, song: str, artist: str):
        self.session = session
        self.song = song
        self.artist = artist

        self._url = url
        self.resp_kwargs = {}
        self.headers = {}

        self._resp = None
        self._text = None
        self._bs = None

    def __repr__(self) -> str:
        """Return string rep."""
        return "<{}>".format(self.url)

    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, value: str):
        self._url = value
        self._resp = None
        self._text = None
        self._bs = None

    @property
    async def resp(self) -> ClientResponse:
        if not self._resp:
            self._resp = await self.session.get(self.url, headers=self.headers, **self.resp_kwargs)
        return self._resp

    @property
    async def text(self) -> str:
        if not self._text:
            self._text = await (await self.resp).text()
        return self._text

    @property
    async def bs(self) -> BeautifulSoup:
        if not self._bs:
            self._bs = BeautifulSoup(await self.text, "lxml")
        return self._bs


class GoogleSearchItem(NamedTuple):
    link: str


async def google_search(session: ClientSession, query: str, api_key: str) -> AsyncIterator[GoogleSearchItem]:
    item_count = 10

    params = {
        "q": query,
        "key": api_key,
        "cx": "000281471148392423350:64fnnp-ny2w", # original + darklyrics
        #"cx": "002017775112634544492:7y5bpl2sn78", # original without darklyrics
        "fields": "items(link)",
        "num": item_count
    }

    for start in range(1, 101, item_count):
        params["start"] = start
        log.debug(f"getting search results starting from {start}")
        async with session.get("https://www.googleapis.com/customsearch/v1", params=params) as resp:
            data = await resp.json()
            items = data.get("items", [])
            for item in items:
                yield GoogleSearchItem(**item)


RE_CHAR_COLLAPSERS = [
    (r"～", "~"),
    (r"[“”]", "\"")
]


def generate_url(artist: str, album: str, song: str) -> list:

    urls = []

    artist = re.sub(r"\(|\)|\'", "", artist)
    album = re.sub(r"\(|\)|\'", "", album)
    song = re.sub(r"\(|\)|\'", "", song)

    # darklyrics
    urls.append({"link": "http://www.darklyrics.com/lyrics/" + artist.lower().replace(" ", "") + "/" + album.lower().replace(" ", "") + ".html"})

    # Anime Lyrics
    # useless - some Japanese lyrics
    
    # AZLyrics
    urls.append({"link": "https://www.azlyrics.com/lyrics/" + artist.lower().replace(" ", "") + "/" + song.lower().replace(" ", "") + ".html"})
    
    # Genius
    urls.append({"link": "https://genius.com/" + artist.strip().lower().capitalize().replace(" ", "-") + "-" + song.strip().lower().replace(" ", "-") + "-lyrics"})
    
    # Lyricsmode
    urls.append({"link": "http://www.lyricsmode.com/lyrics/l/" + artist.lower().replace(" ", "_") + "/" + song.lower().replace(" ", "_") + ".html"})
    
    # Lyrical Nonsense
    # useless - some Japanese lyrics
    
    # Musixmatch
    song = song.split()
    # the list of words that arte not capitalized, may not be exhaustive!!
    do_not_capitatize =["on", "at", "by", "or", "a", "an", "of", "and", "but"]
    # no = ["under","between", "over", "after","without","until", "because","every","this","those", "many", ]
    # maybe = ["and","but",]
    song[0] = song[0].capitalize()
    for i in range(1, len(song)):
        if song[i] not in do_not_capitatize:
            song[i] = song[i].capitalize()

    song = "-".join(song)        

    urls.append({"link": "https://www.musixmatch.com/lyrics/" + artist.strip().upper().replace(" ", "-") + "/" + song})

    return urls


def clean_lyrics(lyrics: str, *, allowed: str = "") -> str:
    lyrics = lyrics.strip()
    for target, replacement in RE_CHAR_COLLAPSERS:
        lyrics = re.sub(target, replacement, lyrics)

    lyrics = re.sub(rf"[^\w\[\]()/ \"',.:\-~\n?!{allowed}]+", "", lyrics)  # remove unwanted characters
    lyrics = re.sub(r" +", " ", lyrics)  # reduce to one space only
    lyrics = re.sub(r"\n{2,}", "\n\n", lyrics)  # reduce to max 2 new lines in a row
    lyrics = re.sub(r" +?\n", "\n", lyrics)  # remove space before newline

    return lyrics
