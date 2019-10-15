"""Module for handling flac tags."""

import logging
from collections import OrderedDict
from typing import Dict, Union

from mutagen.flac import FLAC, FLACNoHeaderError, Picture
from mutagen.id3 import PictureType

from .tag_base import TagBase

log = logging.getLogger(__name__)
log.debug("loading flac module")


class TagFlac(TagBase):
    """A low level implementation of tag handling for flac files. """
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

    def _open(self, filename: str):
        """Function reading flac file to mutagen.flac.FLAC class. """

        try:
            self._song = FLAC(filename=filename)
        except FLACNoHeaderError:
            print("Cannot read FLAC tags")

    def _read(self) -> Dict[str, Union[str, bytearray]]:

        tags = dict()
        for key, value in self._map_keys.items():  # pylint: disable=no-member
            try:
                if key == "picture":
                    tag = self._song.pictures[0].data
                    continue
                else:
                    tag = self._song.tags[key]
                    if isinstance(tag, list):
                        tag = tag[0]
                    tag = str(tag).strip()
            except (KeyError, AttributeError):
                tag = ""
            finally:
                tags[value] = tag

        return tags

    def _write(self, tag: str, value: Union[str, bytearray]):

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
            self._song.tags[self.reverse_map[tag]] = value
