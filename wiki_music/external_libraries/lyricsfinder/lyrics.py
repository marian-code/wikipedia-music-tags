"""Fancy lyrics managment."""

import logging
from typing import TYPE_CHECKING, Iterator, List

from . import extractors
from .extractor import LyricsExtractor
from .extractors.animelyrics import Animelyrics
from .extractors.azlyrics import AZLyrics
from .extractors.darklyrics import Darklyrics
from .extractors.genius import Genius
from .extractors.lyrical_nonsense import LyricalNonsense
from .extractors.lyricsmode import Lyricsmode
from .extractors.musixmatch import MusixMatch
from .models import Lyrics, LyricsOrigin, exceptions
from .utils import UrlData, generate_url, search

log = logging.getLogger(__name__)


class LyricsManager:
    """Manage stuff."""

    extractors: List[LyricsExtractor] = []

    google_api_key = None

    @classmethod
    def setup(cls):
        """Initialize class."""
        log.debug("setting up")
        # ! dissabled because of pyinstaller
        # extractors.load_extractors()

        cls.extractors = LyricsExtractor.extractors
        log.info("loaded {} extractors".format(len(cls.extractors)))

    @classmethod
    def extract_lyrics(cls, url: str, song: str, artist: str) -> Lyrics:
        """Extract lyrics from url."""
        log.info("extracting lyrics from url \"{}\"".format(url))
        url_data = UrlData(url)
        for extractor in cls.extractors:

            if not extractor.can_handle(url_data):
                continue

            log.debug("using {} for {}".format(extractor, url_data))

            try:
                lyrics = extractor.extract_lyrics(url_data, song, artist)
            except exceptions.NoLyrics:
                log.warning(f"{extractor} didn't find any lyrics at {url}")
                continue
            except exceptions.NotAllowedError:
                log.warning(f"{extractor} couldn't access lyrics at {url}")
                continue
            except Exception:
                log.exception(f"Something went wrong when {extractor} "
                              f"handled {url}")
                continue
            else:
                lyrics.origin = LyricsOrigin(url, extractor.name,
                                             extractor.url)
                log.debug(f"extracted lyrics {lyrics}")
                return lyrics
        raise exceptions.NoExtractorError(url)

    @classmethod
    def search_lyrics(cls, song: str, album: str, artist: str, *,
                      google_api_key: str) -> Iterator[Lyrics]:
        """Search the net for lyrics."""
        query = artist + " " + song
        results = search(query, google_api_key)

        log.debug("got {} results fom google search".format(len(results)))

        # google search does not return any results after daily limit
        # of 100 searches is exceeded
        if not results:
            log.warning("Google custom search returned no results! "
                        "---> Switching to url generation")
            results = generate_url(artist, album, song)

        for result in results:
            url = result["link"]

            try:
                lyrics = cls.extract_lyrics(url, song, artist)
            except exceptions.NoExtractorError:
                log.warning("No extractor for url {}".format(url))
                continue
            else:
                lyrics.origin.query = query
                yield lyrics
        log.warning("No lyrics found for query \"{}\"".format(query))


LyricsManager.setup()
