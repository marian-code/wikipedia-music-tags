import package_setup
import unicodedata

import lazy_import
from fuzzywuzzy import fuzz
from colorama import Fore
from urllib.request import urlopen
from PIL import ImageFile, Image
import win32clipboard

init = lazy_import.lazy_callable("colorama.init")
BeautifulSoup = lazy_import.lazy_callable("bs4.BeautifulSoup")
OrderedDict = lazy_import.lazy_callable("collections.OrderedDict")
BytesIO = lazy_import.lazy_callable("io.BytesIO")

json = lazy_import.lazy_module("json")
os = lazy_import.lazy_module("os")
sys = lazy_import.lazy_module("sys")
re = lazy_import.lazy_module("re")
winreg = lazy_import.lazy_module("winreg")
requests = lazy_import.lazy_module("requests")

__all__ = ['write_roman', 'roman_num', "normalize", "normalize_caseless",
           "caseless_equal", "count_spaces", "bracket",
           "colorama_init", "json_dump", "to_bool", "win_naming_convetion",
           "we_are_frozen", "caseless_contains", "get_music_path",
           "image_handle"]  # , "nth"]


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


def normalize(text: str) -> str:
    """ NFKD string normalization """
    return unicodedata.normalize("NFKD", text)


def normalize_caseless(text: str) -> str:
    """ NFKD casefold string normalization """
    return unicodedata.normalize("NFKD", text.casefold())


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


# TODO probably not used
"""
def nth(n: int, string: str) -> int:
    if n < 0:
        pos = -1
    else:
        try:
            pos = [m.start() for m in re.finditer(r" ", string)][n]
        except IndexError:
            pos = len(string) - 2
    return pos
"""


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
        spaces.append(" "*(length - len(tr) - len(tp) + 8))

    return spaces, length


def bracket(data: list) -> list:
    """ Puts elements of the list in brackets.\n

    Parameters
    ----------
    data: list
        input data
    """

    data_tmp = []
    for d in data:
        if len(d) > 0:
            data_tmp.append("({})".format(d))
        else:
            data_tmp.append("")

    return data_tmp


def colorama_init():
    """ Colorama initialize foe Windows """
    init(convert=True)


def list_files(work_dir: str) -> list:
    """ List music files in directory.\n

    Parameters
    ----------
    work_dir: str
        directory to search
    """

    album_files = []
    file_types = [".m4a", ".mp3", ".flac", ".alac", ".wav", ".wma", ".ogg"]

    for root, _, files in os.walk(work_dir):
        for f in files:
            if f[f.rfind("."):] in file_types:
                album_files.append(os.path.join(root, f))

    return album_files


def json_dump(dict_data: list, save_dir: str):
    """ Save json file to disk.\n

    Parameters
    ----------
    dict_data: list
        list of dictionarie to save to disk
    save_dir: str
        directory to save to
    """

    _path = os.path.join(save_dir, 'database.json')
    print(Fore.GREEN + "\nSaving JSON file: " + Fore.RESET + _path + "\n")
    with open(_path, 'w') as outfile:
        json.dump(dict_data, outfile, indent=4)


def _find_N_dim(array, template):
    # hepler function for replace_N_dim and delete_N_dim

    if isinstance(array, list) is True:
        for a in array:
            ret = _find_N_dim(a, template)
            if ret is not None:
                return ret
    else:
        # length check is to stop shortz words replacing long
        if len(array) > len(template):
            if fuzz.token_set_ratio(template, array) > 80:
                return array


def replace_N_dim(to_replace: list, to_find: list):
    """ `to_replace` is a list which elements are not complete. Changes to this
    list are made in-place.\n
    `to_find` argument is the list which contains full strings.\n
    All uncomplete strings in to_replace will be replaced by their
    longer version from to_find.\n

    Parameters
    ----------
    to_replace: list
        Input data.
    to_find: list
       Input data.
    """

    if isinstance(to_replace, list) is True:
        for i in range(len(to_replace)):
            ret = replace_N_dim(to_replace[i], to_find)
            if ret is not None:
                to_replace[i] = ret
    else:
        return _find_N_dim(to_find, to_replace)


def delete_N_dim(to_replace: list, to_find: str):
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

    if isinstance(to_replace, list) is True:
        for i in range(len(to_replace)):
            ret = delete_N_dim(to_replace[i], to_find)
            if ret is not None:
                to_replace[i] = ret
    else:
        return re.sub(to_find, "", to_replace).strip()


def get_max_len(data: list) -> int:
    """ Returns max length of array in horizontal direction.\n

    Parameters
    ----------
    data: list
        Input data.
    """

    return max([len(i) for i in data])


