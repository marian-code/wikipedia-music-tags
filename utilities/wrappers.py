import os
from time import perf_counter
from functools import wraps
from threading import current_thread
from .sync import SharedVars


def exception(logger):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    """
    def real_wrapper(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as e:
                e = f"Unhandled golbal exception: {e}"
                logger.exception(e)
                print(e)
                SharedVars.exception = str(e)

        return wrapper
    return real_wrapper


def synchronized(lock):
    """ Synchronization decorator. """

    def real_wrapper(function):
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

    def real_wrapper(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except AttributeError as e:
                print(e)
                logger.warning(e)
                SharedVars.warning = str(e)
            except Exception as e:
                print(e)
                logger.warning(e)
                SharedVars.warning = str(e)

        return wrapper
    return real_wrapper


class Timer:

    def __init__(self, function_name):
        self.function_name = function_name
        self.start = 0
        self.end = 0

    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, *args):
        self.end = perf_counter()
        with open(os.path.join("profiling", "timing_stats.txt"), "a") as f:
            f.write(f"{current_thread().name:15} --> {self.function_name:30}"
                    f"{(self.end - self.start):8.4f}s\n")


def time_methods(function):
    """ A decorator that wraps the passed in function and function exec time.
    """
    @wraps(function)
    def wrapper(*args, **kwargs):
        with Timer(function.__name__):
            return function(*args, **kwargs)

    return wrapper


def for_all_methods(decorator, exclude=[]):
    """ Decorates class methods, except the ones in excluded list. """

    @wraps(decorator)
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)) and attr not in exclude:
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate
