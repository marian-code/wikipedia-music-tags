"""Utility functions and classes used by parser."""

import collections  # lazy loaded
import logging
import os
import sys
import time  # lazy loaded
from threading import Lock, Thread
from typing import (TYPE_CHECKING, Any, Callable, Dict, Generator, List,
                    Optional, Tuple, Union)

import fuzzywuzzy.fuzz as fuzz  # lazy loaded
import yaml  # lazy loaded

from wiki_music.constants.colors import GREEN, RESET

from .utils import normalize
from .sync import SharedVars

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from logging import Logger

__all__ = ["ThreadWithTrace", "NLTK", "bracket", "write_roman",
           "normalize", "normalize_caseless", "caseless_equal",
           "caseless_contains", "count_spaces", "yaml_dump",
           "complete_N_dim", "replace_N_dim", "delete_N_dim",
           "ThreadPool", "yaml_load", "ThreadWithReturn"]


class ThreadWithTrace(Thread):
    """Subclass of threading.thread, sets trace to thread by means of which
    it can be later killed from outside

    Parameters
    ----------
    args: Any
        same as threading.Thread
    kwargs: Any
        same as threading.Thread

    References
    ----------
    https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
    """

    def __init__(self, *args, **keywords) -> None:
        Thread.__init__(self, *args, **keywords)
        self.killed: bool = False

    def start(self):
        self.__run_backup = self.run
        self.run = self.__run
        Thread.start(self)

    def __run(self):
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, event, arg):
        if event == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, event, arg):
        if self.killed:
            if event == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True


class _NltkMeta(type):
    """Metaclass which defines thread safe nltk property. Only for use in
    NLTK class.

    See Also
    --------
    :class:`NLTK`
    """

    @property
    def nltk(cls):
        """Thread safe property which holds reference to nltk lib.

        :type: nltk
        """
        with cls._lock:
            return cls._nltk


class NLTK(metaclass=_NltkMeta):
    """A thread safe nltk importer.

    Will make other threads wait if they want to access nltk
    until it is imported.
    """

    _import_running: bool = False
    # nltk class attribute is provided by metaclass
    _nltk = None
    _lock: Lock = Lock()

    @classmethod
    def run_import(cls, logger: "Logger"):
        """Import nltk in separate thread and assign it to class attribute.

        Parameters
        ----------
        logger: logging.Logger
            instance of a logger to log import messages
        """
        def imp():
            with cls._lock:
                logger.debug("import nltk")
                try:
                    import nltk
                    cls._nltk = nltk
                except ImportError as e:
                    logger.debug(f"failed to import nltk: {e}")
                else:
                    logger.debug("import nltk done")

        if not cls._import_running:

            cls._import_running = True
            # load NLTK in separate thread
            Thread(target=imp, name="ImportNLTK").start()
        else:
            log.debug("nltk import already running")


class ThreadWithReturn(Thread):
    """Subclass of python threading.Thread which can return result of
    running function. The result is return by calling the Thread.join()
    method.

    Parameters
    ----------
    args: Any
        same as threading.Thread
    kwargs: Any
        same as threading.Thread

    References
    ----------
    https://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread-in-python

    See Also
    --------
    :class:`ThreadPool`
    """

    def __init__(self, *args, **kwargs) -> None:
        super(ThreadWithReturn, self).__init__(*args, **kwargs)

        self._return: Any = None

    def run(self):
        """Override standard threading.Thread.run() method to store
        running function return value.
        """

        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, timeout: Optional[float] = None) -> Any:
        """Override standard threading.Thread.join() method to return
        running function return value.
        """

        super(ThreadWithReturn, self).join(timeout=timeout)

        return self._return


