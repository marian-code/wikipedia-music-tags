"""Logger initialization for package."""

import logging
from os import makedirs, path
from typing import Set

from wiki_music.constants.paths import LOG_DIR

logging.getLogger(__name__)

__all__ = ["set_log_handles"]

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


def _compile_log_path(name: str) -> str:
    """Compiles standard logger path consisting of wiki_music_{name}.log

    Parameters
    ----------
    name: str
        unique logger name

    Returns
    -------
    str
        compiled logger path name
    """

    return path.join(LOG_DIR, f"wiki_music_{name}.log")


def set_log_handles(level: int):
    """Set desired level for package loggers and add file handlers.

    Parameters
    ----------
    level: int
        logging level
    """

    already_set: Set[str] = set()
    for name in logging.root.manager.loggerDict:
        if "wiki_music" in name:
            # assumed format is wiki_music.<submodule>.<subsubmodule>.<...>
            try:
                log_name = name.split(".")[1]
            except IndexError:
                pass
            else:
                if log_name in already_set:
                    continue

                log_path = _compile_log_path(log_name)

                fh = logging.FileHandler(log_path, mode="w")
                fh.setLevel(level)
                fh.setFormatter(FORMATTER)

                log = logging.getLogger(name)
                log.setLevel(level)
                log.addHandler(fh)

                already_set.add(log_name)

    return log
