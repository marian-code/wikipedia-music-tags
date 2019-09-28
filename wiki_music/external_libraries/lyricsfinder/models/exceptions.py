"""Lyric finder exceptions."""

LyricsException = type("LyricsException", (Exception,), {})
NoLyrics = type("NoLyrics", (LyricsException,), {})
NotAllowedError = type("NotAllowedError", (LyricsException,), {})


class NoExtractorError(LyricsException):
    """When there's no extractor for a url."""

    def __init__(self, url):
        """Create new."""
        super().__init__("No extractor found for {}".format(url))
