import os
from threading import Lock, Thread

import lazy_import
from colorama import Fore
from fuzzywuzzy import fuzz

from .utils import normalize

OrderedDict = lazy_import.lazy_callable("collections.OrderedDict")
json = lazy_import.lazy_module("json")


__all__ = ["NLTK", "bracket", "write_roman",
           "roman_num", "normalize", "normalize_caseless", "caseless_equal",
           "caseless_contains", "count_spaces", "json_dump",
           "complete_N_dim", "replace_N_dim", "delete_N_dim"]


class NltkMeta(type):
    @property
    def nltk(cls):
        with cls.lock:
            return cls._nltk


class NLTK(metaclass=NltkMeta):
    """ A thread safe nltk importer. Will make other threads wait if they want
        to access nltk until it is imported.
    """

    import_running = False
    # nltk class attribute is provided by metaclass
    _nltk = None
    lock = Lock()

    @classmethod
    def run_import(cls):

        def imp():
            with cls.lock:
                import nltk
                cls._nltk = nltk

        if not cls.import_running:

            cls.import_running = True
            # load NLTK in separate thread
            Thread(target=imp, name="ImportNLTK").start()


def bracket(data: list) -> list:
    """ Puts elements of the list in brackets.\n

    Parameters
    ----------
    data: list
        input data
    """

    data_tmp = []
    for d in data:
        if d:
            data_tmp.append("({})".format(d))
        else:
            data_tmp.append("")

    return data_tmp


def write_roman(num: int):
    """ Convert integer to roman number """

    roman = OrderedDict()
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


def roman_num(num: int) -> str:

    for r in roman.keys():  # pylint: disable=E0602
        x, _ = divmod(num, r)
        yield roman[r] * x  # pylint: disable=E0602
        num -= (r * x)
        if num > 0:
            roman_num(num)
        else:
            break

    return "".join([a for a in roman_num(num)])


def normalize_caseless(text: str) -> str:
    """ NFKD casefold string normalization """
    return normalize(text).casefold()


def caseless_equal(left: str, right: str) -> bool:
    """ Check for normalized string equality """
    return normalize_caseless(left) == normalize_caseless(right)


def caseless_contains(string: str, in_text: str) -> bool:
    """ Check if string is contained in text.\n
    string: str
        string to search for
    in_text: str
        string to search in
    """

    if normalize_caseless(string) in normalize_caseless(in_text):
        return True
    else:
        return False


def count_spaces(tracks: list, types: list) -> (list, int):
    """ Counts max length of elements in list and croesponding spaces for
    each item to fit that length.\n

    Parameters
    ----------
    tracks: list
        input data
    types: list
        input data
    """

    length = 0
    for tr, tp in zip(tracks, types):
        if len(tr) + len(tp) > length:
            length = len(tr) + len(tp)

    spaces = []
    for tr, tp in zip(tracks, types):
        spaces.append(" " * (length - len(tr) - len(tp) + 8))

    return spaces, length


def json_dump(dict_data: list, save_dir: str):
    """ Save json file to disk.\n

    Parameters
    ----------
    dict_data: list
        list of dictionarie to save to disk
    save_dir: str
        directory to save to
    """

    _path = os.path.join(save_dir, "database.json")
    print(Fore.GREEN + "\nSaving JSON file: " + Fore.RESET + _path + "\n")
    with open(_path, "w") as outfile:
        json.dump(dict_data, outfile, indent=4)


def _find_N_dim(array, template):
    # hepler function for complete_N_dim and replace_N_dim

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
    """ `to_complete` is a list which elements are not complete. Changes to this
    list are made in-place.\n
    `to_find` argument is the list which contains full strings.\n
    All uncomplete strings in to_complete will be replaced by their
    longer version from to_find.\n

    Parameters
    ----------
    to_complete: list
        Input data.
    to_find: list
       Input data.
    """

    if isinstance(to_complete, list):
        for i, _ in enumerate(to_complete):
            ret = complete_N_dim(to_complete[i], to_find)
            if ret is not None:
                to_complete[i] = ret
    else:
        return _find_N_dim(to_find, to_complete)


def replace_N_dim(to_replace: list, to_find: str):
    """ `to_replace` is a list which elements contain unwanted strings.
    Changes to this list are made in-place.\n
    `to_find` argument is the unwanted string. All unwanted strings will be
    replaced by empty string.\n

    Parameters
    ----------
    to_replace: list
        Input data.
    to_find: str
       Input data.
    """

    if isinstance(to_replace, list):
        for i, _ in enumerate(to_replace):
            ret = replace_N_dim(to_replace[i], to_find)
            if ret is not None:
                to_replace[i] = ret
    else:
        return to_replace.replace(to_find, "").strip()
        # return re.sub(to_find, "", to_replace).strip()


def delete_N_dim(to_delete: list, to_find: list):
    """ `to_delete` is a list which contains undesired elements.
    Changes to this list are made in-place.\n
    `to_find` argument is the list which contains full strings.\n
    All elements of to_delete with strings matching one of to_find will be
    deleted.\n

    Parameters
    ----------
    to_delete: list
        Input data.
    to_find: list
       Input data.
    """

    if isinstance(to_delete, list):
        if to_delete:
            if isinstance(to_delete[0], list):
                for i, td in enumerate(to_delete):
                    to_delete[i] = delete_N_dim(td, to_find)
            else:
                return [td for td in to_delete if td not in to_find]
        else:
            return []
    else:
        raise TypeError("to_delete must be a list instance")
