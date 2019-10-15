"""Module for handling m4a tags."""

import logging
from collections import OrderedDict
from typing import Dict, Union, cast

from mutagen.mp4 import MP4, MP4Cover, MP4MetadataError

from .tag_base import TagBase

log = logging.getLogger(__name__)
log.debug("loading m4a module")


class TagM4a(TagBase):
    """A low level implementation of tag handling for m4a files. """
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

    def _open(self, filename: str):
        """Function reading m4a file to mutagen.mp4.MP4 class. """

        try:
            self._song = MP4(filename=filename)
        except MP4MetadataError:
            print("Cannot read MP4 tags")

    def _read(self) -> Dict[str, Union[str, bytearray]]:

        tags = dict()
        for key, value in self._map_keys.items():  # pylint: disable=no-member
            try:
                tag = self._song.tags[key]
                if isinstance(tag, list):
                    tag = tag[0]
                if value in ("DISCNUMBER", "TRACKNUMBER"):
                    tag = tag[0]
                if value != "COVERART":
                    tag = str(tag).strip()
            except KeyError:
                tag = ""
            finally:
                tags[value] = tag

        return tags

    def _write(self, tag: str, value: Union[str, bytearray]):

        if tag in ("DISCNUMBER", "TRACKNUMBER"):
            value = [[int(value), 0]]  # type: ignore
        elif tag == "COVERART":
            value = [MP4Cover(value, imageformat=MP4Cover.FORMAT_JPEG)]  # type: ignore

        self._song.tags[self.reverse_map[tag]] = value
