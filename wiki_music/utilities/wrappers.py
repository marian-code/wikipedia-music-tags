import os
from functools import wraps
from threading import current_thread
import time  # lazy loaded
from typing import Callable, NoReturn, Union

from .sync import SharedVars
from .utils import module_path


def exception(logger):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    """
    def real_wrapper(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Unhandled golbal exception: {e}")
                SharedVars.exception(f"Unhandled golbal exception: {e}")

        return wrapper
    return real_wrapper


def synchronized(lock):
    """ Synchronization decorator. """

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


def warning(logger):
    """ A decorator that wraps the passed in function and logs
    exceptions should one occur
    """

    def real_wrapper(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except AttributeError as e:
                logger.warning(e)
                SharedVars.warning(e)
            except Exception as e:
                logger.warning(e)
                SharedVars.warning(e)

        return wrapper
    return real_wrapper


class Timer:
    start: float
    end: float

    def __init__(self, function_name: str) -> None:
        self.function_name = function_name
        self.path = os.path.join(module_path(), "profiling", "timing_stats.txt")
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


def time_methods(function):
    """ A decorator that wraps the passed in function and function exec time.
    """
    @wraps(function)
    def wrapper(*args, **kwargs) -> Callable:
        with Timer(function.__name__):
            return function(*args, **kwargs)

    return wrapper


def for_all_methods(decorator, exclude: list = []) -> Callable:
    """ Decorates class methods, except the ones in excluded list. """

    @wraps(decorator)
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)) and attr not in exclude:
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate
