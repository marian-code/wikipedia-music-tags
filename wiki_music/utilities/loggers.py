"""Logger initialization for package."""

import logging
from typing import Set

from wiki_music.constants.paths import LOG_DIR

logging.getLogger(__name__)

__all__ = ["set_log_handles"]

# logger formater
FFORMATTER = logging.Formatter("%(asctime)s - %(levelname)s \n\t - "
                               "thread name = %(threadName)s \n\t - "
                               "module = %(module)s,"
                               "funcName = %(funcName)s \n\t - "
                               "%(message)s \n\t",
                               datefmt="%H:%M:%S")

CFORMATTER = logging.Formatter("%(levelname)s - %(threadName)s - "
                               "%(funcName)s - %(message)s")

# create dir to store logs
LOG_DIR.mkdir(parents=True, exist_ok=True)


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

    return str(LOG_DIR / f"wiki_music_{name}.log")


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
            log = logging.getLogger(name)

            # ch = logging.StreamHandler()
            # ch.setLevel(level)
            # ch.setFormatter(CFORMATTER)

            # log.addHandler(ch)

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
                fh.setFormatter(FFORMATTER)

                log.addHandler(fh)

                already_set.add(log_name)
            finally:
                log.setLevel(level)

    return log
