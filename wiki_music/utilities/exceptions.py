"""Defines exception for whole package."""

import logging

logging.getLogger(__name__)

__all__ = ["NoTracklistException", "NoReleaseDateException",
           "NoGenreException", "NoCoverArtException",
           "NoNames2ExtractException", "NoContentsException",
           "NoPersonnelException", "Mp3tagNotFoundException",
           "NltkUnavailableException"]


class NoTracklistException(Exception):
    """Exception raised when no tracklist is found on wikipedia page."""

    pass


class NoReleaseDateException(Exception):
    """Exception raised when release date could not be extracted."""

    pass


class NoGenreException(Exception):
    """Exception raised when genres could not be extracted."""

    pass


class NoCoverArtException(Exception):
    """Exception raised when cover art could not be extracted."""

    pass


class NoNames2ExtractException(Exception):
    """Exception raised when cover art could not be extracted."""

    pass


class NoContentsException(Exception):
    """Exception raised when page contents could not be extracted."""

    pass


class NoPersonnelException(Exception):
    """Exception raised when page contents could not be extracted."""

    pass


class Mp3tagNotFoundException(Exception):
    """Exception raised when Mp3tag could not be run."""

    pass


class NltkUnavailableException(Exception):
    """Exception raised when Mp3tag could not be run."""

    pass
