""" Basic utilities used by the whole package. """

import argparse  # lazy loaded
import os
import re  # lazy loaded
import sys
import unicodedata
from shutil import rmtree
from typing import NoReturn, Tuple, Union, Any, List

import yaml  # lazy loaded

from .sync import SharedVars
from wiki_music.constants import FILES_DIR

__all__ = ["list_files", "to_bool", "normalize", "we_are_frozen",
           "module_path", "win_naming_convetion", "flatten_set",
           "input_parser", "MultiLog", "get_google_api_key"]


class MultiLog:
    """ Passes the messages to logger instance and to SharedVars sychronization
    class where applicable as SharedVars does not implement whole Logger API

    See also
    --------
    :class:`wiki_music.utilities.sync.SharedVars`
        class passing the messages to GUI

    Parameters
    ----------
    logger: logging.Logger
        Logger instance
    """

    def __init__(self, logger):
        self.logger = logger

    def debug(self, message: Any):
        """ Issue a debug message. """
        self.logger.debug(message)

    def info(self, message: Any):
        """ Issue a info message. """
        self.logger.info(message)
        SharedVars.info(message)

    def warning(self, message: Any):
        """ Issue a warning message. """
        self.logger.warning(message)
        SharedVars.has_warning = message

    def error(self, message: Any):
        """ Issue a error message. """
        self.logger.error(message)

    def critical(self, message: Any):
        """ Issue a critical message. """
        self.logger.critical(message)

    def exception(self, message: Any):
        """ Issue a exception message. """
        self.logger.exception(message)
        SharedVars.has_exception = message


def list_files(work_dir: str, file_type: str = "music",
               recurse: bool = True) -> List[str]:
    """ List music files in directory.

    Parameters
    ----------
    work_dir: str
        directory to search
    file_type: str
        type of files to search
    recurse: bool
        whether to preform the search recursively

    Raises
    ------
    NotImplementedError
        if file_type is unsupported

    Note
    ----
    supported music formats are: .m4a, .mp3, .flac, .alac, .wav, .wma, .ogg
    supprted image formats are: .jpg, .png Qt library has trouble reading
    other formats.

    Returns
    -------
    list
        returns list of files in folder with specified file_type
    """

    found_files: List[str] = []
    allowed_types: Tuple[str, ...]

    if file_type == "music":
        # TODO list of files we ail to support:
        # (".m4a", ".mp3", ".flac", ".alac", ".wav", ".wma", ".ogg")
        allowed_types = (".m4a", ".mp3", ".flac")
    elif file_type == "image":
        allowed_types = ("jpg", "png")
    else:
        raise NotImplementedError(f"file type {file_type} is not supported")

    for root, _, files in os.walk(work_dir):
        for f in files:
            if f.endswith(allowed_types):
                found_files.append(os.path.join(root, f))
        if not recurse:
            break

    return found_files


def to_bool(string: str) -> bool:
    """ Coverts string (yes, no, y, n adn capitalized versions) to bool.\n

    Parameters
    ----------
    string: str
        Input value.

    Note
    ----
    all these values and their uprercase variants are considered true:
    y, yes, t, true, <empty string>

    Returns
    -------
    bool
        truth value of given string
    """

    return string.casefold() in ("y", "yes", "t", "true", "")


def normalize(text: str) -> str:
    """ NFKD string normalization

    Parameters
    ----------
    text: str
        text to normalize

    Returns
    -------
    str
        normalized version of text
    """
    return unicodedata.normalize("NFKD", text)


def we_are_frozen() -> bool:
    """ Checks if the running code is frozen (e.g by cx-Freeze, pyinstaller).

    Returns
    -------
    bool
        True if the code is frozen
    """

    # All of the modules are built-in to the interpreter
    return hasattr(sys, "frozen")


def module_path() -> str:
    """ Outputs root path of the module. Acounts for changes in path when
    app is frozen.

    Returns
    -------
    str
        string with root module path

    See also
    --------
    :func:`we_are_frozen`
    """

    if we_are_frozen():
        return os.path.dirname(sys.executable)
    else:
        return os.path.join(os.path.dirname(__file__), "..")


def get_google_api_key() -> Union[str, NoReturn]:
    """ Reads google api key needed by lyricsfinder in external libraries from
    file.

    Raises
    ------
    FileNotFoundError
        if the key file was not found

    Returns
    -------
    str
        google api key
    """

    # load google api key for lyrics search
    _file = os.path.join(FILES_DIR, "google_api_key.txt")
    try:
        f = open(_file, "r")
        return f.read().strip()
    except Exception:
        msg = (f"You must input Google api key. Refer to "
               f"https://github.com/marian-code/wikipedia-music-tags "
               f"for instructions. Expected key file at: {_file}")
        raise FileNotFoundError(msg)


def win_naming_convetion(string: str, dir_name=False) -> str:
    """ Returns Windows normalized path name with removed forbiden
    characters. If platworm is not windows string is returned without changes.

    Parameters
    ----------
    string: str
        Input path to normalize
    dir_name: bool
        whether to use aditional normalization for directories

    Returns
    -------
    str
        normalized string for use in windows
    """

    if sys.platform == "nt":
        if dir_name:  # windows doesn´t like folders with dots at the end
            string = re.sub(r"\.+$", "", string)
        return re.sub(r"\<|\>|\:|\"|\/|\\|\||\?|\*", "", string)
    else:
        return string


def flatten_set(array: List[list]) -> set:
    """ Converst 2D list to 1D set.

    Parameters
    ----------
    array: list
        2D list to flatten

    Returns
    -------
    set
        1D set made of serialized lists
    """

    return set([item for sublist in array for item in sublist])


def input_parser() -> Tuple[bool, bool, bool, str, str, str, bool]:
    """ Parse command line input parameters.

    Note
    ----
    command line arguments are parsed and honoured only when running in
    CLI mode

    Returns
    -------
    bool
        yaml switch for outputing in yaml format
    bool
        offline_debug switch to turn on offline debugging
    bool
        lyrics_only search only for lyrics switch
    str
        album name
    str
        artist name
    str
        path to working directorym, default is current dir
    bool
        with_log switch on logging
    """

    parser = argparse.ArgumentParser(description="Description of your program")

    parser.add_argument("-y", "--yaml", action="store_true",
                        help="Write yaml save file?")
    parser.add_argument("-o", "--offline_debbug", action="store_true",
                        help="Use offline pickle debbug file instead of "
                             "web page?")
    parser.add_argument("-l", "--lyrics_only", action="store_true",
                        help="Download only lyrics?")
    parser.add_argument("-a", "--album", default=None, help="Album name",
                        nargs="*")
    parser.add_argument("-b", "--band", default=None, help="Band name",
                        nargs="*")
    parser.add_argument("-w", "--work_dir", default=os.getcwd(),
                        help="working directory", type=str)
    parser.add_argument("-W", "--With_log", default=False,
                        action="store_false", help="Print loggning output, "
                        "applies only to console app")

    args = parser.parse_args()

    if args.album:
        args.album = " ".join(args.album)
    if args.band:
        args.band = " ".join(args.band)

    return (args.yaml, args.offline_debbug, args.lyrics_only,
            args.album, args.band, args.work_dir, args.With_log)


def loading():
    """ CLI loading marker

    Todo
    ----
    impement this
    """

    # under construction
    pass
