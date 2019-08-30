from collections import OrderedDict

from mutagen.mp4 import MP4, MP4MetadataError

from .tag_base import TagBase


class TagM4a(TagBase):

    def __init__(self, filename):

        super().__init__()

        self._open(filename)

        self.map_keys = OrderedDict([
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
            ("trkn", "TRACKNUMBER")]
        )

        self.reverse_map = self.get_reversed(self.map_keys)

    def _open(self, filename):

        try:
            self.song = MP4(filename=filename)
        except MP4MetadataError:
            print("Cannot read MP4 tags")

    def _read(self):

        tags = dict()
        for key, value in self.map_keys.items():
            try:
                tag = self.song.tags[key]
                if isinstance(tag, list):
                    tag = tag[0]
                if value in ("DISCNUMBER", "TRACKNUMBER"):
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

        if tag in ("DISCNUMBER", "TRACKNUMBER"):
            value = [[int(value), 0]]

        self.song.tags[self.reverse_map[tag]] = value