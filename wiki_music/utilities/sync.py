"""Module for variable synchronization between application and GUI """

import logging
from threading import Barrier, Lock
from typing import ClassVar, Union

logging.getLogger(__name__)

__all__ = ["SharedVars"]


class SharedVars:
    """Class for synchronizing variables between parser and GUI thread.

    Serves to pass the questions asked in parser to to PyQt GIU.
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
        write yaml file contining tags for all tracks
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
    progress: ClassVar[int] = 0
    threadpool_prog: ClassVar[int] = 0
    describe: ClassVar[str] = ""
    ask_exit: ClassVar[str] = ""
    switch: ClassVar[str] = ""

    # switches
    write_json: ClassVar[bool] = False
    offline_debbug: ClassVar[bool] = False
    write_lyrics: ClassVar[bool] = False
    assign_artists: ClassVar[bool] = False
    get_api_key: ClassVar[Union[str, bool]] = True

    # exceptions
    has_warning: ClassVar[str] = ""
    has_exception: ClassVar[str] = ""

    # control
    wait_exit: ClassVar[bool] = False
    terminate_app: ClassVar[bool] = False
    wait: ClassVar[bool] = False
    done: ClassVar[bool] = False
    load: ClassVar[bool] = False
    lock: ClassVar[Lock] = Lock()
    barrier: ClassVar[Barrier] = Barrier(2)

    @classmethod
    def re_init(cls):
        """Initializes class variables to default values."""

        cls.write_lyrics = None
        cls.select_genre = None
        cls.assign_artists = None
        cls.write_tags = None
        cls.wait = None
        cls.switch = None
        cls.done = False
        cls.load = False

        # progressbars
        cls.progress = 0
        cls.threadpool_prog = 0

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
    def increment_progress(cls):
        """Increments progress read by GUI main progressbar.

        See also
        --------
        :meth:`wiki_music.gui_lib.main_window.Checkers._description_check`
            periodically running method that displays progress in GUI.
        """
        cls.lock.acquire()
        cls.progress += 1
        cls.lock.release()

    @classmethod
    def set_threadpool_prog(cls, count):
        """Increments progress read by GUI threadpool progressbar dialog.

        See also
        --------
        :meth:`wiki_music.gui_lib.main_window.Checkers._threadpool_check`
            periodically running method that displays progress in GUI.
        """
        cls.threadpool_prog = count

    @classmethod
    def info(cls, msg: str):
        """Messages to be displayed in GUI progressbar.

        Parameters
        ----------
        msg: str
            message text
        """
        if len(msg) > 100 and ":" in msg:
            msg = msg.split(": ", 1)[1]
        cls.lock.acquire()
        cls.describe = str(msg).strip()
        cls.lock.release()

    @classmethod
    def warning(cls, msg: Union[Exception, str]):
        """Warnings to be displayed in GUI.

        Warnings, only inform user but do not interupt the program.

        Parameters
        ----------
        msg: str
            message text
        """
        cls.has_warning = str(msg)

    @classmethod
    def exception(cls, msg: Union[Exception, str]):
        """Exceptions to be displayed in GUI.

        Exceptions can interupt running program, based on their severity.

        Parameters
        ----------
        msg: str
            message text
        """
        cls.has_exception = str(msg)
