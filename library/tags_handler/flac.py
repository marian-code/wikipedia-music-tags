from collections import OrderedDict

from mutagen.flac import FLAC, FLACNoHeaderError

from .tag_base import TagBase


class TagFlac(TagBase):

    def __init__(self, filename):

        super().__init__()

        self._open(filename)

        self.map_keys = OrderedDict([
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
            ("tracknumber", "TRACKNUMBER")]
        )

        self.reverse_map = self.get_reversed(self.map_keys)

    def _open(self, filename):

        try:
            self.song = FLAC(filename=filename)
        except FLACNoHeaderError:
            print("Cannot read FLAC tags")

    def _read(self):

        tags = dict()
        for key, value in self.map_keys.items():
            try:
                tag = self.song.tags[key]
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

        self.song.tags[self.reverse_map[tag]] = value
