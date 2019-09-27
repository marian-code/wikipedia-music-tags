from collections import OrderedDict
from typing import Dict, Union, cast

from mutagen.mp4 import MP4, MP4Cover, MP4MetadataError

from wiki_music.constants.tags import TAGS

from .tag_base import TagBase


class TagM4a(TagBase):

    map_keys = OrderedDict([
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

    def __init__(self, filename: str):

        super().__init__(filename)

    def _open(self, filename: str):

        try:
            self.song = MP4(filename=filename)
        except MP4MetadataError:
            print("Cannot read MP4 tags")

    def _read(self) -> Dict[str, Union[str, bytearray]]:

        tags = dict()
        for key, value in self.map_keys.items():
            try:
                tag = self.song.tags[key]
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

        self.song.tags[self.reverse_map[tag]] = value
