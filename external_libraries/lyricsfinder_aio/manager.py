import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, List

from aiohttp import ClientSession

from . import extractors
from .extractor import LyricsExtractor
from .models import Lyrics, LyricsOrigin, SearchResult, exceptions
from .utils import Request, google_search

log = logging.getLogger(__name__)


class LyricsManager:
    extractors: List[LyricsExtractor] = []

    @classmethod
    def setup(cls):
        log.debug("setting up")
        extractors.load_extractors()

        cls.extractors = LyricsExtractor.extractors
        log.info("loaded {} extractors".format(len(cls.extractors)))

    @classmethod
    @asynccontextmanager
    async def get_session(cls, session: ClientSession = None) -> ClientSession:
        if session:
            yield session
        else:
            async with ClientSession() as session:
                yield session

    @classmethod
    async def extract_lyrics(cls, url: str, song: str, artist: str, *, session: ClientSession = None) -> Lyrics:
        async with cls.get_session(session) as session:
            exc = None

            log.info("extracting lyrics from url \"{url}\"")
            request = Request(session, url, song, artist)

            for extractor in cls.extractors:
                if not await extractor.can_handle(request):
                    continue

                log.debug(f"using {extractor} for {request}")
                try:
                    lyrics = await extractor.extract_lyrics(request)
                except exceptions.NoLyrics:
                    log.warning(f"{extractor} didn't find any lyrics at {url}")
                    continue
                except exceptions.NotAllowedError:
                    log.warning(f"{extractor} couldn't access lyrics at {url}")
                    continue
                except Exception as e:
                    e.__cause__ = exc
                    exc = e
                    log.exception(f"Something went wrong when {extractor} handled {request}")
                    continue
                else:
                    lyrics.set_origin(LyricsOrigin(url, extractor.name, extractor.url))
                    log.debug(f"extracted lyrics {lyrics}")
                    return lyrics

            raise exceptions.NoExtractorError(url) from exc

    @classmethod
    async def search_lyrics_url_gen(cls, query: str, *, api_key: str, session: ClientSession = None) -> AsyncIterator[str]:
        async with cls.get_session(session) as session:
            result_iter = google_search(session, query, api_key)

            async for result in result_iter:
                url = result.link
                yield url

    @classmethod
    def search_lyrics(cls, song: str, album: str, artist: str, *, api_key: str, session: ClientSession = None) -> SearchResult:
        query = f"{artist} {song}"
        url_iter = cls.search_lyrics_url_gen(query, api_key=api_key, session=session)
        return SearchResult(cls, session, url_iter, query)
