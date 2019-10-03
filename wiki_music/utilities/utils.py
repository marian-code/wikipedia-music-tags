import argparse  # lazy loaded
import os
import re  # lazy loaded
import sys
import unicodedata
from shutil import rmtree
from typing import NoReturn, Tuple, Union

import yaml  # lazy loaded

from .sync import SharedVars

__all__ = ["list_files", "to_bool", "normalize",
           "we_are_frozen", "module_path", "win_naming_convetion",
           "flatten_set", "clean_logs", "input_parser",
           "MultiLog", "get_google_api_key"]


class MultiLog:

    def __init__(self, logger):
        self.logger = logger

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)
        SharedVars.info(message)

    def warning(self, message):
        self.logger.warning(message)
        SharedVars.warning = message

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    def exception(self, message):
        self.logger.exception(message)
        SharedVars.exception = message


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


def to_bool(string: str) -> bool:
    """ Coverts string (yes, no, y, n adn capitalized versions) to bool.\n

    Parameters
    ----------
    string: str
        Input value.
    """

    return string.casefold() in ("y", "yes", "t", "true", "")


def normalize(text: str) -> str:
    """ NFKD string normalization """
    return unicodedata.normalize("NFKD", text)


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
    else:
        return os.path.join(os.path.dirname(__file__), "..")


def get_google_api_key() -> Union[str, NoReturn]:

    # load google api key for lyrics search
    _file = os.path.join(module_path(), "files", "google_api_key.txt")
    try:
        f = open(_file, "r")
        return f.read().strip()
    except Exception:
        raise Exception("You must input Google api key. Refer to "
                        "https://github.com/marian-code/wikipedia-music-tags "
                        f"for instructions. Expected key file at: {_file}")


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

    if dir_name:  # windows doesn´t like folders with dots at the end
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


# TODO probably not needed any more
def clean_logs():
    """ Attempts to clear the log files from previous run in logs directory.
    """
    _dir = os.path.join(module_path(), "logs")
    print(f"removing {_dir} logs")

    try:
        if os.path.isdir(_dir):
            rmtree(_dir, ignore_errors=True)
    except Exception as e:
        print(e)
    else:
        try:
            os.mkdir("logs")
        except FileExistsError as e:
            print(e)


def input_parser() -> Tuple[bool, bool, bool, str, str, str, bool]:
    """ Parse command line input parameters. """

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

    # under construction
    pass
