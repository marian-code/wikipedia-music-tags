from mutagen.flac import FLAC, FLACNoHeaderError
from mutagen.id3 import (ID3, TALB, TCOM, TCON, TDRC, TIT2, TPE1, TPE2, TPOS,
                         TRCK, USLT, ID3NoHeaderError)
from mutagen.mp4 import MP4, MP4MetadataError

from collections import OrderedDict
from abc import ABC, abstractmethod
from utilities.loggers import log_tags
from utilities.sync import SharedVars


def File(filename):

    if filename.lower().endswith(".mp3"):
        return TagMp3(filename)
    elif filename.lower().endswith(".flac"):
        return TagFlac(filename)
    elif filename.lower().endswith(".m4a"):
        return TagM4a(filename)
    else:
        e = (f"Tagging for {filename.rsplit(".", 1)[1]} files is not "
             f"implemented")
        SharedVars.exception = e
        log_tags.exception(e)
        raise NotImplementedError(e)


class TagBase(ABC):

    def __init__(self):

        self.song = None
        self._tags = None

    # TODO only write changes not everything
    def save(self):

        for tag, value in self._tags.items():
            self._write(tag, value)

        self.song.save()

    @abstractmethod
    def _read(self):
        raise NotImplementedError("Call to abstarct method!")

    @abstractmethod
    def _write(self, tag, value):
        raise NotImplementedError("Call to abstarct method!")

    @abstractmethod
    def _open(self, filename):
        raise NotImplementedError("Call to abstarct method!")

    @property
    def tags(self):

        if self._tags is None:
            self._tags = self._read()

        return self._tags

    @staticmethod
    def get_reversed(map_keys):

        reverse_map = OrderedDict()

        for key, value in map_keys.items():
            reverse_map[value] = key

        return reverse_map


class TagMp3(TagBase):

    def __init__(self, filename):

        super().__init__()

        self._open(filename)

        self.map_keys = OrderedDict([
            ("TALB", "ALBUM"),
            ("TPE2", "ALBUMARTIST"),
            ("TPE1", "ARTIST"),
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
                tag = self.song[key].text
                if not isinstance(tag, list):
                    tag = [tag]
            except KeyError:
                tag = ""
            finally:
                tags[value] = tag

        return tags

    def _write(self, tag, value):

        tag_cls = self.reverse_map[tag]

        self.song[tag_cls] = self.map_clacsses[tag_cls](encoding=3, text=value)


class TagFlac(TagBase):

    def __init__(self, filename):

        super().__init__()

        self._open(filename)

        self.map_keys = OrderedDict([
            ("album", "ALBUM"),
            ("albumartist", "ALBUMARTIST"),
            ("artist", "ARTIST"),
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
                if not isinstance(tag, list):
                    tag = [tag]
            except KeyError:
                tag = ""
            finally:
                tags[value] = tag

        return tags

    def _write(self, tag, value):

        self.song.tags[self.reverse_map[tag]] = value


class TagM4a(TagBase):

    def __init__(self, filename):

        super().__init__()

        self._open(filename)

        self.map_keys = OrderedDict([
            ("\xa9alb", "ALBUM"),
            ("aART", "ALBUMARTIST"),
            ("\xa9ART", "ARTIST"),
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
                if not isinstance(tag, list):
                    tag = [tag]
            except KeyError:
                tag = ""
            finally:
                tags[value] = tag

        return tags

    def _write(self, tag, value):

        self.song.tags[self.reverse_map[tag]] = value


if __name__ == "__main__":

    print("mp4---------------------------------------------------------------")

    s = File("Aventine.m4a")
    s.tags["ALBUM"] = "hovno m4aaaa"
    s.save()

    print(s.tags)

    print("flac--------------------------------------------------------------")

    s = File("Aventine.flac")
    s.tags["ALBUM"] = "hovno flac"
    s.save()
    print(s.tags)

    print("mp3---------------------------------------------------------------")

    s = File("Aventine.mp3")
    s.tags["ALBUM"] = "hovno mp3"
    s.save()
    print(s.tags)

