import os
import logging


def get_logger(name, logfile, mode="a"):

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logfile, mode=mode)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    return log

# logger formater
formatter = logging.Formatter("%(asctime)s - %(levelname)s \n\t - "
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
_id = str(os.getpid())
log_lyrics = get_logger(_id, f"logs/wiki_music_lyrics_{_id}.log")
