"""Module for variable synchronization between application and GUI."""

import logging
from queue import Queue
from threading import Barrier, RLock
from typing import Any, ClassVar, Dict, Hashable, Tuple, Union, Optional

import yaml  # lazy loaded

from wiki_music.constants import SETTINGS_YML

log = logging.getLogger(__name__)

__all__ = ["SharedVars", "YmlSettings", "Action", "Control", "Progress"]


class Action:
    """Represents action that should be taken by GUI.

    Attributes
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

    Warning
    -------
    Action may be used only once, the response is cached and GUI will not be
    asked for new response on each call of :attr:`response`
    """

    def __init__(self, switch: str, message: Optional[str] = None,
                 load: bool = False, options: list = []) -> None:

        self.switch = switch
        self.message = message
        self._response: Any = None
        self.load = load
        self.options = options

    @property
    def response(self) -> Any:
        """Pass `Action` to GUI, wait for response than return it.

        :type: Any
        """
        SharedVars.a_queue.put(self)
        return SharedVars.r_queue.get()._response

    @response.setter
    def response(self, value: Any):
        self._response = value
        SharedVars.r_queue.put(self)


# TODO should probably have its own queue and not reuse r_queue
class Control(Action):
    """Passes flow control actions to GUI."""

    @property
    def response(self) -> Any:
        """Pass `Control` to GUI, wait for response than return it.

        :type: Any
        """
        SharedVars.a_queue.put(self)
        return SharedVars.r_queue.get()._response

    @response.setter
    def response(self, value: Any):
        self._response = value
        SharedVars.r_queue.put(self)


class Progress:
    """Class that informs GUI of parser progress.

    Attributes
    ----------
    desctiption: str
        desctiption of the ongoing action
    actual_progress: int
        actual progress value
    max_progress: int
        max progress value
    finished: bool
        flag indicating that the background process has finished work
    """

    def __init__(self, description: str = "", actual: int = 0,
                 maximum: int = 0, finished: bool = False,
                 busy: bool = False) -> None:

        self.description = description
        self.actual = actual
        self.max = maximum
        self.finished = finished

        if busy:
            self.max = self.actual

    def __str__(self):
        return (f"<Progres: actual={self.actual}, max={self.max}, "
                f"desc={self.description}>")


class SharedVars:
    """Class for synchronizing variables between parser and GUI thread.

    Serves to pass the questions asked in parser to to PyQt GIU.
    Should not be instantiated, all methods and attributes belog to the
    class. The class implements API similar to logging.Logger with info(),
    warning() and exception() methods. These are prefered to directly
    setting the attributes value.

    Attributes
    ----------
    progress: int
        controlls main gui progressbar
    a_queue: Queue[Action]
        queue with actions gui should take
    r_queue: Queue[Action]
        GUI response to actions taken
    c_queue: Queue[Action]
        queue containing flow control actions
    p_queue: Queue[Progress]
        informs main GUI progresbar of parser progress
    tp_queue: Queue[Progress]
        informas gui of threadpool progress
    """

    # thread safe attributes, defined by properties in metaclass
    progress: ClassVar[int] = 0

    # control queues
    a_queue: "Queue[Action]" = Queue()
    r_queue: "Queue[Action]" = Queue()
    c_queue: "Queue[Action]" = Queue()
    p_queue: "Queue[Progress]" = Queue()
    tp_queue: "Queue[Progress]" = Queue()

    @classmethod
    def set_threadpool_prog(cls, actual: int, maximum: int):
        """Increments progress read by GUI threadpool progressbar dialog.

        See also
        --------
        :meth:`wiki_music.gui_lib.main_window.Checkers._threadpool_check`
            periodically running method that displays progress in GUI.
        """
        cls.tp_queue.put(Progress(actual=actual, maximum=maximum))

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

        cls.p_queue.put(Progress(str(msg).strip(), cls.progress))

    @classmethod
    def warning(cls, msg: Union[Exception, str]):
        """Warnings to be displayed in GUI.

        Warnings, only inform user but do not interupt the program.

        Parameters
        ----------
        msg: str
            message text
        """
        cls.c_queue.put(Control("warning", str(msg)))

    @classmethod
    def exception(cls, msg: Union[Exception, str]):
        """Exceptions to be displayed in GUI.

        Exceptions can interupt running program, based on their severity.

        Parameters
        ----------
        msg: str
            message text
        """
        cls.c_queue.put(Control("exception", str(msg)))


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
            with SETTINGS_YML.open("w") as f:
                _settings_dict = yaml.dump(cls._settings_dict, f,
                                           default_flow_style=False,
                                           allow_unicode=True)

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
                log.debug("Accesing non-existent setting")
                return default
