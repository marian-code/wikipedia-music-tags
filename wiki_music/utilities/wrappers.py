""" Fancy wrapper function used in whole package. """

import os
import time  # lazy loaded
from functools import wraps
from threading import current_thread
from typing import Callable, NoReturn, Union, Any, List, TYPE_CHECKING

from .sync import SharedVars
from .exceptions import *
from wiki_music.constants import LOG_DIR

if TYPE_CHECKING:
    from logging import Logger
    from threading import Lock


def exception(logger: "Logger", show_GUI: bool = True) -> Callable:
    """
    A decorator that wraps the passed in function and logs exceptions should
    one. Messages are sent to gui through SharedVars and to logger.

    Warnings
    --------
    Use with caution, only on critical parts of the code and not in early
    development stage as it will hide code errors

    Parameters
    ----------
    logger: logging.Logger
        logger instance whih will be recording occured errors
    show_GUI: bool
        whether to show the exception message in GUI messagebox

    Returns
    -------
    Callable
        wrapped callable which will not crash app when it raises error
    """
    def real_wrapper(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Unhandled golbal exception: {e}")
                if show_GUI:
                    SharedVars.exception(f"Unhandled golbal exception: {e}")

        return wrapper
    return real_wrapper


def synchronized(lock: "Lock") -> Callable:
    """ Synchronization decorator. Syncs all callables wrapped by this
    decorator which are passed the same lock

    Warnings
    --------
    Do not use on computationally heavy functions, as this could cause GUI
    freezing. When dealing with such functions always lock only single
    variables
    
    Parameters
    ----------
    lock: threading.Lock
        lock instance

    Returns
    -------
    Callable
        callable synchronized with passed lock
    """

    def real_wrapper(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args, **kwargs):
            lock.acquire()
            try:
                return function(*args, **kwargs)
            finally:
                lock.release()
        return wrapper
    return real_wrapper


def warning(logger: "Logger", show_GUI: bool = True) -> Callable:
    """
    A decorator that wraps the passed in function and logs AttributeErrors
    to logger warning and Exceptions to logger exceptions. Messages are sent to
    gui through SharedVars and to logger.

    Warnings
    --------
    Use with caution, only on critical parts of the code and not in early
    development stage as it will hide code errors

    Parameters
    ----------
    logger: logging.Logger
        logger instance whih will be recording occured errors
    show_GUI: bool
        whether to show the warning message in GUI messagebox

    Returns
    -------
    Callable
        wrapped callable which will not crash app when it raises error
    """

    def real_wrapper(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except (NoTracklistException, NoReleaseDateException,
                    NoGenreException, NoCoverArtException,
                    NoNames2ExtractException, NoContentsException,
                    NoPersonnelException, NoGoogleApiKeyException) as e:
                logger.warning(e)
                if show_GUI:
                    SharedVars.warning(e)

        return wrapper
    return real_wrapper


class Timer:
    """ Timing context manager. measures execution time of a function.

    Parameters
    ----------
    function_name: str
        name of the timed function that will be visible in log

    Attributes
    ----------
        start: float
            execution start time
        end: float
            excecution end time
        path: string
            string contining path to file where results are logged
    """

    start: float
    end: float

    def __init__(self, function_name: str) -> None:
        self.function_name = function_name
        self.path = os.path.join(LOG_DIR, "timing_stats.log")
        self.start = 0
        self.end = 0

        if not os.path.isfile(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w") as f:
                f.write("")

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()

        with open(self.path, "a") as f:
            f.write(f"{current_thread().name:15} --> {self.function_name:30}"
                    f"{(self.end - self.start):8.4f}s\n")


def time_methods(function: Callable) -> Callable:
    """ A decorator that wraps the passed in function and measures execution
    time.

    Parameters
    ----------
    function: Callable
    """
    @wraps(function)
    def wrapper(*args, **kwargs) -> Callable:
        with Timer(function.__name__):
            return function(*args, **kwargs)

    return wrapper


def for_all_methods(decorator: Callable[[Any], Callable],
                    exclude: List[str] = []) -> Callable:
    """ Decorates class methods, except the ones in excluded list.

    Warnings
    --------
    staticmetods of a class and inner classes must be excluded from decorating
    ofherwise exception is thrown.

    Todo
    ----
    why exceptions are thrown??

    References
    ----------
    https://stackoverflow.com/questions/6307761/how-to-decorate-all-functions-of-a-class-without-typing-it-over-and-over-for-eac
    
    Parameters
    ----------
    decorator: Callable
        Callable which will be used to decorate class methods
    exclude: List[str]
        list of method names to exclude from decorating
    """

    @wraps(decorator)
    def decorate(cls: Callable) -> Callable:
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)) and attr not in exclude:
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate
