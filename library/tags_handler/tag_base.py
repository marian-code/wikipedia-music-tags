from abc import ABC, abstractmethod
from collections import OrderedDict


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
