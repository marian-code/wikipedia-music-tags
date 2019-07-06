"""Fancy lyrics managment."""

import logging
from typing import Iterator

from .extractor import LyricsExtractor
from .models import Lyrics, LyricsOrigin, exceptions
from .utils import UrlData, search, generate_url

log = logging.getLogger(__name__)
#log.setLevel(logging.DEBUG)
#logging.basicConfig()


class LyricsManager:
    """Manage stuff."""

    extractors = []

    google_api_key = None

    @classmethod
    def setup(cls):
        """Load extractors."""
        log.debug("setting up")
        # noinspection PyUnresolvedReferences
        #from . import extractors

        # this was introduced as a workaround for freeze support 
        # with cx_freeze. The original implementation was not able
        # to load modules from extractors dir
        from .extractors.genius import Genius
        from .extractors.azlyrics import AZLyrics
        from .extractors.darklyrics import Darklyrics
        from .extractors.lyrical_nonsense import LyricalNonsense
        from .extractors.lyricsmode import Lyricsmode
        from .extractors.musixmatch import MusixMatch
        from .extractors.animelyrics import Animelyrics

        cls.extractors = [Genius, AZLyrics, Darklyrics, LyricalNonsense, Lyricsmode, MusixMatch, Animelyrics]
        #log.info("loaded {} extractors".format(len(cls.extractors)))

    @classmethod
    def extract_lyrics(cls, url: str, song: str, artist: str) -> Lyrics:
        """Extract lyrics from url."""
        #log.info("extracting lyrics from url \"{}\"".format(url))
        url_data = UrlData(url)
        for extractor in cls.extractors:
            if extractor.can_handle(url_data):
                log.debug("using {} for {}".format(extractor, url_data))
                try:
                    lyrics = extractor.extract_lyrics(url_data, song, artist)
                except exceptions.NoLyrics:
                    log.warning("{} didn't find any lyrics at {}".format(extractor, url))
                    continue
                except exceptions.NotAllowedError:
                    log.warning("{} couldn't access lyrics at {}".format(extractor, url))
                    continue
                except Exception:
                    # switch of so it doesn´t clutter console 
                    # when not debugging
                    #log.exception("Something went wrong when {} handled {}".format(extractor, url_data))
                    continue

                if lyrics:
                    lyrics.origin = LyricsOrigin(url, extractor.name, extractor.url)
                    log.debug("extracted lyrics {}".format(lyrics))
                    return lyrics
        raise exceptions.NoExtractorError(url)

    @classmethod
    def search_lyrics(cls, song: str, album: str, artist: str, *, google_api_key: str) -> Iterator[Lyrics]:
        """Search the net for lyrics."""
        query = artist + " " + song
        results = search(query, google_api_key)

        log.debug("got {} results fom google search".format(len(results)))

        #google search does not return any results sometimes
        if len(results) == 0:
            log.warning("Google custom search returned no results! ---> Switching to url generation")
            results = generate_url(artist, album, song)

        for result in results:
            url = result["link"]

            try:
                lyrics = cls.extract_lyrics(url, song, artist)
            except exceptions.NoExtractorError as e:
                log.warning("No extractor for url {}".format(url))
                continue
            if lyrics:
                lyrics.origin.query = query
                yield lyrics
        log.warning("No lyrics found for query \"{}\"".format(query))


LyricsManager.setup()
