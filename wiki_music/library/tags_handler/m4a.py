"""Module for handling m4a tags."""

import logging
from collections import OrderedDict
from typing import TYPE_CHECKING, Dict, Union, cast

from mutagen.mp4 import MP4, MP4Cover, MP4MetadataError

from .tag_base import TagBase

if TYPE_CHECKING:
    from pathlib import Path

log = logging.getLogger(__name__)
log.debug("loading m4a module")

__all__ = ["TagM4a"]


class TagM4a(TagBase):
    """A low level implementation of tag handling for m4a files."""

    __doc__ += TagBase.__doc__  # type: ignore

    _map_keys = OrderedDict([
        ("\xa9alb", "ALBUM"),
        ("aART", "ALBUMARTIST"),
        ("\xa9ART", "ARTIST"),
        ("\xa9cmt", "COMMENT"),
        ("\xa9wrt", "COMPOSER"),
        ("\xa9day", "DATE"),
        ("disk", "DISCNUMBER"),
        ("\xa9gen", "GENRE"),
        ("\xa9lyr", "LYRICS"),
        ("\xa9nam", "TITLE"),
        ("trkn", "TRACKNUMBER"),
        ("covr", "COVERART")]
    )

    def _open(self, filename: "Path"):
        """Function reading m4a file to mutagen.mp4.MP4 class."""
        try:
            self._song = MP4(filename=filename)
        except MP4MetadataError:
            log.warning("Cannot read MP4 tags")

    def _read(self) -> Dict[str, Union[str, bytes]]:

        tags = dict()
        for key, value in self._map_keys.items():  # pylint: disable=no-member
            try:
                tag = self._song.tags[key]
                if value in ("DISCNUMBER", "TRACKNUMBER"):
                    tag = tag[0]

            except KeyError:
                tag = self._get_default_tag(value)
            finally:
                tags[value] = self._process_tag(tag)

        return tags

    def _write(self, tag: str, value: Union[str, bytes]):

        if tag in ("DISCNUMBER", "TRACKNUMBER"):
            value = [[int(value), 0]]  # type: ignore
        elif tag == "COVERART":
            fmt = MP4Cover.FORMAT_JPEG
            value = [MP4Cover(value, imageformat=fmt)]  # type: ignore

        self._song.tags[self.reverse_map[tag]] = value
