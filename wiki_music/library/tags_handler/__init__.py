"""Low level tags handling implementation based on mutagen library."""

import logging
from typing import TYPE_CHECKING, Type, Union
from pathlib import Path

from wiki_music.utilities import exception, UnsupportedFileType

# TODO does not work, not sure why? gives wird attribute errors
# from lazy_import import lazy_callable
# TagMp3 = lazy_callable("wiki_music.library.tags_handler.mp3.TagMp3")
# TagFlac = lazy_callable("wiki_music.library.tags_handler.flac.TagFlac")
# TagM4a = lazy_callable("wiki_music.library.tags_handler.m4a.TagM4a")


if TYPE_CHECKING:
    from .tag_base import TagBase

log = logging.getLogger(__name__)

__all__ = ["File"]


def File(filename: Union[str, Path]) -> "TagBase":
    """Class factory which returns coresponding class based on file type.

    Note
    ----
    Currently supported types are: mp3, flac, m4a

    Raises
    ------
    UnsupportedFileType
        if file is not one of supported types

    Returns
    -------
    TagBase
        one of the low level tag handling classes
    """
    if isinstance(filename, str):
        filename = Path(filename)

    if filename.suffix.endswith("mp3"):
        from .mp3 import TagMp3
        return TagMp3(filename)
    elif filename.suffix.endswith("flac"):
        from .flac import TagFlac
        return TagFlac(filename)
    elif filename.suffix.endswith("m4a"):
        from .m4a import TagM4a
        return TagM4a(filename)
    else:
        e = (f"Tagging for {filename.suffix} files is not implemented")
        raise UnsupportedFileType(e)
