"""Defines exceptions for whole package."""

import logging

log = logging.getLogger(__name__)

__all__ = ["NoTracklistException", "NoReleaseDateException",
           "NoGenreException", "NoCoverArtException",
           "NoNames2ExtractException", "NoContentsException",
           "NoPersonnelException", "Mp3tagNotFoundException",
           "NltkUnavailableException", "TagReadException",
           "TagSaveException", "ExceptionBase", "UnsupportedFileType"]


class _ExceptionCollect(type):
    """Registers new Exceptions."""

    def __init__(cls, name, bases, attrs):
        """Add base class to list of exceptions."""
        if not hasattr(cls, "exceptions"):
            cls.exceptions = []
            log.debug("Created Exception Meta Class")
        else:
            cls.exceptions.append(cls)
            log.debug("Registered Exception \"{}\"".format(name))

    @property
    def registered_exceptions(cls):
        return tuple(cls.exceptions)


class ExceptionBase(Exception, metaclass=_ExceptionCollect):
    """Base exception class for all package exceptions."""

    name: str = "ExceptionBase"


class NoTracklistException(ExceptionBase):
    """Raised when no tracklist is found on wikipedia page."""

    name: str = "NoTracklistException"


class NoReleaseDateException(ExceptionBase):
    """Raised when release date could not be extracted."""

    name: str = "NoReleaseDateException"


class NoGenreException(ExceptionBase):
    """Raised when genres could not be extracted."""

    name: str = "NoGenreException"


class NoCoverArtException(ExceptionBase):
    """Raised when cover art could not be extracted."""

    name: str = "NoCoverArtException"


class NoNames2ExtractException(ExceptionBase):
    """Raised when cover art could not be extracted."""

    name: str = "NoNames2ExtractException"


class NoContentsException(ExceptionBase):
    """Raised when page contents could not be extracted."""

    name: str = "NoContentsException"


class NoPersonnelException(ExceptionBase):
    """Raised when page contents could not be extracted."""

    name: str = "NoPersonnelException"


class Mp3tagNotFoundException(ExceptionBase):
    """Raised when Mp3tag could not be run."""

    name: str = "Mp3tagNotFoundException"


class NltkUnavailableException(ExceptionBase):
    """Raised when Mp3tag could not be run."""

    name: str = "NltkUnavailableException"


class TagReadException(ExceptionBase):
    """Raised when tags could not be read from file."""

    name: str = "TagReadException"


class TagSaveException(ExceptionBase):
    """Raised when tags could not be saved to file."""

    name: str = "TagSaveException"


class UnsupportedFileType(ExceptionBase):
    """Raised when wiki_music cannot handle tags for given file type."""

    name: str = "UnsupportedFileType"
