import collections
from abc import ABC, abstractmethod
from typing import Dict, ClassVar, Optional


class SelectiveDict(dict):
    """ A subclass of a dictionary with capacity to remember which keys are
    being changed. This is archieved by simply overriding the __setitem__
    method.

    Attributes
    ----------
    writable: set
        a set of keys(tags) that were changed, and should be written to file
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.writable = set()

    def __getitem__(self, key):
        val = super().__getitem__(key)
        return val

    def __setitem__(self, key, val):
        """ Altered magic method which caches the changed keys names.
        
        Parameters
        ----------
        key: str
            dictionary key (tag name)
        val: Any
            dictionary value (tag value)
        """

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
        """ Method simillar to dict.items() method only this one loops
        through key-value pairs that have changed since the creation of
        this dictionary instance.
        """

        for key, val in super().items():
            if key in self.writable:
                yield key, val


class TagBase(ABC):
    """

    Attributes
    ----------
    _map_keys: dict
        a maping between highlevel tag names and lowlevel tag names used by
        mutagen impementation of tags for specific file type
    _reverse_map: dict
        reversed `_map_keys` dictionary
    _tags: Selective_dict
        private attribute which caches the read tags and records any occuring
        changes, it is exposed in class API through tags property

    See also
    --------
    :class:`wiki_music.library.tags_handler.tag_base.SelectiveDict`
        a subclass of a dictionary in which tags are stored, does remember
        changes in tags, so only the changed tags can be written
    :const:`wiki_music.constants.tags.TAGS`
        for list of supported tags

    Parameters
    ----------
    filename: str
        path to song file with tags
    """

    __doc__: Optional[str]
    _map_keys: ClassVar[Dict[str, str]]
    reverse_map: Dict[str, str]
    _tags: SelectiveDict

    def __init__(self, filename):

        self._song = None
        self._tags = None

        self.reverse_map = self._get_reversed(self._map_keys)

        self._open(filename)

    def save(self):
        """ Writes tags to song file and than calls the save function, to save
        to disk.
        """

        for tag, value in self._tags.save_items():
            self._write(tag, value)

        self._song.save()

    @abstractmethod
    def _read(self):
        """ Reads tags from an open mutagen file to dictionary as key-value
        pairs. Tries to avoid all the pitfalls of different tag formats.

        Returns
        -------
        dict
            dictionary of tag names and values
        """
        raise NotImplementedError("Call to abstarct method!")

    @abstractmethod
    def _write(self, tag, value):
        """ Given a high level tag name, convert it to low level name and write
        to file tags."""
        raise NotImplementedError("Call to abstarct method!")

    @abstractmethod
    def _open(self, filename):
        """ Method that reads in the file frim location suplied by filename
        argument. see subclasses for specific implementation.
        """
        raise NotImplementedError("Call to abstarct method!")

    @property
    def tags(self):
        """ Propery which is used to access the read tags. If the tags are not
        present it reads them from a suplied file and casts them from
        dictionary to SelectiveDict type to record occured changes

        Returns
        -------
        SelectiveDict
            dictionary containing tag labes and their values 
        """

        if not self._tags:
            self._tags = self._read()

        # for reading tags we use standard dict but we expose to outer
        # world the SelectiveDict class to record occured changes
        if not isinstance(self._tags, SelectiveDict):
            self._tags = SelectiveDict(self._tags)

        return self._tags

    @staticmethod
    def _get_reversed(_map_keys: Dict[str, str]) -> Dict[str, str]:
        """ Given a dictionary of [keys, values] it returns a reversed version
        with [values, key] while preserving order of items if is an instance
        of collections.OderedDict.

        Returns
        -------
        dict
            dictionary with switched keys and values
        """

        reverse_map: Dict[str, str] = collections.OrderedDict()

        for key, value in _map_keys.items():
            reverse_map[value] = key

        return reverse_map
