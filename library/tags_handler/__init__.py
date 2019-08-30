from lazy_import import lazy_callable

from utilities.loggers import log_tags
from utilities.sync import SharedVars

TagMp3 = lazy_callable("library.tags_handler.mp3.TagMp3")
TagFlac = lazy_callable("library.tags_handler.flac.TagFlac")
TagM4a = lazy_callable("library.tags_handler.m4a.TagM4a")


def File(filename):

    if filename.lower().endswith(".mp3"):
        return TagMp3(filename)
    elif filename.lower().endswith(".flac"):
        return TagFlac(filename)
    elif filename.lower().endswith(".m4a"):
        return TagM4a(filename)
    else:
        e = (f"Tagging for {filename.rsplit('.', 1)[1]} files is not "
             f"implemented")
        SharedVars.exception = e
        log_tags.exception(e)
        raise NotImplementedError(e)
