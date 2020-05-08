"""Module for handling mp3 tags."""

import logging
from ast import literal_eval
from collections import OrderedDict
from typing import TYPE_CHECKING, Dict, Union

from mutagen.id3 import (APIC, COMM, ID3, TALB, TCOM, TCON, TDRC, TIT2, TPE1,
                         TPE2, TPOS, TRCK, USLT, ID3NoHeaderError, PictureType)

from .tag_base import TagBase

if TYPE_CHECKING:
    from pathlib import Path

log = logging.getLogger(__name__)
log.debug("loading mp3 module")

__all__ = ["TagMp3"]


class TagMp3(TagBase):
    """A low level implementation of tag handling for mp3 files."""

    __doc__ += TagBase.__doc__  # type: ignore

    _map_keys = OrderedDict([
        (TALB, "ALBUM"),
        (TPE2, "ALBUMARTIST"),
        (TPE1, "ARTIST"),
        (COMM, "COMMENT"),
        (TCOM, "COMPOSER"),
        (TDRC, "DATE"),
        (TPOS, "DISCNUMBER"),
        (TCON, "GENRE"),
        (USLT, "LYRICS"),
        (TIT2, "TITLE"),
        (TRCK, "TRACKNUMBER"),
        (APIC, "COVERART")]
    )

    def _open(self, filename: "Path"):
        """Function reading mp3 file to mutagen.id3.ID3 class."""
        try:
            self._song = ID3(filename=filename)
        except ID3NoHeaderError as e:
            log.warning("Cannot read Mp3 tags")
            log.debug(e)

    @staticmethod
    def _key2str(key):
        """From string like <class 'mutagen.id3.TCOM'> get the name TCOM.

        Returns
        -------
        str
            string reptresentation of mutagen.ID3 class tag name
        """
        return str(key).rsplit(".", 1)[1][:-2]

    def _read(self) -> Dict[str, Union[str, bytes]]:

        tags = dict()
        for key, value in self._map_keys.items():  # pylint: disable=no-member
            frame = self._song.getall(self._key2str(key))
            try:
                if value == "COVERART":
                    tag = frame[0].data
                else:
                    tag = frame[0].text
                    if value == "LYRICS":
                        tag = [tag]

            except IndexError:
                tag = self._get_default_tag(value)
            finally:
                tags[value] = self._process_tag(value, tag)

        return tags

    def _write(self, tag: str, value: Union[str, bytes]):

        if tag == "COVERART":
            try:
                self._song[self._reverse_map[tag]](
                    mime=u"image/jpeg", type=PictureType.COVER_FRONT,
                    desc=u"Cover", data=value, encoding=3)
            except KeyError:
                self._song.add(self._reverse_map[tag](
                    mime=u"image/jpeg", type=PictureType.COVER_FRONT,
                    desc=u"Cover", data=value, encoding=3))
                log.warning(f"Couldn't find tag {tag}: "
                            f"{self._reverse_map[tag]}")
        else:
            # if tag is not present add it
            try:
                self._song[self._reverse_map[tag]](encoding=3, text=value)
            except KeyError:
                self._song.add(self._reverse_map[tag](encoding=3, text=value))
                log.warning(f"Couldn't find tag {tag}: "
                            f"{self._reverse_map[tag]}")
