"""Fancy wrapper functions used in whole package."""

import logging
from functools import wraps
from threading import current_thread
from typing import TYPE_CHECKING, Any, Callable, List, NoReturn, Union

from wiki_music.constants import LOG_DIR

from .exceptions import ExceptionBase
from .sync import GuiLoggger

logging.getLogger(__name__)

if TYPE_CHECKING:
    from logging import Logger

__all__ = ["exception", "warning"]


def exception(logger: "Logger", show_GUI: bool = True) -> Callable:
    """Wraps the passed in function and logs exceptions should one occure.

    Messages are sent to gui through GuiLoggger and to logger. Application
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
                    GuiLoggger.exception(f"Unhandled golbal exception: {e}")

        return wrapper
    return real_wrapper


def warning(logger: "Logger", show_GUI: bool = True) -> Callable:
    """Catch and inform user of module defined exceptions.

    A decorator that wraps the passed in function and logs wiki_music defined
    errors to logger warning. Messages are sent to gui through GuiLoggger.

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
                    GuiLoggger.warning(e)

        return wrapper
    return real_wrapper
