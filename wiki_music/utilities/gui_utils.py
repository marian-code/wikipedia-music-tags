"""Utility functions used by GUI classes."""

import io  # lazy loaded
import logging
import os
import sys
import urllib  # lazy loaded
import winreg  # lazy loaded
from typing import Optional, Tuple

import requests  # lazy loaded
from PIL import Image, ImageFile  # lazy loaded

from wiki_music.constants.paths import FILES_DIR

logging.getLogger(__name__)

# TODO meditate on including clipboard interaction
# import win32clipboard  # lazy loaded


__all__ = ["get_music_path", "abstract_warning", "get_image", "get_sizes",
           "comp_res", "get_image_size", "get_icon"]  # , "send_to_clipboard"]


def abstract_warning():
    """Raises error when abstract method is called directly.
    Raises
    ------
    NotImplementedError
        this is the sole purpose of this function
    """
    raise NotImplementedError("This method is abstaract and should be "
                              "reimplemented by inheriting class")


# TODO not used for now, need to rethink, maybe it is useless when we have
# writing to tags, it has a complex dependency which does not play nice with
# other platform except windows: pywin32>=224; platform_system == "Windows"
# maybe this function sholud be removed.
# ! in the future it might be replaced by PyQt QClipboard
# ! https://www.tutorialspoint.com/pyqt/pyqt_qclipboard.htm
"""
def send_to_clipboard(data: bytearray, clip_type: Optional[int] = None):
     Pastes data to clipboard.

    Parameters
    ----------
    clip_type: int
        type of the clipboard
    data: bytearray
        data to paste to clipboard

    Raises
    ------
    NotImplementedError
        when unsupported platform is detected, and we don't know how to
        interact with cilpboard

    clip_data: bytes

    file_stream = io.BytesIO(data)
    image = Image.open(file_stream)

    clip_stream = io.BytesIO()
    image.convert("RGB").save(clip_stream, "BMP")
    clip_data = clip_stream.getvalue()[14:]
    clip_stream.close()

    if os.name == "nt":
        if not clip_type:
            clip_type = win32clipboard.CF_DIB

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(clip_type, clip_data)
        win32clipboard.CloseClipboard()
    else:
        raise NotImplementedError("Only Windows clipboard is supported "
                                  "at the moment")
"""


def get_music_path() -> str:
    """Returns the default music path for linux or windows

    Returns
    -------
    str
        string path pointing to music library location
    """

    if os.name == "nt":
        sub_key = (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer"
                   r"\Shell Folders")
        music_guid = "{4BD8D571-6D19-48D3-BE97-422220080E43}"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                location = winreg.QueryValueEx(key, music_guid)[0]
            return location
        except Exception:
            return "~"

    else:
        return os.path.join(os.path.expanduser("~"), "music")


def get_image(address: str) -> Optional[bytes]:
    """Based on addres decides if the image is online or local. If address
    has http prefix, image is downloaded from internet. If not then it is read
    from disk.

    Parameters
    ----------
    address:
        string with path to picture on local PC or with http address

    Returns
    -------
    bytes
        bytes repesentation of image loaded to memory or None if address is
        not valid
    """

    if address.startswith("http"):
        return requests.get(address).content
    else:
        # this is for offline debug
        try:
            with open(address, "rb") as f:
                return bytearray(f.read())
        except Exception as e:
            print(f"Address: {address} could not be opened in "
                  f"online or offline mode. {e}")
            return None


def comp_res(image: bytearray, quality: int, x: int = 0, y: int = 0) -> bytes:
    """Compress and/or change image resolution. If x and y dimension are
    both specified than image is resized to these dimension otherwise it is
    only compressed

    Parameters
    ----------
    image: bytearray
        bytes representation of image loaded to memory
    quality: int
        target quality to which we wanto compress the limits are (1, 99)
    x: int
        horizontal image dimension
    y: int
        vertical iage dimension

    Returns
    -------
    bytes
        bytes image compressed and resized than reloaded to memory
    """

    FORMAT = Image.registered_extensions()[".jpg"]

    file_stream = io.BytesIO(image)
    img = Image.open(file_stream)

    if x and y:
        img = img.resize((x, y), Image.LANCZOS)

    file_stream = io.BytesIO()
    img.save(file_stream,
             FORMAT,
             optimize=True,
             quality=quality,
             progressive=True)

    return file_stream.getvalue()


def get_image_size(image: bytearray) -> str:
    """get size of image in memory

    Parameters
    ----------
    image: bytearray
        bytes image in loaded in memory

    Returns
    -------
    str
        string with image size in Kb rounded to 2 decimal places
    """

    return f"{sys.getsizeof(image) / 1024:.2f}"


def get_icon() -> str:
    """returns application icon path

    Raises
    ------
    FileNotFoundError
        if the path does not exist

    Returns
    -------
    str
        string with icon path
    """

    icon = os.path.join(FILES_DIR, "icon.ico")
    if not os.path.isfile(icon):
        raise FileNotFoundError(f"There is no icon file in: {icon}")
    else:
        return icon


def get_sizes(uri: str) -> Tuple[Optional[int], Optional[Tuple[int, int]]]:
    """Get file size and image size (None if not known) of picture on the
    internet without downloading it.

    Parameters
    ----------
    uri: str
        picture url addres

    References
    ----------
    https://stackoverflow.com/questions/15800704/get-image-size-without-loading-image-into-memory

    Returns
    -------
    tuple
        if the size can be obtained result is a tuple with picture size in Kb
        and dimensions tuple as a second element
    """

    try:
        fl = urllib.request.urlopen(uri)
        size = fl.headers.get("content-length")
        if size:
            size = int(size)

        p = ImageFile.Parser()
        while True:
            data = fl.read(1024)
            if not data:
                break
            p.feed(data)
            if p.image:
                return size, p.image.size

        fl.close()

        return size, None
    except Exception:
        return None, None
