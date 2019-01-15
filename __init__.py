import package_setup
import os
import logging
from package_setup import we_are_frozen
from functools import wraps

from sync import info_exchange
shared_vars = info_exchange()

# logger formater
formatter = logging.Formatter("%(asctime)s - %(levelname)s \n\t - "
                              "pid = %(process)d \n\t - "
                              "proces name = %(processName)s \n\t - "
                              "module = %(module)s,"
                              "funcName = %(funcName)s \n\t - "
                              "%(message)s \n\t",
                              datefmt="%H:%M:%S")
# loggging for app
log_app = logging.getLogger('wiki_music_app')
log_app.setLevel(logging.DEBUG)
fh = logging.FileHandler(r'logs/wiki_music_app.log', mode='w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log_app.addHandler(fh)

# logging for gui
log_gui = logging.getLogger('wiki_music_GUI')
log_gui.setLevel(logging.DEBUG)
fh = logging.FileHandler(r'logs/wiki_music_GUI.log', mode='w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log_gui.addHandler(fh)

# logging for ID3_tags
log_tags = logging.getLogger("wiki_music_tags")
log_tags.setLevel(logging.DEBUG)
fh = logging.FileHandler(r"logs/wiki_music_ID3_tags.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log_tags.addHandler(fh)

# logging for parser
log_parser = logging.getLogger("wiki_music_parser")
log_parser.setLevel(logging.DEBUG)
fh = logging.FileHandler(r"logs/wiki_music_parser.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log_parser.addHandler(fh)

from libb.wiki_parse import wikipedia_parser
parser = wikipedia_parser()

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
                logger.exception(e)
                print(e)
                shared_vars.exception = e

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

"""
# switch off logging when GUI is not running
if we_are_frozen() == False:
    log_app.propagate = False
    log_gui.propagate = False
    log_parser.propagate = False
    log_tags.propagate = False
"""
