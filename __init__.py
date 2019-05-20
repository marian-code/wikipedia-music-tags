import package_setup
import os
import logging
from package_setup import we_are_frozen
from functools import wraps
from utils import module_path

from sync import InfoExchange
shared_vars = InfoExchange()

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

# logging for lyrics
log_lyrics = logging.getLogger(str(os.getpid()))
log_lyrics.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs/wiki_music_lyrics_{}.log".format(os.getpid()))
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log_lyrics.addHandler(fh)

# must be here after loggers, otherwise parser imports fail
# because things that parser imports are not yet initialized
from libb.wiki_parse import WikipediaParser  # noqa E402
parser = WikipediaParser()

# load google api key for lyrics search
_file = os.path.join(module_path(), "files", "google_api_key.txt")
try:
    f = open(_file, "r")
    google_api_key = f.read().strip()
except Exception:
    raise Exception("You must input Google api key. Refer to repository "
                    "for instructions "
                    "https://github.com/marian-code/wikipedia-music-tags")


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
