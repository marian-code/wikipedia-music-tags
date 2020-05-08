"""Module for variable synchronization between application and GUI."""

import inspect
import logging
from configparser import ConfigParser  # lazy loaded
from queue import Empty, Queue
from threading import Barrier, RLock, current_thread
from typing import Any, ClassVar, Dict, Hashable, Optional, Tuple, Union

from wiki_music.constants import SETTINGS_INI

log = logging.getLogger(__name__)

__all__ = ["GuiLoggger", "IniSettings", "Action", "Control", "Progress",
           "ThreadPoolProgress"]


class Action:
    """Represents action that should be taken by GUI.

    Parameters
    ----------
    switch: str
        type of action
    message: Optional[str]
        message to show in GUI
    load: bool
        whether to load data to GUI from parser prior to any action
    options: list
        list of options to display in GUI for user to choose
    response
        property that caches GUI response

    Attributes
    ----------
    _queue: Queue[Action]
        queue with actions gui should take
    _response_queue: Queue[Action]
        GUI response to actions taken

    Warning
    -------
    Action may be used only once, the response is cached and GUI will not be
    asked for new response on each call of :attr:`response`
    """

    _queue: "Queue[Action]" = Queue()  # action commands
    _response_queue: "Queue[Action]" = Queue()  # action responses

    def __init__(self, switch: str, message: Optional[str] = None,
                 load: bool = False, options: list = []) -> None:

        self.switch = switch
        self.message = message
        self._response: Any = None
        self.load = load
        self.options = options

        # TODO only for debugging
        caller_name = inspect.stack()[1].function
        caller_thread = current_thread().getName()

        self._put(self)

    def __str__(self) -> str:

        return (f"Action<switch: {self.switch}, message: {self.message}, "
                f"response: {self._response}, load: {self.load}, "
                f"options: {self.options}>")

    @classmethod
    def _put(cls, value: "Action"):

        # TODO only for debugging
        caller_name = inspect.stack()[1].function
        caller_thread = current_thread().getName()
        log.debug(f"{str(value)}\n"
                  f"put in queue by: {caller_name}\n"
                  f"in thread: {caller_thread}\n"
                  f"actual queue size: {cls._queue.qsize()}")

        cls._queue.put(value)

    @classmethod
    def _put_resp(cls, value: "Action"):
        cls._response_queue.put(value)

    @classmethod
    def _get_resp(cls) -> "Action":
        return cls._response_queue.get()

    @classmethod
    def get_nowait(cls) -> Optional["Action"]:
        """Get the latest entry in the response queue or None if it is empty.

        Returns
        -------
        Optional[Action]
            instance of the Action class or None
        """
        try:
            return cls._queue.get_nowait()
        except Empty:
            return None

    @property
    def response(self) -> Any:
        """Pass `Action` to GUI, wait for response than return it.

        :type: Any
        """
        return self._get_resp()._response

    @response.setter
    def response(self, value: Any):
        self._response = value
        self._put_resp(self)


class Control(Action):
    """Passes flow control actions to GUI.

    See also
    --------
    :class:`Action`
    """

    _queue: "Queue[Action]" = Queue()  # control commands
    _response_queue: "Queue[Action]" = Queue()  # control responses


class Progress:
    """Class that informs GUI of parser progress.

    Parameters
    ----------
    desctiption: str
        desctiption of the ongoing action
    actual_progress: int
        actual progress value
    max_progress: int
        max progress value
    finished: bool
        flag indicating that the background process has finished work

    Attributes
    ----------
    _queue: Queue[Action]
        queue which describes parser progress
    """

    _queue: "Queue[Progress]" = Queue()  # main progress

    def __init__(self, description: str = "", actual: int = 0,
                 maximum: int = 0, finished: bool = False,
                 busy: bool = False) -> None:

        self.description = description
        self.actual = actual
        self.max = maximum
        self.finished = finished

        if busy:
            self.max = self.actual

        self._put(self)

    def __str__(self):
        return (f"<Progres: actual={self.actual}, max={self.max}, "
                f"description={self.description}, finished={self.finished}>")

    @classmethod
    def _put(cls, value: "Progress"):
        cls._queue.put(value)

    @classmethod
    def get_nowait(cls) -> Optional["Progress"]:
        """Get the first entry in the Progress queue or None if it is empty.

        Returns
        -------
        Optional[Progress]
            instance of the Progress class or None
        """
        try:
            return cls._queue.get_nowait()
        except Empty:
            return None

    @classmethod
    def get_actual_nowait(cls) -> Optional["Progress"]:
        """Get the latest entry in the Progress queue or None if it is empty.

        The method empties whole queue.

        Returns
        -------
        Optional[Progress]
            instance of the Progress class or None
        """
        previous = None
        while True:
            actual = cls.get_nowait()
            if not actual:
                return previous
            else:
                previous = actual


