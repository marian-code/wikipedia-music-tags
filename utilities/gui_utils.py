import os
import sys
from threading import Thread

import lazy_import
import win32clipboard
from PIL import Image

winreg = lazy_import.lazy_module("winreg")
requests = lazy_import.lazy_module("requests")
BytesIO = lazy_import.lazy_callable("io.BytesIO")

__all__ = ["ThreadWithTrace", "image_handle", "get_music_path"] 


class ThreadWithTrace(Thread):
    def __init__(self, *args, **keywords):
        Thread.__init__(self, *args, **keywords)
        self.killed = False

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
        """
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
        """

        if path is not None:
            image.save(path, )

        if clipboad:
            output = BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()

            _send_to_clipboard(win32clipboard.CF_DIB, data)
    except Exception as e:
        return e
    else:
        return True


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
