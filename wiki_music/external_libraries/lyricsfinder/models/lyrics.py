"""Lyrics object."""
import json
from datetime import datetime
from io import TextIOBase
from typing import Any, Dict, Union, TYPE_CHECKING, Optional

from .. import utils

if TYPE_CHECKING:
    from typing_extensions import TypedDict

    OrignDict = TypedDict("OrignDict", {"query": Optional[str], "url": str,
                                        "source_name": str, "source_url": str})

    LyricsDict = TypedDict("LyricsDict", {"title": str, "release_date": Any,
                                          "artist": Optional[str],
                                          "lyrics": str, "origin": OrignDict})


class LyricsOrigin:
    """Represents a place where lyrics come from."""

    def __init__(self, url: str, source_name: str, source_url: str, *,
                 query: str = None):
        """Create new origin."""
        self.url = url
        self.source_name = source_name
        self.source_url = source_url
        self.query = query

    def __str__(self):
        """Return string rep."""
        return self.source_name

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LyricsOrigin":
        """Load from dict."""
        return cls(**data)

    def to_dict(self) -> "OrignDict":
        """Convert to dict."""
        return {
            "query": self.query,
            "url": self.url,
            "source_name": self.source_name,
            "source_url": self.source_url
        }


class Lyrics:
    """Represents lyrics for a song."""

    def __init__(self, title: str, lyrics: str, artist: str = None,
                 release_date: datetime = None, *,
                 origin: LyricsOrigin = None):
        """Create lyrics."""
        self.title = title
        self.artist = artist
        self.release_date = release_date
        self.lyrics = lyrics
        self.origin = origin

    def __str__(self):
        """Return string rep."""
        return "<Lyrics for \"{}\" from {}>".format(self.title, self.origin)

    @property
    def save_name(self) -> str:
        """Get a possible filename."""
        return utils.safe_filename(self.origin.query or self.title)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Load from dict."""
        data["origin"] = LyricsOrigin.from_dict(data["origin"])
        if data["release_date"]:
            data["release_date"] = datetime.fromtimestamp(data["release_date"])
        return cls(**data)

    def to_dict(self) -> "LyricsDict":
        """Convert to dict."""
        return {
            "title": self.title,
            "artist": self.artist,
            "release_date": self.release_date.timestamp() if self.release_date else None,
            "lyrics": self.lyrics.replace("\r", "").replace("\n", "\r\n"),
            "origin": self.origin.to_dict()
        }

    def save(self, f: Union[str, TextIOBase] = None) -> TextIOBase:
        """Save the lyrics."""
        if isinstance(f, TextIOBase):
            d = f
        elif isinstance(f, str):
            d = open(f, "w+")
        else:
            d = open(self.save_name, "w+")

        json.dump(self.to_dict(), d)
        d.seek(0)

        return d
