from ast import literal_eval
from collections import OrderedDict
from typing import Dict, Union

from mutagen.id3 import (APIC, COMM, ID3, TALB, TCOM, TCON, TDRC, TIT2, TPE1,
                         TPE2, TPOS, TRCK, USLT, ID3NoHeaderError, PictureType)

from .tag_base import TagBase


class TagMp3(TagBase):
    """ A low level implementation of tag handling for mp3 files. """
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

    def _open(self, filename: str):
        """ Function reading mp3 file to mutagen.id3.ID3 class. """

        try:
            self._song = ID3(filename=filename)
        except ID3NoHeaderError:
            print("Cannot read Mp3 tags")

    def _find_variable_key(self, tag: str) -> str:
        """ Sometimes the key in tags is appended with some string like
        USTL::eng this functions finds the specific key if supliedd with the
        common prefix.

        Returns
        -------
        str
            mutagen.ID3 tag name
        """

        tag = self.reverse_map[tag]

        for k in self._song.keys():
            if tag in k:
                return self._key2str(k)

        return ""

    @staticmethod
    def _key2str(key):
        """ get from string like <class 'mutagen.id3.TCOM'> the name TCOM.

        Returns
        -------
        str
            string reptresentation of mutagen.ID3 class tag name
        """
        return str(key).rsplit(".", 1)[1][:-2]

    def _read(self) -> Dict[str, Union[str, bytearray]]:

        tags = dict()
        for key, value in self._map_keys.items():  # pylint: disable=no-member
            key = self._key2str(key)
            try:
                # lyrics key is formated like: USLT::xxx
                # where xxx designates language
                if value == "LYRICS":
                    key = self._find_variable_key(value)
                    # lyrics tag field returns literal string
                    tag = literal_eval(self._song[key].text)
                elif value == "COVERART":
                    key = self._find_variable_key(value)
                    tag = self._song[key].data
                    continue
                else:
                    tag = self._song[key].text

                if isinstance(tag, list):
                    tag = tag[0]
                tag = str(tag).strip()

            except KeyError:
                tag = ""
            finally:
                tags[value] = tag

        return tags

    def _write(self, tag: str, value: Union[str, bytearray]):

        if tag == "COVERART":
            self._song[self.reverse_map[tag]](
                mime=u"image/jpeg", type=PictureType.COVER_FRONT,
                desc=u"Cover", data=value, encoding=3)
        else:
            self._song[self.reverse_map[tag]](encoding=3, text=value)
