"""Fancy lyrics managment."""

import logging
from typing import Iterator, List

from . import extractors
from .extractor import LyricsExtractor
from .models import Lyrics, LyricsOrigin, exceptions
from .utils import UrlData, search, generate_url

log = logging.getLogger(__name__)


class LyricsManager:
    """Manage stuff."""

    extractors: List[LyricsExtractor] = []

    google_api_key = None

    @classmethod
    def setup(cls):
        log.debug("setting up")
        extractors.load_extractors()

        cls.extractors = LyricsExtractor.extractors
        log.info("loaded {} extractors".format(len(cls.extractors)))

    def extract_lyrics(self, url: str, song: str, artist: str) -> Lyrics:
        """Extract lyrics from url."""
        #log.info("extracting lyrics from url \"{}\"".format(url))
        url_data = UrlData(url)
        for ext in self.extractors:

            if not ext.can_handle(url_data):
                continue

            extractor = ext()

            log.debug("using {} for {}".format(ext, url_data))
            
            try:
                lyrics = extractor.extract_lyrics(url_data, song, artist)
            except exceptions.NoLyrics:
                log.warning(f"{extractor} didn't find any lyrics at {url}")
                continue
            except exceptions.NotAllowedError:
                log.warning(f"{extractor} couldn't access lyrics at {url}")
                continue
            except Exception:
                # switch of so it doesn´t clutter console
                # when not debugging
                log.exception(f"Something went wrong when {extractor} "
                              f"handled {url}")
                continue
            else:
                lyrics.origin = LyricsOrigin(url, extractor.name,
                                             extractor.url)
                log.debug("extracted lyrics {}".format(lyrics))
                return lyrics
        raise exceptions.NoExtractorError(url)

    def search_lyrics(self, song: str, album: str, artist: str, *,
                      google_api_key: str) -> Iterator[Lyrics]:
        """Search the net for lyrics."""
        query = artist + " " + song
        results = search(query, google_api_key)

        log.debug("got {} results fom google search".format(len(results)))

        #google search does not return any results sometimes
        if not results:
            log.warning("Google custom search returned no results! "
                        "---> Switching to url generation")
            results = generate_url(artist, album, song)

        for result in results:
            url = result["link"]

            try:
                lyrics = self.extract_lyrics(url, song, artist)
            except exceptions.NoExtractorError:
                log.warning("No extractor for url {}".format(url))
                continue
            else:
                lyrics.origin.query = query
                yield lyrics
        log.warning("No lyrics found for query \"{}\"".format(query))


LyricsManager.setup()
