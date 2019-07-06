import asyncio
import logging
from typing import Any, AsyncIterator, Generator, List, Optional, TYPE_CHECKING, Type

from aiohttp import ClientSession

from .exceptions import NoExtractorError, NoLyrics
from .lyrics import Lyrics

if TYPE_CHECKING:
    from lyricsfinder import LyricsManager

__all__ = ["SearchResult"]

log = logging.getLogger(__name__)


class SearchResult:
    def __init__(self, manager: Type["LyricsManager"], session: Optional[ClientSession], url_iter: AsyncIterator[str], query: str) -> None:
        self._manager = manager
        self._session = session
        self._url_iter = url_iter
        self._query = query

    def __repr__(self) -> str:
        return f"SearchResult({self._url_iter!r}, {self._query!r})"

    def __str__(self) -> str:
        return f"SearchResult \"{self._query}\""

    def __await__(self) -> Generator[Any, None, Lyrics]:
        return self.next().__await__()

    async def __aiter__(self) -> AsyncIterator[Lyrics]:
        return self

    async def __anext__(self) -> Optional[Lyrics]:
        try:
            return await self.next()
        except NoLyrics:
            return None

    @property
    def query(self) -> str:
        return self._query

    def _inject_query(self, lyrics: Lyrics) -> Lyrics:
        lyrics.origin.query = self._query
        return lyrics

    async def _extract_lyrics(self, url: str, *, silent: bool = True) -> Optional[Lyrics]:
        try:
            lyrics = await self._manager.extract_lyrics(url, session=self._session)
        except NoExtractorError as e:
            if silent:
                log.warning(f"No extractor for url {url}")
                return None
            else:
                raise e
        else:
            return self._inject_query(lyrics)

    async def next_url(self) -> Optional[str]:
        try:
            return await self._url_iter.__anext__()
        except StopAsyncIteration:
            return None

    async def next(self, *, silent: bool = True) -> Lyrics:
        url = await self.next_url()

        while url:
            lyrics = await self._extract_lyrics(url, silent=silent)

            if lyrics:
                return lyrics
            else:
                log.warning(f"No extractor for url {url}")
                url = await self.next_url()

        raise NoLyrics(f"Couldn't find any lyrics for query {self._query}")

    async def url_list(self) -> List[str]:
        urls = []
        async for url in self._url_iter:
            urls.append(url)
        return urls

    async def to_list(self, *, max_results: int = None, timeout: float = None) -> List[Lyrics]:
        loop = asyncio.get_event_loop()
        futures = []
        async for url in self._url_iter:
            coro = self._extract_lyrics(url)
            futures.append(asyncio.ensure_future(coro, loop=loop))

            if len(futures) >= max_results:
                break

        gathered = asyncio.gather(*futures, loop=loop)
        result = await asyncio.wait_for(gathered, timeout, loop=loop)

        return [lyrics for lyrics in result if lyrics]