class ThreadPool:
    """Spawns pool of threads to excecute function. If the list of arguments
    contains only one tuple, run the function in the calling thread to
    avoid unnecessary overhead as a result of spawning a new thread.

    Parameters
    ----------
    target: Callable
        callable that each thread should run
    args: List[tuple]
        each tuple in list contains args for one thread running target

    See Also
    --------
    :class:`ThreadWithReturn`
    """

    def __init__(self, target: Callable[..., list] = lambda *args: [],
                 args: List[tuple] = [tuple()]) -> None:

        self._args = args
        self._target = target

    def run(self, timeout: Optional[float] = 60) -> list:
        """Starts the execution of threads in pool. returns after all threads
        join() metod has returned.

        See also
        --------
        :meth:`wiki_music.utilities.sync.SharedVars.set_threadpool_prog`
            inform GUI of threadpool progress

        Parameters
        ----------
        timeout: Optional[float]
            timeout after which waiting for results will be abandoned

        Returns
        -------
        list
            list of returned values from the functions run by the ThreadPool
        """

        if len(self._args) == 1:
            return self._target(*self._args)
        else:
            threads: List[ThreadWithReturn] = []

            for i, a in enumerate(self._args):
                threads.append(ThreadWithReturn(target=self._target, args=a,
                                                name=f"ThreadPoolWorker-{i}"))
                threads[-1].daemon = True
                threads[-1].start()

            # report progress to gui
            while True:
                count = [t.is_alive() for t in threads].count(False)
                SharedVars.set_threadpool_prog(count)
                if count == len(threads):
                    break

                time.sleep(0.05)

            for i, l in enumerate(threads):
                threads[i] = l.join(timeout=timeout)

            return threads


def bracket(data: List[str]) -> List[str]:
    """Puts elements of the list in brackets.

    Parameters
    ----------
    data: List[str]
        input data

    Returns
    -------
    List[str]
        list of strings with brackets at the ends
    """

    data_tmp = []
    for d in data:
        if d:
            data_tmp.append("({})".format(d))
        else:
            data_tmp.append("")

    return data_tmp


def write_roman(num: Union[int, str]):
    """Convert integer to roman number.

    Parameters
    ----------
    num: int
        integer to convert to roman number

    References
    ----------
    https://stackoverflow.com/questions/52554702/roman-numerals-to-integers-converter-with-python-using-a-dictionary

    Returns
    -------
    str
        roman number converted from integer
    """

    roman = collections.OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"

    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num <= 0:
                break

    return "".join([a for a in roman_num(num)])


def normalize_caseless(text: str) -> str:
    """NFKD casefold string normalization.

    Parameters
    ----------
    text: str
        string to normalize

    Returns
    -------
    str
        normalized caseless version of string
    """
    return normalize(text).casefold()


def caseless_equal(left: str, right: str) -> bool:
    """Check for normalized string equality.

    Parameters
    ----------
    left: str
        string to compare
    right: str
        string to compare

    Returns
    -------
    bool
        true if normalized caseless strings are equal

    See also
    --------
    :func:`normalize_caseless`
    """
    return normalize_caseless(left) == normalize_caseless(right)


def caseless_contains(string: str, in_text: str) -> bool:
    """Check if string is contained in text.

    Parameters
    ----------
    string: str
        string to search for
    in_text: str
        string to search in

    Returns
    -------
    bool
        True if string is in text

    See also
    --------
    :func:`normalize_caseless`
    """
    if normalize_caseless(string) in normalize_caseless(in_text):
        return True
    else:
        return False


def count_spaces(*lists: Tuple[List[str], ...]) -> Tuple[List[str], int]:
    """Counts max length of elements in list and coresponding spaces for
    each item to fit that length.

    Parameters
    ----------
    lists: Tuple[List[str]]
        data on which to count spaces, all lists in tuple must be of
        same length

    Returns
    -------
    tuple
        list of number os apces to append to list elements to make them span
        max length
    """
    transposed: List[List[str]] = list(map(list, zip(*lists)))
    max_length: int = 0
    spaces: List[str] = []

    for trans in transposed:
        length = sum([len(t) for t in trans])
        if length > max_length:
            max_length = length

    for trans in transposed:
        spaces.append(" " * (max_length - sum([len(t) for t in trans]) + 8))

    return spaces, max_length


