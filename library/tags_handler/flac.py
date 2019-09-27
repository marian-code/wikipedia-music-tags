from collections import OrderedDict
from typing import Dict, Union

from mutagen.flac import FLAC, FLACNoHeaderError, Picture
from mutagen.id3 import PictureType

from .tag_base import TagBase


class TagFlac(TagBase):

    map_keys = OrderedDict([
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

    def __init__(self, filename: str):

        super().__init__(filename)

    def _open(self, filename: str):

        try:
            self.song = FLAC(filename=filename)
        except FLACNoHeaderError:
            print("Cannot read FLAC tags")

    def _read(self) -> Dict[str, Union[str, bytearray]]:

        tags = dict()
        for key, value in self.map_keys.items():
            try:
                if key == "picture":
                    tag = self.song.pictures[0].data
                    continue
                else:
                    tag = self.song.tags[key]
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
            self.song.clear_pictures()
            self.song.add_picture(pic)
        else:
            self.song.tags[self.reverse_map[tag]] = value
