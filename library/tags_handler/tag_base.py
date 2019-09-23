from abc import ABC, abstractmethod
from collections import OrderedDict
from os.path import join, split
from wiki_music.constants.tags import TAGS


class SelectiveDict(dict):

    def __init__(self, *args):
        super().__init__(*args)
        self.writable = set()

    def __getitem__(self, key):
        val = super().__getitem__(key)
        return val

    def __setitem__(self, key, val):

        try:
            old_val = super().__getitem__(key)
        except KeyError:
            self.writable.add(key)
        else:
            if old_val != val:
                self.writable.add(key)
        finally:
            super().__setitem__(key, val)

    def save_items(self):
        for key, val in super().items():
            if key in self.writable:
                yield key, val


class TagBase(ABC):

    map_keys: dict  # noqa E701

    def __init__(self, filename):

        self.song = None
        self._tags = None

        # ensure we are consistent with package defined tags
        assert sorted(self.map_keys.values()) == sorted(TAGS + ("COMMENT",))

        self.reverse_map = self.get_reversed(self.map_keys)

        self._open(filename)

    def save(self):

        for tag, value in self._tags.save_items():
            self._write(tag, value)

        # for key, value in self.song.tags.items():
        #    if key in self.map_keys:
        #        print(f"{key}: {value}")

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

        if not self._tags:
            self._tags = self._read()

        # for reading tags we use standard dict but we expose to outer
        # world the SelectiveDict class to record occured changes
        if not isinstance(self._tags, SelectiveDict):
            self._tags = SelectiveDict(self._tags)

        return self._tags

    @staticmethod
    def get_reversed(map_keys):

        reverse_map = OrderedDict()

        for key, value in map_keys.items():
            reverse_map[value] = key

        return reverse_map
