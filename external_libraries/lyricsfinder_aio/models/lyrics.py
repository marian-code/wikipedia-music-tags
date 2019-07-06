from datetime import datetime
from typing import Any, Dict


class LyricsOrigin:

    def __init__(self, url: str, source_name: str, source_url: str, *, query: str = None):
        self.url = url
        self.source_name = source_name
        self.source_url = source_url
        self.query = query

    def __str__(self) -> str:
        return self.source_name

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LyricsOrigin":
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "url": self.url,
            "source_name": self.source_name,
            "source_url": self.source_url
        }


class Lyrics:
    def __init__(self, title: str, lyrics: str, artist: str = None, release_date: datetime = None, *, origin: LyricsOrigin = None):
        self.title = title
        self.artist = artist
        self.release_date = release_date
        self.lyrics = lyrics
        self.origin = origin

    def __str__(self) -> str:
        return "<Lyrics for \"{}\" from {}>".format(self.title, self.origin)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        data["origin"] = LyricsOrigin.from_dict(data["origin"])
        if data["release_date"]:
            data["release_date"] = datetime.fromtimestamp(data["release_date"])
        return cls(**data)

    def set_origin(self, origin: LyricsOrigin):
        self.origin = origin

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "artist": self.artist,
            "release_date": self.release_date.timestamp() if self.release_date else None,
            "lyrics": self.lyrics,
            "origin": self.origin.to_dict()
        }
