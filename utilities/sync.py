# Module for variable synchronization between application and GUI

from threading import Barrier, Lock
from typing import Union

__all__ = ["SharedVars"]


class SharedVars:
    """ Class for synchronizing info between threads
        info_exchange class provides means to synchronize some
        variables between gui and application, it serves to pass
        the questions asked in application to to PyQt (Tkinter) frontend.
    """

    # action description
    describe: str = ""
    ask_exit: str = ""
    switch: str = ""

    # switches
    write_json: bool = False
    offline_debbug: bool = False
    write_lyrics: bool = False
    assign_artists: bool = False

    # exceptions
    has_warning: str = ""
    has_exception: str = ""

    # control
    wait_exit: bool = False
    terminate_app: bool = False
    wait: bool = False
    done: bool = False
    load: bool = False
    lock = Lock()
    barrier = Barrier(2)

    @classmethod
    def re_init(cls):

        cls.write_lyrics = None
        cls.select_genre = None
        cls.assign_artists = None
        cls.write_tags = None
        cls.wait = None
        cls.switch = None
        cls.done = False
        cls.load = False

        # action description
        cls.describe = ""

        # caught exceptions
        cls.ask_exit = None

        # switches
        cls.wait_exit = False
        cls.terminate_app = False

        # threads
        cls.preload = None
        cls.parser_running = False

        # exceptions
        cls.has_warning = None
        cls.has_exception = None

    @classmethod
    def info(cls, msg: str):
        cls.describe = str(msg)

    @classmethod
    def warning(cls, msg: Union[Exception, str]):
        cls.has_warning = str(msg)

    @classmethod
    def exception(cls, msg: Union[Exception, str]):
        cls.has_exception = str(msg)