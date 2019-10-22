"""Expose high level tag writing and reading functions."""

import logging
import re  # lazy loaded
from os import path
from pathlib import Path
from typing import Dict, Optional, Union

import mutagen  # lazy loaded

from wiki_music.constants.colors import GREEN, RED, RESET, YELLOW
from wiki_music.constants.tags import TAGS
from . import tags_handler
from wiki_music.utilities import (TagReadException, TagSaveException,
                                  exception, warning)

__all__ = ["read_tags", "write_tags", "supported_tags"]

log = logging.getLogger(__name__)


def supported_tags():
    """Print a list of wiki_music supported tags."""
    print("wiki_music supports these tags:")
    print(", ".join(TAGS))


# TODO someting is wrong with m4q lyrics reading
@exception(log)
@warning(log)
def write_tags(data: Dict[str, Union[str, float, list, bytes]]):
    """Convenience function which takes care of writing data to tags.

    See also
    --------
    :const:`wiki_music.constants.tags.TAGS`
        for list of supported tags
    :mod:`wiki_music.library.tags_handler`
        low level implemetation of tags handling built on mutagen library

    Parameters
    ----------
    data: dict
        containes dictionary of tag names and coresponding values
    """
    if not data["FILE"]:
        print(f"{data['TITLE']} {data['type']}" + YELLOW +
              f"does not have matching file!")
        return

    try:
        song = tags_handler.File(data["FILE"])
    except mutagen.MutagenError:
        raise TagReadException(f"Couldn´t open file {data['FILE']} "
                               f"for writing")
    else:

        print(GREEN + "Writing tags to:" + RESET, data["FILE"])

        # preprocess data
        if isinstance(data["ARTIST"], list):
            data["ARTIST"].append(data["ALBUMARTIST"])
        elif isinstance(data["ARTIST"], str):
            data["ARTIST"] = [data["ALBUMARTIST"], data["ARTIST"]]
        else:
            raise NotImplementedError("Unsupported data type for "
                                      "ARTIST tag")

        data["ARTIST"] = sorted(list(set(data["ARTIST"])))
        if data["TYPE"]:
            data["TITLE"] = f"{data['TITLE']} {data['TYPE']}"

        # write tags, except file and type,
        # these don't belong in music tags
        for t in TAGS:
            if t not in ("FILE", "TYPE"):
                song.tags[t] = data[t]

        song.tags[t] = ""

        try:
            song.save()
        except (mutagen.MutagenError, TypeError, ValueError):
            raise TagSaveException(f'Couldn´t save file {data["FILE"]}')
        else:
            print(GREEN + "Tags written succesfully!")


@exception(log)
@warning(log)
def read_tags(song_file: Path) -> Dict[str, Union[str, list, bytes]]:
    """Convenience function which takes care of reading tags from file.

    Abstracts away from low level mutagen API. If no tags are read, function
    can guess track title from file name, assumming some decent formating.

    See also
    --------
    :const:`wiki_music.constants.tags.TAGS`
        for list of supported tags
    :mod:`wiki_music.library.tags_handler`
        low level implemetation of tags handling built on mutagen library

    Parameters
    ----------
    song_file: Path
        path to song on disk

    Returns
    -------
    dict
        dictionary of tag labels with coresponding values if the file could be
        loaded. If not then the dictionary is empty
    """
    try:
        song = tags_handler.File(song_file)
    except mutagen.MutagenError:
        tags = {}
        raise TagReadException(f"Error in reading file: {song_file.resolve()}")
    else:
        # convert selective dict to normal dict, selectivness is needed only
        # for writing tags
        tags = dict(song.tags)

        if not tags["TITLE"]:
            f = str(Path(song_file).stem)
            # match digits, zero or one whitespace characters,
            # zero or one dot, zero or one dash,
            # zero or one whitespace characters
            tags["TITLE"] = re.sub(r"\d\s?\.?-?\s?", "", f).strip()

    finally:
        return tags
