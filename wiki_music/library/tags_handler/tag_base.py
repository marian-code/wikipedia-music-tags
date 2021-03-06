"""Base module for all tag handlers."""

import collections
import logging
import re
from abc import ABC, abstractmethod
from typing import (ClassVar, Dict, List, Optional, Union, Callable,
                    TYPE_CHECKING)
from wiki_music.constants.tags import LIST_TAGS

if TYPE_CHECKING:
    from pathlib import Path


logging.getLogger(__name__)

__all__ = ["TagBase"]


class SelectiveDict(dict):
    """A subclass of a dictionary which remembers which keys are being changed.

    Behaviur is archieved by simply overriding the __setitem__ method.

    Attributes
    ----------
    writable: set
        a set of keys(tags) that were changed, and should be written to file
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.writable = set()

    def __setitem__(self, key, val):
        """Altered magic method which caches the changed keys names.

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
        """Method simillar to dict.items().

        Difference if this method loops through key-value pairs that have
        changed since the creation of this dictionary instance.
        """
        for key, val in super().items():
            if key in self.writable:
                yield key, val

    def to_dict(self):
        """Cast contents of selective dict to dict.

        Returns
        -------
        dict
            tags dictionary
        """
        return dict(self)


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
    :class:`SelectiveDict`
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
    _reverse_map: Dict[str, Union[str, Callable]]
    _tags: SelectiveDict

    def __init__(self, filename: "Path") -> None:

        self._song = None
        self._tags = None

        self._reverse_map = self._get_reversed(self._map_keys)

        self._open(filename)

    def save(self):
        """Write tags to song file and than save to disk."""
        for tag, value in self._tags.save_items():

            # lists must joined before writing,
            # otherwise results are inconsistent
            if isinstance(value, list):
                if len(value) == 1:
                    value = value[0]
                else:
                    value = ", ".join(value)

            self._write(tag, value)

        self._song.save()

    @abstractmethod
    def _read(self):
        """Reads tags from an open mutagen file to dictionary.

        Tags are stored as key-value pairs. Tries to avoid all the pitfalls
        of different tag formats.

        Returns
        -------
        dict
            dictionary of tag names and values
        """
        raise NotImplementedError("Call to abstarct method!")

    @abstractmethod
    def _write(self, tag, value):
        """Write single tag to file.

        Converts high level tag name, to low level which is specific for
        each implementation and write to file tags.
        """
        raise NotImplementedError("Call to abstarct method!")

    @abstractmethod
    def _open(self, filename):
        """Reads in the file from location suplied by filename argument.

        See subclasses for specific implementation.
        """
        raise NotImplementedError("Call to abstarct method!")

    @property
    def tags(self) -> SelectiveDict:
        """Reads and returns file tags.

        If the tags are present it reads them from a suplied file and casts
        them from dictionary to SelectiveDict type to record occured changes.

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
    def _get_reversed(map_keys: Dict[str, str]
                      ) -> Dict[str, Union[str, Callable]]:
        """Swaps keys and values in dictionary.

        Given a dictionary of [keys, values] it returns a reversed version
        with [values, key] while preserving order of items if is an instance
        of collections.OderedDict.

        Returns
        -------
        dict
            dictionary with switched keys and values
        """
        _reverse_map: Dict[str, str] = collections.OrderedDict()

        for key, value in map_keys.items():
            _reverse_map[value] = key

        return _reverse_map

    @staticmethod
    def _get_default_tag(tag_name: str) -> Union[bytes, str, list]:
        """Return default value with corret type for each supported tag.
        
        Parameters
        ----------
        tag_name: str
            name of the tag which default value is desired
        """
        if tag_name == "COVERART":
            return bytes()
        elif tag_name in LIST_TAGS:
            return [""]
        else:
            return ""

    @staticmethod
    def _process_tag(tag_name: str, tag: List) -> Union[bytes, str, list]:
        """Postprocessing of each tag based on its expected type.

        Parameters
        ----------
        tag: List[Any]
            tag or a list of tags to be processed
        tag_name: str
            string identifying tag
        """
        def rm_pref_comma(string: str) -> str:
            """Remove comma from the string begining."""
            return re.sub(r"^ ?, ?", "", string.strip())

        if tag_name not in LIST_TAGS:
            try:
                tag = tag[0]
            except IndexError:
                pass
            if isinstance(tag, str):
                tag = rm_pref_comma(tag)
            return tag
        else:
            if len(tag) == 1:
                tag = tag[0].split(",")
            return [rm_pref_comma(t) for t in tag if t not in ("", " ", None)]
