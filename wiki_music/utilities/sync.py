""" Module for variable synchronization between application and GUI """

import logging
from threading import Barrier, Lock
from typing import ClassVar, Union

logging.getLogger(__name__)

__all__ = ["SharedVars"]

ClsStr = ClassVar[str]
ClsBool = ClassVar[bool]


class SharedVars:
    """ Class for synchronizing info between threads SharedVars class provides
    means to synchronize some variables between gui and application,
    it serves to pass the questions asked in úarser to to PyQt GIU.
    Should not be instantiated, all methods and attributes belog to the
    class. The class implements API similar to logging.Logger with info(),
    warning() and exception() methods. These are prefered to directly
    setting the attributes value.

    Attributes
    ----------
    describe : str
        describes the current progress in parser
    ask_exit : str
        initialize dialog to exit app, works only in GUI mode
    switch : str
        decides which dialog should be displayed in GUI - lyrics, genres,
        or lyrics
    write_json : bool
        write yaml fiel contining tags for all tracks
    offline_debbug : bool
        switch to offline debugging mode. Instead of online page a local
        pickle version is used of wikipedia.Page object and cover art
        is loaded from file on local PC. Currently doesn't work for lyrics
    write_lyrics : bool
        write lyrics to tags
    assign_artists : bool
        switch telling if  we should assign artist to composers
    has_warning : str
        atttribute set by warning() method
    has_exception : str
        attribute set ba exception() method
    wait_exit : bool
        GUI wait for parser termination
    terminate_app : bool
        switch to trigger parser termination
    wait : bool
        blocks parser thread execution if true until GUI get answer from
        user
    done : bool
        anounce parser is done
    load : bool
        switch for gui to update model
    lock : Lock
        threading.Lock to sync GUI and parser thread
    barrier : Barrier
        threading.Barried  to sync GUI and parser thread
    """

    # action description
    describe: ClsStr = ""
    ask_exit: ClsStr = ""
    switch: ClsStr = ""

    # switches
    write_json: ClsBool = False
    offline_debbug: ClsBool = False
    write_lyrics: ClsBool = False
    assign_artists: ClsBool = False
    get_api_key: ClassVar[Union[str, bool]] = True

    # exceptions
    has_warning: ClsStr = ""
    has_exception: ClsStr = ""

    # control
    wait_exit: ClsBool = False
    terminate_app: ClsBool = False
    wait: ClsBool = False
    done: ClsBool = False
    load: ClsBool = False
    lock: ClassVar[Lock] = Lock()
    barrier: ClassVar[Barrier] = Barrier(2)

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
        cls.lock.acquire()
        cls.describe = str(msg)
        cls.lock.release()

    @classmethod
    def warning(cls, msg: Union[Exception, str]):
        cls.has_warning = str(msg)

    @classmethod
    def exception(cls, msg: Union[Exception, str]):
        cls.has_exception = str(msg)