def yaml_dump(dict_data: List[Dict[str, str]], save_dir: str):
    """Save yaml tracklist file to disk.

    Parameters
    ----------
    dict_data: List[Dict[str, str]]
        list of dictionarie to save to disk, each dictionary in list contains
        tags of one album track
    save_dir: str
        directory to save to
    """
    path = os.path.join(save_dir, "database.yaml")
    print(GREEN + "\nSaving YAML file: " + RESET + path + "\n")
    with open(path, "w") as f:
        yaml.dump(dict_data, f, default_flow_style=False)


def yaml_load(yml_file: str) -> List[dict]:
    """Loads yaml format file to dictionary.
    
    Parameters
    ----------
    yml_file: str
        path to yml file

    Returns
    -------
    List[dict]
        list of loaded dictionaries
    """
    with open(yml_file, "r") as infile:
        return yaml.full_load(infile)


def _find_N_dim(array: Union[list, str], template: str
                ) -> Optional[Union[list, str]]:
    """Recursive helper function with two nested list as input. array is
    traversed and its elements are fuzzy tested if they match expresion in 
    template

    Parameters
    ----------
    array: list
        argument is a nested list of strings in which we want to find
        element.
    template: str
       string to find in the nested list

    See also
    --------
    :func:`complete_N_dim`
    :func:`replace_N_dim`
    """
    if isinstance(array, list):
        for a in array:
            ret = _find_N_dim(a, template)
            if ret is not None:
                return ret
    else:
        # length check is to stop shortz words replacing long
        if len(array) > len(template):
            if fuzz.token_set_ratio(template, array) > 80:
                return array


def complete_N_dim(to_complete: list, to_find: list):
    """Recursive function with two list as input, one list contains incomplete
    versions of strings and the other has full versions. Lists can be nested.
    both are then traversed and the strings in the first list are completed
    with strings from the second list. Changes are made in place.

    Parameters
    ----------
    to_complete: list
        argument is a list which elements are not complete. Changes to this
        list are made in-place.
    to_find: list
       argument is the list which contains full strings. All uncomplete
       strings in to_complete will be replaced by their longer version
       from to_find

    See also
    --------
    :func:`_find_N_dim`
    """
    if isinstance(to_complete, list):
        for i, _ in enumerate(to_complete):
            ret = complete_N_dim(to_complete[i], to_find)
            if ret is not None:
                to_complete[i] = ret
    else:
        return _find_N_dim(to_find, to_complete)


def replace_N_dim(to_replace: list, to_find: str):
    """Recursive function with nested list as input. The nested list elements
    are traversed and defined expresion is replaced by empty string in each
    element. Changes are made in place.

    Parameters
    ----------
    to_replace: list
        argument is a list which elements are not contain unwanted string.
    to_find: str
       the unwanted string to find in nested list

    See also
    --------
    :func:`_find_N_dim`
    """
    if isinstance(to_replace, list):
        for i, _ in enumerate(to_replace):
            ret = replace_N_dim(to_replace[i], to_find)
            if ret is not None:
                to_replace[i] = ret
    else:
        return to_replace.replace(to_find, "").strip()


def delete_N_dim(to_delete: list, to_find: list) -> list:  # type: ignore
    """Recursive function with nested list as input. The nested list elements
    are traversed and each that is equal to one of the elements in to_find list
    is deleted. Changes are made in place.

    Parameters
    ----------
    to_replace: list
        argument is a nested list which contains unwanted elements.
    to_find: str
       list of unwanted elements
    """
    if to_delete:
        if isinstance(to_delete[0], list):
            for i, td in enumerate(to_delete):
                to_delete[i] = delete_N_dim(td, to_find)
        else:
            return [td for td in to_delete if td not in to_find]
    else:
        return []
