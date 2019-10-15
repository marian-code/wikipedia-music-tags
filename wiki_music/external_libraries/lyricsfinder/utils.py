"""Utitlities."""

import re
from typing import List, Tuple, Optional

import requests
from bs4 import BeautifulSoup
from requests import Response


class UrlData:
    """Url stuff."""

    _resp: Optional[Response]
    _html: Optional[str]
    _bs: Optional[BeautifulSoup]

    def __init__(self, url: str):
        """Build url."""
        self.headers: dict = {}

        self.html_parser: str = "lxml"

        self._url = url
        self._resp = None
        self._html = None
        self._bs = None

    def __str__(self):
        """Return string rep."""
        return "<{}>".format(self.url)

    @property
    def resp(self) -> Response:
        """Get the requests response object."""
        if not self._resp:
            self._resp = requests.get(self.url, headers=self.headers)
        return self._resp

    @property
    def html(self) -> str:
        """Get the html for this url."""
        if not self._html:
            self._html = self.resp.text
        return self._html

    @property
    def bs(self) -> BeautifulSoup:
        """Get the BeautifulSoup object."""
        if not self._bs:
            self._bs = BeautifulSoup(self.html, self.html_parser)
        return self._bs

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value: str):
        self._url = value
        self._resp = None
        self._html = None
        self._bs = None


def search(query: str, api_key: str) -> List:
    """Return search results."""

    # ! to edit head to: https://cse.google.com/cse/all

    params = {
        "key": api_key,
        #"cx": "'000281471148392423350:ymsqkb0dqs8"
        "cx": "000281471148392423350:64fnnp-ny2w",  # original + darklyrics
        #"cx": "002017775112634544492:7y5bpl2sn78", # original without darklyrics
        "q": query
    }
    resp = requests.get("https://www.googleapis.com/customsearch/v1",
                        params=params)
    data = resp.json()
    items = data.get("items", [])
    return items


def generate_url(artist: str, album: str, song: str) -> List[dict]:

    # the list of words that are not capitalized, may not be exhaustive!!
    DONT_CAPITALIZE: Tuple[str, ...] = ("on", "at", "by", "or", "a", "an",
                                        "of", "and", "but")

    # no = ["under","between", "over", "after","without","until",
    #       "because","every","this","those", "many", ]
    # maybe = ["and","but",]

    def r(string: str, replace: str) -> str:
        return string.replace(" ", replace)

    urls: List[dict] = []

    artist = re.sub(r"\(|\)|\'", "", artist).strip().lower()
    album = re.sub(r"\(|\)|\'", "", album).strip().lower()
    song = re.sub(r"\(|\)|\'", "", song).strip().lower()

    # darklyrics
    urls.append({
        "link":
        f"http://www.darklyrics.com/lyrics/{r(artist, '')}/" +
        f"{r(album, '')}.html"
    })
    # AZLyrics
    urls.append({
        "link":
        f"https://www.azlyrics.com/lyrics/{r(artist, '')}/" +
        f"{r(song, '')}.html"
    })
    # Genius
    link = (f"https://genius.com/{r(artist.capitalize(), '-')}"
            f"-{r(song, '-')}-lyrics").replace("&", "and")
    urls.append({"link": link})  # sometimes annotated version is present
    urls.append({"link": f"{link}-annotated"})
    # Lyricsmode
    urls.append({
        "link":
        f"http://www.lyricsmode.com/lyrics/{artist[0]}/" +
        f"{r(artist, '_')}/{r(song, '_')}.html"
    })
    # Musixmatch
    song = "-".join([
        s.capitalize() for s in song.split() if s not in DONT_CAPITALIZE
    ]).capitalize()
    urls.append({
        "link":
        f"https://www.musixmatch.com/lyrics/" +
        f"{r(artist.upper(), '-')}/{song}"
    })
    # Lyrical Nonsense, Anime Lyrics - useless, some Japanese lyrics

    return urls


def safe_filename(name: str, file_ending: str = ".json") -> str:
    """Return a safe version of name + file_type."""
    filename = re.sub(r"\s+", "_", name)
    filename = re.sub(r"\W+", "-", filename)

    return filename.lower().strip() + file_ending


def clean_lyrics(lyrics: str) -> str:
    """Perform some simple operations to clean the lyrics."""
    lyrics = lyrics.strip()
    # remove unwanted characters
    lyrics = re.sub(r"[^\w\[\]()/ \"',\.:\-\n?!]+", "", lyrics)
    # reduce to one space only
    lyrics = re.sub(r" +", " ", lyrics)
    # reduce to max 2 new lines in a row
    lyrics = re.sub(r"\n{2,}", "\n\n", lyrics)
    # remove space before newline
    lyrics = re.sub(r" +?\n", "\n", lyrics)

    return lyrics