def to_bool(string: str) -> bool:
    """ Coverts string (yes, no, y, n adn capitalized versions) to bool.\n

    Parameters
    ----------
    string: str
        Input value.
    """

    if (normalize_caseless(string) == "y" or
       normalize_caseless(string) == "yes"):
        return True
    if (normalize_caseless(string) == "n" or
       normalize_caseless(string) == "no"):
        return False


def we_are_frozen() -> bool:
    """ Checks if the running code is frozen (e.g by cx-Freeze). Outputs
    True or False.
    """

    # All of the modules are built-in to the interpreter, e.g., by py2exe
    return hasattr(sys, "frozen")


def module_path() -> str:
    """ Outputs root path of the module. """
    # encoding = sys.getfilesystemencoding()
    if we_are_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)


def clean_logs():
    """ Attempts to clear the log files from previous run in logs directory.
    """

    print("removing", os.path.join(module_path(), "logs"))

    import shutil
    try:
        shutil.rmtree(os.path.join(module_path(), "logs"), ignore_errors=True)
    except Exception as e:
        print(e)

    # remove previous log(s)
    try:
        os.mkdir('logs')
    except FileExistsError as e:
        print(e)
    except PermissionError as e:
        print(e)


def win_naming_convetion(string: str, dir_name=False) -> str:
    """ Returns Windows normalized path name with removed forbiden
    characters.\n

    Parameters
    ----------
    string: str
        Input path to normalize
    dir_name: bool
        whether to use aditional normalization for directories
    """

    if dir_name is True:  # windows doesn´t like folders with dots at the end
        string = re.sub(r"\.+$", "", string)
    return re.sub(r"\<|\>|\:|\"|\/|\\|\||\?|\*", "", string)


def flatten_set(array: list) -> set:
    """ Converst 2D list to 1D set.\n

     Parameters
    ----------
    array: list
        2D list to flatten
    """

    return set([item for sublist in array for item in sublist])


def get_music_path() -> str:
    """Returns the default music path for linux or windows"""

    if os.name == 'nt':
        sub_key = (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer"
                   r"\Shell Folders")
        music_guid = '{4BD8D571-6D19-48D3-BE97-422220080E43}'
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                location = winreg.QueryValueEx(key, music_guid)[0]
            return location
        except:
            return "~"

    else:
        return os.path.join(os.path.expanduser('~'), 'music')


def get_sizes(uri):
    """ Get file size *and* image size (None if not known) of picture on the
    internet without downloading it.\n

    Parameters
    ----------
    uri: str
        picture url addres
    """

    try:
        file = urlopen(uri)
        size = file.headers.get("content-length")
        if size:
            size = int(size)

        p = ImageFile.Parser()
        while True:
            data = file.read(1024)
            if not data:
                break
            p.feed(data)
            if p.image:
                return size, p.image.size

        file.close()

        return size, None
    except:
        return None, None


def _send_to_clipboard(clip_type: int, data: BytesIO):
    """ Pastes data to clipboard.\n

    Parameters
    ----------
    clip_type: int
        type of the clipboard
    data: ByteIO
        data to paste to clipboard
    """

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(clip_type, data)
    win32clipboard.CloseClipboard()


def image_handle(url: str, size=None, clipboad=True, path=None,
                 log=None) -> bool:
    """ Downloads image from internet and reduces its size to <300Kb. If
    specified in input image can be also resized to defined dimensions.
    Than paste to clipboard or/and save to file based on input.

    Parameters
    ----------
    url: str
        url addres of image
    size: tuple or None
        tuple of desired image dimensions e.g. (500, 500). If None (default)
        image is not resized.
    clipboard: bool
        whether to paste image to clipboard
    path: str or None
        path to save picture on disk. If None - don´t save.
    log: logging.Logger
        logger object to log messages
    """

    try:
        image = requests.get(url).content
        file_stream = BytesIO(image)
        image = Image.open(file_stream)

        if size is not None:
            image = image.resize(size, Image.LANCZOS)

        # get size down to ~300Kb
        disk_size = sys.getsizeof(file_stream)/1024
        _format = Image.registered_extensions()[".jpg"]
        q = 95
        while disk_size > 300:
            # TODO this is good, but how do the streams work?
            file_stream = BytesIO()
            image.save(file_stream, _format, optimize=True, quality=q)
            image = Image.open(file_stream)
            disk_size = sys.getsizeof(file_stream)/1024
            # print("disk size:", disk_size, "quality:", q)
            q -= 5
            if q < 50:
                if log is not None:
                    log.warning("Couldn´t reduce the size under 300 Kb")
                break

        if path is not None:
            image.save(path, )

        if clipboad is True:
            output = BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()

            _send_to_clipboard(win32clipboard.CF_DIB, data)
    except Exception as e:
        return e
    else:
        return True


def json_load(work_dir: str):
    pass
    # under construction


def loading():

    # under construction
    pass
