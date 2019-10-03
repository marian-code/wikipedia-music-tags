import logging
from os import path, makedirs
from threading import get_ident

from wiki_music.constants.paths import LOG_DIR


def log_name(name: str) -> str:
    return path.join(LOG_DIR, f"wiki_music_{name}.log")


def get_logger(name: str, logfile: str, mode: str = "w") -> logging.Logger:

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logfile, mode=mode)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(FORMATTER)
    log.addHandler(fh)

    return log

# logger formater
FORMATTER = logging.Formatter("%(asctime)s - %(levelname)s \n\t - "
                              "pid = %(process)d \n\t - "
                              "proces name = %(processName)s \n\t - "
                              "module = %(module)s,"
                              "funcName = %(funcName)s \n\t - "
                              "%(message)s \n\t",
                              datefmt="%H:%M:%S")

# create dir to store logs
makedirs(LOG_DIR, exist_ok=True)

# loggging for app
log_app = get_logger('wiki_music_app', log_name("app"))

# logging for gui
log_gui = get_logger('wiki_music_GUI', log_name("GUI"))

# logging for ID3_tags, previously in mode='a'
log_tags = get_logger("wiki_music_tags", log_name("ID3_tags"))

# logging for parser, previously in mode='a'
log_parser = get_logger("wiki_music_parser", log_name("parser"))

# logging for lyrics
_id = str(get_ident())
log_lyrics = get_logger(_id, log_name(f"lyrics_{_id}"))
