"""Basic utilities used by the whole package."""

import argparse  # lazy loaded
import logging
import re  # lazy loaded
import sys
import unicodedata
from pathlib import Path
from shutil import rmtree
from time import sleep
from typing import Any, List, Optional, Tuple, Union

from .sync import GuiLoggger

logging.getLogger(__name__)

__all__ = ["list_files", "to_bool", "normalize", "we_are_frozen",
           "win_naming_convetion", "flatten_set", "input_parser", "MultiLog",
           "limited_input"]


class MultiLog:
    """Passes the messages to logger instance and to GuiLoggger.

    Only where applicable as GuiLoggger does not implement whole Logger API

    See also
    --------
    :class:`wiki_music.utilities.sync.GuiLoggger`
        class passing the messages to GUI

    Parameters
    ----------
    logger: logging.Logger
        Logger instance
    """

    def __init__(self, logger):
        self._logger = logger

    def debug(self, message: Any):
        """Issue a debug message."""
        self._logger.debug(message)

    def info(self, message: Any):
        """Issue a info message."""
        self._logger.info(message)
        GuiLoggger.info(message)

    def warning(self, message: Any):
        """Issue a warning message."""
        self._logger.warning(message)
        GuiLoggger.warning(message)

    def error(self, message: Any):
        """Issue a error message."""
        self._logger.error(message)

    def critical(self, message: Any):
        """Issue a critical message."""
        self._logger.critical(message)

    def exception(self, message: Any):
        """Issue a exception message."""
        self._logger.exception(message)
        GuiLoggger.exception(message)


def list_files(work_dir: Path, file_type: str = "music",
               recurse: bool = True) -> List[Path]:
    """List music files in directory.

    Parameters
    ----------
    work_dir: Path
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
        returns list of Path objects in folder with specified file_type
    """
    found_files: List[Path] = []
    allowed_types: Tuple[str, ...]

    if file_type == "music":
        # TODO list of files we aim to support:
        # ("m4a", "mp3", "flac", "alac", "wav", "wma", "ogg")
        allowed_types = ("m4a", "mp3", "flac")
    elif file_type == "image":
        allowed_types = ("jpg", "png")
    else:
        raise NotImplementedError(f"file type {file_type} is not supported")

    if recurse:
        pattern = "**/*"  # glog recurse
    else:
        pattern = "*"

    for f in work_dir.glob(pattern):
        if f.suffix.endswith(allowed_types):
            found_files.append(f)

    return found_files


def to_bool(string: Union[str, bool]) -> bool:
    """Coverts string (yes, no, y, n adn capitalized versions) to bool.

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
    if isinstance(string, bool):
        return string
    else:
        return string.casefold() in ("y", "yes", "t", "true", "")


def limited_input(dont_bother: bool) -> Union[bool, str]:
    """Prompt for cli input with limited options: y, n, d(dont bother me).

    Returns
    -------
    Union[bool, str]
        can be True, False or d for dont bother
    """
    while True:
        if dont_bother:
            inpt = input("Do you want to proceed? [y(yes), n(no), "
                         "d(don't bother me again)]")
        else:
            inpt = input("Do you want to proceed? [y(yes), n(no)]: ")

        inpt = str(inpt).strip().casefold()

        if not inpt or inpt == "y":
            return True
        elif inpt == "n":
            return False
        elif inpt == "d" and dont_bother:
            return "d"
        else:
            if dont_bother:
                print("You must input 'y', 'n' or 'd'")
            else:
                print("You must input 'y' or 'n'")


def normalize(text: str) -> str:
    """NFKD string normalization.

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
    """Checks if the running code is frozen (e.g by cx-Freeze, pyinstaller).

    Returns
    -------
    bool
        True if the code is frozen
    """
    # All of the modules are built-in to the interpreter
    return hasattr(sys, "frozen")


def win_naming_convetion(string: str, dir_name=False) -> str:
    """Returns Windows normalized path name.

    Forbiden characters are removed. If platworm is not windows string is
    returned without changes.

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
    if sys.platform.startswith("win32"):
        if dir_name:  # windows doesn´t like folders with dots at the end
            string = re.sub(r"\.+$", "", string)
        return re.sub(r"\<|\>|\:|\"|\/|\\|\||\?|\*", "", string)
    else:
        return string


def flatten_set(array: List[list]) -> set:
    """Converst 2D list to 1D set.

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
    """Parse command line input parameters.

    Parameters
    ----------
    log: bool
        true when logger asks for argument parsing, to set the right level

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
    bool
        true if logging level is debug
    """
    parser = argparse.ArgumentParser(description="Description of your program",
                                     epilog="Only --debug option is read in "
                                            "GUI mode, others work only with"
                                            "CLI app.")

    parser.add_argument("-y", "--yaml",
                        action="store_true",
                        help="Write yaml save file?")
    parser.add_argument("-o", "--offline_debbug",
                        action="store_true",
                        help="Use offline pickle debbug file instead of "
                        "web page?")
    parser.add_argument("-l", "--lyrics_only",
                        action="store_true",
                        help="Download only lyrics?")
    parser.add_argument("-a", "--album",
                        default=None,
                        help="Album name",
                        nargs="*")
    parser.add_argument("-b", "--band",
                        default=None,
                        help="Band name",
                        nargs="*")
    parser.add_argument("-w", "--work_dir",
                        default=Path(".").resolve(),
                        help="working directory",
                        type=str)
    parser.add_argument("-W", "--With_log",
                        default=False,
                        action="store_false",
                        help="Print loggning output, "
                        "applies only to console app")
    parser.add_argument("-d", "--debug",
                        default=False,
                        action="store_true",
                        help="Run in debugging mode")

    args = parser.parse_args()

    if args.album:
        args.album = " ".join(args.album)
    if args.band:
        args.band = " ".join(args.band)

    return (args.yaml, args.offline_debbug, args.lyrics_only, args.album,
            args.band, args.work_dir, args.With_log, args.debug)


def loading():
    """CLI loading marker.

    Warnings
    --------
    not implemented
    """
    # under construction
    pass
