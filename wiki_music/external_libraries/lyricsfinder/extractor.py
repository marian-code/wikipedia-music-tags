"""Base for extracting."""

import abc
import logging
from typing import TYPE_CHECKING

from .utils import UrlData

if TYPE_CHECKING:
    from .lyrics import Lyrics

log = logging.getLogger(__name__)


class LyricsExtractorMount(type):
    """Registers new Extractors."""

    def __init__(cls, name, bases, attrs):
        """Add base class to list of extractors."""
        if not hasattr(cls, "extractors"):
            cls.extractors = []
            log.debug("Created Extractor Meta Class")
        else:
            cls.extractors.append(cls)
            log.debug("Registered Extractor \"{}\"".format(name))

    def __str__(self):
        """Return string rep."""
        return "<Extractor {}>".format(self.__name__)


class LyricsExtractor(metaclass=LyricsExtractorMount):
    """A class capable of retrieving lyrics."""

    name: str = "GENERIC"
    url: str = "http://giesela.org"
    display_url: str = "giesela.org"

    @classmethod
    def can_handle(cls, url_data: UrlData) -> bool:
        """Check whether this extractor can extract lyrics from this url."""
        return cls.display_url in url_data.url

    @abc.abstractmethod
    def extract_lyrics(self, url_data: UrlData, song: str, artist: str
                       ) -> "Lyrics":
        """Return a Lyrics object for the given url, html or bs."""
        raise NotImplementedError

    def __str__(self):
        return "<Extractor {}>".format(self.name)
