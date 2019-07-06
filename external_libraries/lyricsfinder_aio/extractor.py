import abc
import logging
from typing import TYPE_CHECKING

from .utils import Request

if TYPE_CHECKING:
    from .manager import Lyrics

log = logging.getLogger(__name__)


class LyricsExtractorMount(type):
    """Registers new Extractors."""

    def __init__(cls, *args):
        super().__init__(*args)

        if not hasattr(cls, "extractors"):
            cls.extractors = []
            log.debug("Created Extractor Meta Class")
        else:
            cls.extractors.append(cls)
            log.debug(f"Registered {cls}")

    def __str__(self):
        """Return string rep."""
        return "<Extractor {}>".format(self.__name__)


class LyricsExtractor(metaclass=LyricsExtractorMount):
    name: str
    url: str
    display_url: str

    @classmethod
    async def can_handle(cls, url_data: Request) -> bool:
        """Check whether this extractor can extract lyrics from this url."""
        return cls.display_url in url_data.url

    @classmethod
    @abc.abstractmethod
    async def extract_lyrics(cls, url_data: Request) -> "Lyrics":
        """Return a Lyrics object for the given url, text or bs."""
        raise NotImplementedError
