""" Defines exception for whole package. """

class NoTracklistException(Exception):
    """ Exception raised when no tracklist is found on wikipedia page. """
    pass

class NoReleaseDateException(Exception):
    """ Exception raised when release date could not be extracted. """
    pass

class NoGenreException(Exception):
    """ Exception raised when genres could not be extracted. """
    pass

class NoCoverArtException(Exception):
    """ Exception raised when cover art could not be extracted. """
    pass

class NoNames2ExtractException(Exception):
    """ Exception raised when cover art could not be extracted. """
    pass

class NoContentsException(Exception):
    """ Exception raised when page contents could not be extracted. """
    pass

class NoPersonnelException(Exception):
    """ Exception raised when page contents could not be extracted. """
    pass