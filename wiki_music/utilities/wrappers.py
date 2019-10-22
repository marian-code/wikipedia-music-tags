"""Fancy wrapper functions used in whole package."""

import logging
import time  # lazy loaded
from functools import wraps
from threading import current_thread
from typing import TYPE_CHECKING, Any, Callable, List, NoReturn, Union

from wiki_music.constants import LOG_DIR

from .exceptions import ExceptionBase
from .sync import SharedVars

logging.getLogger(__name__)

if TYPE_CHECKING:
    from logging import Logger

__all__ = ["exception", "warning", "time_methods", "for_all_methods"]


def exception(logger: "Logger", show_GUI: bool = True) -> Callable:
    """Wraps the passed in function and logs exceptions should one occure.

    Messages are sent to gui through SharedVars and to logger. Application
    is not interupted.

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


def warning(logger: "Logger", show_GUI: bool = True) -> Callable:
    """Catch and inform user of module defined exceptions.

    A decorator that wraps the passed in function and logs wiki_music defined
    errors to logger warning. Messages are sent to gui through SharedVars.

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
            except ExceptionBase.registered_exceptions as e:
                logger.warning(e)
                if show_GUI:
                    SharedVars.warning(e)

        return wrapper
    return real_wrapper


class SimpleTimer:
    """Timing context manager. measures execution time of a function.

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
        self.path = LOG_DIR / "timing_stats.log"
        self.start = 0
        self.end = 0

        if not self.path.is_file():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("")

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()

        with self.path.open("w") as f:
            f.write(f"{current_thread().name:15} --> {self.function_name:30}"
                    f"{(self.end - self.start):8.4f}s\n")


class _Timer:
    """Timing context manager. measures execution time of a function.

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
        self.path = LOG_DIR / "timing_stats.log"
        self.start = 0
        self.end = 0

        if not self.path.is_file():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("")

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()

        with self.path.open("a") as f:
            f.write(f"{current_thread().name:15} --> {self.function_name:30}"
                    f"{(self.end - self.start):8.4f}s\n")


def time_methods(function: Callable) -> Callable:
    """Wraps the passed in function and measures execution time.

    Parameters
    ----------
    function: Callable
    """
    @wraps(function)
    def wrapper(*args, **kwargs) -> Callable:
        with _Timer(function.__name__):
            return function(*args, **kwargs)

    return wrapper


# TODO why exceptions are thrown for static methods??
def for_all_methods(decorator: Callable[[Any], Callable],
                    exclude: List[str] = []) -> Callable:
    """Decorates class methods, except the ones in excluded list.

    Warnings
    --------
    staticmetods of a class and inner classes must be excluded from decorating
    ofherwise exception is thrown.

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