class ThreadPoolProgress(Progress):
    """Class that informs GUI of threadpool progress.

    See also
    --------
    :class:`Progress`
    """

    _queue: "Queue[Progress]" = Queue()  # treadpool progress

    def __str__(self):
        return super().__str__().replace("Progress", "ThreadPoolProgress")


class GuiLoggger:
    """Class Implementing logging facility for GUI.

    API copies that of python logging.Logger

    Attributes
    ----------
    progress: int
        controlls main gui progressbar
    """

    progress: ClassVar[int] = 0

    @classmethod
    def info(cls, msg: str):
        """Messages to be displayed in GUI progressbar.

        Parameters
        ----------
        msg: str
            message text
        """
        cls.progress += 1

        if len(msg) > 100 and ":" in msg:
            msg = msg.split(": ", 1)[1]

        Progress(description=str(msg).strip(), actual=cls.progress)

    @classmethod
    def warning(cls, msg: Union[Exception, str]):
        """Warnings to be displayed in GUI.

        Warnings, only inform user but do not interupt the program.

        Parameters
        ----------
        msg: str
            message text
        """
        Control("warning", str(msg))

    @classmethod
    def exception(cls, msg: Union[Exception, str]):
        """Exceptions to be displayed in GUI.

        Exceptions can interupt running program, based on their severity.

        Parameters
        ----------
        msg: str
            message text
        """
        Control("exception", str(msg))


class IniSettings:
    """Holds all package settings. All new settings are witten to disc.

    All methods are thraed safe.

    Attribures
    ----------
    _parser: ConfigParser
        dictionary-like object holding all settings
    """

    _lock: RLock = RLock()
    _parser: ConfigParser = ConfigParser()

    if SETTINGS_INI.is_file():
        _parser.read(SETTINGS_INI)
    else:
        log.warning("Couldn't open settings ini file")

        _parser["SETTINGS"] = {}

    # TODO might be an encoding problem
    @classmethod
    def write(cls, key: Hashable, value: Any):
        """Write new value to settings dictionary and to disk.

        Parameters
        ----------
        key: Hashable
            dictionary key
        value:
            value to write under key
        """
        with cls._lock:
            cls._parser["SETTINGS"][key] = str(value)
            cls._dump()

    @classmethod
    def delete(cls, key: Hashable):
        """Delete specified key for settings dictionary.

        Parameters
        ----------
        key: Hashable
            key to delete
        """
        with cls._lock:
            try:
                del cls._parser["SETTINGS"][key]
            except KeyError:
                log.debug("deleting non-existent INI setting")
            else:
                cls._dump()

    @classmethod
    def read(cls, key: Hashable, default: Any = None,
             _type: type = str) -> Any:
        """Get value from settings dictionary.

        Parameters
        ----------
        key: Hashable
            dictionary key
        default: Any
            default value to return if key is not present
        _type: type
            after read variable is cast to specisied type, as configparser
            always stores variables to string

        Returns
        -------
        Any
            value found under key if it was found or default
        """
        if _type == bool:
            _type = lambda x: x.lower() in ("y", "yes", "t", "true", "on", "1")

        with cls._lock:
            try:
                return _type(cls._parser["SETTINGS"][key])
            except KeyError:
                log.debug("Accesing non-existent INI setting")
                return default

    @classmethod
    def _dump(cls):
        """Syncronize in-memory settings ini-parser object with disk file.

        Has to be called in locked context.
        """
        with SETTINGS_INI.open("w") as f:
            cls._parser.write(f)
