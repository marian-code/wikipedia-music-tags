""" Low level tags handling implementation based on mutagen library. """

from lazy_import import lazy_callable
from typing import TYPE_CHECKING, Type

from wiki_music.utilities import SharedVars, log_tags, exception

TagMp3 = lazy_callable("wiki_music.library.tags_handler.mp3.TagMp3")
TagFlac = lazy_callable("wiki_music.library.tags_handler.flac.TagFlac")
TagM4a = lazy_callable("wiki_music.library.tags_handler.m4a.TagM4a")

if TYPE_CHECKING:
    from wiki_music.library.tags_handler.tag_base import TagBase


@exception(log_tags)
def File(filename: str) -> Type["TagBase"]:
    """ Class factory function which returns coresponding class based on file
    type.

    Note
    ----
    Currently supported types are: mp3, flac, m4a

    Raises
    ------
    NotImplementedError
        if file is not one of supported types

    Returns
    -------
    TagBase
        one of the low level tag handling classes
    """

    if filename.lower().endswith(".mp3"):
        return TagMp3(filename)
    elif filename.lower().endswith(".flac"):
        return TagFlac(filename)
    elif filename.lower().endswith(".m4a"):
        return TagM4a(filename)
    else:
        e = (f"Tagging for {filename.rsplit('.', 1)[1]} files is not "
             f"implemented")
        raise NotImplementedError(e)
