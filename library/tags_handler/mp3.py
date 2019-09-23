from ast import literal_eval
from collections import OrderedDict

from mutagen.id3 import (APIC, COMM, ID3, TALB, TCOM, TCON, TDRC, TIT2, TPE1,
                         TPE2, TPOS, TRCK, USLT, ID3NoHeaderError, PictureType)

from .tag_base import TagBase


class TagMp3(TagBase):

    def __init__(self, filename):

        self.map_keys = OrderedDict([
            ("TALB", "ALBUM"),
            ("TPE2", "ALBUMARTIST"),
            ("TPE1", "ARTIST"),
            ("COMM", "COMMENT"),
            ("TCOM", "COMPOSER"),
            ("TDRC", "DATE"),
            ("TPOS", "DISCNUMBER"),
            ("TCON", "GENRE"),
            ("USLT::eng", "LYRICS"),
            ("TIT2", "TITLE"),
            ("TRCK", "TRACKNUMBER"),
            ("APIC", "COVERART")]
        )

        self.map_clacsses = {
            "TALB": TALB,
            "TPE2": TPE2,
            "TPE1": TPE1,
            "COMM": COMM,
            "TCOM": TCOM,
            "TDRC": TDRC,
            "TPOS": TPOS,
            "TCON": TCON,
            "USLT::eng": USLT,
            "TIT2": TIT2,
            "TRCK": TRCK,
            "APIC": APIC
        }

        super().__init__(filename)

    def _open(self, filename):

        try:
            self.song = ID3(filename=filename)
        except ID3NoHeaderError:
            print("Cannot read Mp3 tags")

    def _find_variable_key(self, tag):

        tag = self.reverse_map[tag].split(":")[0]

        for k in self.song.keys():
            if tag in k:
                return k

    def _read(self):

        tags = dict()
        for key, value in self.map_keys.items():
            try:
                # lyrics key is formated like: USLT::xxx
                # where xxx designates language
                if value == "LYRICS":
                    key = self._find_variable_key(value)
                    # lyrics tag field returns literal string
                    # slicing removes brackets at the ends
                    tag = literal_eval(self.song[key].text)
                elif value == "COVERART":
                    key = self._find_variable_key(value)
                    tag = self.song[key].data
                    continue
                else:
                    tag = self.song[key].text

                if isinstance(tag, list):
                    tag = tag[0]
                tag = str(tag).strip()

            except KeyError:
                tag = ""
            finally:
                tags[value] = tag

        return tags

    def _write(self, tag, value):

        tag_cls = self.reverse_map[tag]

        if tag == "COVERART":
            self.song[tag_cls] = self.map_clacsses[tag_cls](
                mime=u"image/jpeg", type=PictureType.COVER_FRONT,
                desc=u"Cover", data=value, encoding=3)
        else:
            self.song[tag_cls] = self.map_clacsses[tag_cls](encoding=3,
                                                            text=value)
