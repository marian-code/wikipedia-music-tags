"""Module for handling flac tags."""

import logging
from collections import OrderedDict
from typing import TYPE_CHECKING, Dict, Union

from mutagen.flac import FLAC, FLACNoHeaderError, Picture
from mutagen.id3 import PictureType

from .tag_base import TagBase

if TYPE_CHECKING:
    from pathlib import Path

log = logging.getLogger(__name__)
log.debug("loading flac module")

__all__ = ["TagFlac"]


class TagFlac(TagBase):
    """A low level implementation of tag handling for flac files."""

    __doc__ += TagBase.__doc__  # type: ignore

    _map_keys = OrderedDict([
        ("album", "ALBUM"),
        ("albumartist", "ALBUMARTIST"),
        ("artist", "ARTIST"),
        ("comment", "COMMENT"),
        ("composer", "COMPOSER"),
        ("date", "DATE"),
        ("discnumber", "DISCNUMBER"),
        ("genre", "GENRE"),
        ("lyrics", "LYRICS"),
        ("title", "TITLE"),
        ("tracknumber", "TRACKNUMBER"),
        ("picture", "COVERART")]
    )

    def _open(self, filename: "Path"):
        """Function reading flac file to mutagen.flac.FLAC class."""
        try:
            self._song = FLAC(filename=filename)
        except FLACNoHeaderError as e:
            log.warning("Cannot read FLAC tags")
            log.debug(e)

    def _read(self) -> Dict[str, Union[str, bytes]]:

        tags = dict()
        for key, value in self._map_keys.items():  # pylint: disable=no-member
            try:
                if key == "picture":
                    try:
                        tag = [self._song.pictures[0].data]
                    except IndexError:
                        raise KeyError("No cover art in file")
                else:
                    tag = self._song.tags[key]

            except (KeyError, AttributeError):
                tag = self._get_default_tag(value)
            finally:
                tags[value] = self._process_tag(value, tag)

        return tags

    def _write(self, tag: str, value: Union[str, bytes]):

        if tag == "COVERART":

            pic = Picture()
            pic.type = PictureType.COVER_FRONT
            pic.mime = "image/jpeg"
            pic.data = value
            pic.desc = "Front Cover"

            # first we have to delete previous pictures and then write new
            self._song.clear_pictures()
            self._song.add_picture(pic)
        else:
            self._song.tags[self._reverse_map[tag]] = value
