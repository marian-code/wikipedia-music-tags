LyricsException = type("LyricsException", (Exception,), {})
NoLyrics = type("NoLyrics", (LyricsException,), {})
NotAllowedError = type("NotAllowedError", (LyricsException,), {})


class NoExtractorError(LyricsException):
    def __init__(self, url: str):
        super().__init__(f"No extractor found for {url}")
