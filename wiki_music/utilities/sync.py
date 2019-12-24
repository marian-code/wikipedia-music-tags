"""Module for variable synchronization between application and GUI."""

import logging
from queue import Queue, Empty
from threading import Barrier, RLock
from typing import Any, ClassVar, Dict, Hashable, Tuple, Union, Optional

import yaml  # lazy loaded

from wiki_music.constants import SETTINGS_YML

log = logging.getLogger(__name__)

__all__ = ["GuiLoggger", "YmlSettings", "Action", "Control", "Progress",
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

        self._put(self)

    @classmethod
    def _put(cls, value: "Action"):
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

    @classmethod
    def _put(cls, value: "Progress"):
        cls._queue.put(value)

    @classmethod
    def get_nowait(cls) -> Optional["Progress"]:
        """Get the latest entry in the Progress queue or None if it is empty.

        Returns
        -------
        Optional[Progress]
            instance of the Progress class or None
        """
        try:
            return cls._queue.get_nowait()
        except Empty:
            return None

    def __str__(self):
        return (f"<Progres: actual={self.actual}, max={self.max}, "
                f"desc={self.description}>")


class ThreadPoolProgress(Progress):
    """Class that informs GUI of threadpool progress.

    See also
    --------
    :class:`Progress`
    """

    _queue: "Queue[Progress]" = Queue()  # treadpool progress


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


class YmlSettings:
    """Holds all package settings. All new settings are witten to disc.

    All methods are thraed safe.

    Attribures
    ----------
    _settings_dict: dict
        dictionary holding all settings
    """

    _settings_dict: Dict[Hashable, Any]
    _lock: RLock = RLock()

    if SETTINGS_YML.is_file():
        with SETTINGS_YML.open("r") as f:
            _settings_dict = yaml.full_load(f)
    else:
        log.warning("Couldn't open settings yaml file")
        _settings_dict = dict()

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
            cls._settings_dict[key] = value
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
                del cls._settings_dict[key]
            except KeyError:
                log.debug("deleting non-existent YAML setting")
            else:
                cls._dump()

    @classmethod
    def read(cls, key: Hashable, default: Any) -> Any:
        """Get value from settings dictionary.

        Parameters
        ----------
        key: Hashable
            dictionary key
        default: Any
            default value to return if key is not present

        Returns
        -------
        Any
            value found under key if it was found or default
        """
        with cls._lock:
            try:
                return cls._settings_dict[key]
            except KeyError:
                log.debug("Accesing non-existent YAML setting")
                return default

    @classmethod
    def _dump(cls):
        """Syncronize in-memory settings dict with disk file.

        Has to be called in locked context.
        """
        with SETTINGS_YML.open("w") as f:
            yaml.dump(cls._settings_dict, f, default_flow_style=False,
                      allow_unicode=True)
