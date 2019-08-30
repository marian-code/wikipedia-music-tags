from ast import literal_eval
from collections import OrderedDict

from mutagen.id3 import (COMM, ID3, TALB, TCOM, TCON, TDRC, TIT2, TPE1, TPE2,
                         TPOS, TRCK, USLT, ID3NoHeaderError)

from .tag_base import TagBase


class TagMp3(TagBase):

    def __init__(self, filename):

        super().__init__()

        self._open(filename)

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
            ("TRCK", "TRACKNUMBER")]
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
            "TRCK": TRCK
        }

        self.reverse_map = self.get_reversed(self.map_keys)

    def _open(self, filename):

        try:
            self.song = ID3(filename=filename)
        except ID3NoHeaderError:
            print("Cannot read Mp3 tags")

    def _read(self):

        tags = dict()
        for key, value in self.map_keys.items():
            try:
                # lyrics key is formated like: USLT::xxx
                # where xxx designates language
                if key == "USLT::eng":
                    for k in self.song.keys():
                        if "USLT" in k:
                            key = k
                            break
                    # lyrics tag field returns literal string
                    # slicing removes brackets at the ends
                    tag = literal_eval(self.song[key].text)
                else:
                    tag = self.song[key].text

                if isinstance(tag, list):
                    tag = tag[0]
                tag = str(tag).strip()

            except KeyError:
                tag = ""
            finally:
                tags[value] = [tag]

        tags["UNSYNCEDLYRICS"] = tags["LYRICS"]

        return tags

    def _write(self, tag, value):

        if tag == "UNSYNCEDLYRICS":
            tag = "LYRICS"

        tag_cls = self.reverse_map[tag]

        self.song[tag_cls] = self.map_clacsses[tag_cls](encoding=3, text=value)
