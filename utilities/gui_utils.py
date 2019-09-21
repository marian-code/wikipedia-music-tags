import os

import lazy_import
import win32clipboard
from PIL import Image, ImageFile

from .utils import module_path

sys = lazy_import.lazy_module("sys")
winreg = lazy_import.lazy_module("winreg")
requests = lazy_import.lazy_module("requests")
BytesIO = lazy_import.lazy_callable("io.BytesIO")

__all__ = ["get_music_path", "abstract_warning", "get_image", "get_sizes",
           "comp_res", "get_image_size", "get_icon", "send_to_clipboard"]

FORMAT = Image.registered_extensions()[".jpg"]


def abstract_warning():
    """ Raises error when abstract method is called directly. """
    raise NotImplementedError("This method is abstaract and should be "
                              "reimplemented by inheriting class")


def send_to_clipboard(data: bytearray, clip_type=win32clipboard.CF_DIB):
    """ Pastes data to clipboard.\n

    Parameters
    ----------
    clip_type: int
        type of the clipboard
    data: bytearray
        data to paste to clipboard
    """

    file_stream = BytesIO(data)
    image = Image.open(file_stream)

    clip_stream = BytesIO()
    image.convert("RGB").save(clip_stream, "BMP")
    data = clip_stream.getvalue()[14:]
    clip_stream.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(clip_type, data)
    win32clipboard.CloseClipboard()


def get_music_path() -> str:
    """Returns the default music path for linux or windows"""

    if os.name == "nt":
        sub_key = (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer"
                   r"\Shell Folders")
        music_guid = "{4BD8D571-6D19-48D3-BE97-422220080E43}"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                location = winreg.QueryValueEx(key, music_guid)[0]
            return location
        except:
            return "~"

    else:
        return os.path.join(os.path.expanduser("~"), "music")


def get_image(address: str) -> bytearray:

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


def comp_res(image: bytearray, quality: int, x: int=0, y: int=0) -> bytearray:

    file_stream = BytesIO(image)
    image = Image.open(file_stream)

    if x and y:
        image = image.resize((x, y), Image.LANCZOS)

    file_stream = BytesIO()
    image.save(file_stream, FORMAT, optimize=True, quality=quality,
               progressive=True)

    return file_stream.getvalue()


def get_image_size(image) -> str:

    return f"{sys.getsizeof(image) / 1024:.2f}"


def get_icon() -> str:

    icon = os.path.join(module_path(), "files", "icon.ico")
    if not os.path.isfile(icon):
        raise FileNotFoundError(f"There is no icon file in: {icon}")
    else:
        return icon


def get_sizes(uri: str) -> (str, [int, int]):
    """ Get file size *and* image size (None if not known) of picture on the
    internet without downloading it.\n

    Parameters
    ----------
    uri: str
        picture url addres
    """

    try:
        fl = urlopen(uri)
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
    except:
        return None, None
