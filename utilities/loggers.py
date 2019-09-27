import logging
from threading import get_ident


def get_logger(name: str, logfile: str, mode: str = "a") -> logging.Logger:

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

# loggging for app
log_app = get_logger('wiki_music_app', r'logs/wiki_music_app.log', mode="w")

# logging for gui
log_gui = get_logger('wiki_music_GUI', r'logs/wiki_music_GUI.log', mode="w")

# logging for ID3_tags
log_tags = get_logger("wiki_music_tags", r"logs/wiki_music_ID3_tags.log")

# logging for parser
log_parser = get_logger("wiki_music_parser", r"logs/wiki_music_parser.log")

# logging for lyrics
_id = str(get_ident())
log_lyrics = get_logger(_id, f"logs/wiki_music_lyrics_{_id}.log")
