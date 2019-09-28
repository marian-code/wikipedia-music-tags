import re
from os.path import join, split
from typing import Dict, Optional, Union

from mutagen import MutagenError

from wiki_music.constants.colors import GREEN, LRED, LYELLOW, RED, RESET
from wiki_music.constants.tags import TAGS
from wiki_music.library import tags_handler as taglib
from wiki_music.utilities import SharedVars, exception, log_tags

__all__ = ["read_tags", "write_tags"]


@exception(log_tags)
def write_tags(data: Dict[str, Union[str, float, list]], lyrics_only: bool):

    def write(tag, value=None):

        if value is None:
            value = data[tag]

        if isinstance(value, list):
            if len(value) == 1:
                value = value[0]
            else:
                value = ", ".join(value)
        if isinstance(value, (int, float)):
            value = str(value)

        song.tags[tag] = value

    if not data["FILE"]:
        print(f"{data['TITLE']} {data['type']}" + LYELLOW +
              "does not have matching file!")
        return

    try:
        song = taglib.File(data["FILE"])
    except MutagenError as e:
        print(f'Couldn´t open file {data["FILE"]} for writing')
        SharedVars.exception(e)
        log_tags.exception(e)
    else:

        if lyrics_only:
            print(GREEN + "Writing lyrics to:" + RESET, data["FILE"])
            write("LYRICS")

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
                    write(t)

            write("COMMENT", "")

        try:
            song.save()
        except (MutagenError, TypeError, ValueError) as e:
            print(f'Couldn´t save file {data["FILE"]}')
            SharedVars.exception(e)
            log_tags.exception(e)
        else:
            print(GREEN + "Tags written succesfully!")


@exception(log_tags)
def read_tags(song_file: str) -> Optional[dict]:

    try:
        song = taglib.File(song_file)
    except MutagenError as e:
        print(RED + "Error in reading file: " + RESET + song_file)
        SharedVars.exception(e)
        log_tags.exception(e)
        return None
    else:
        tags = dict(song.tags)

        if not tags["TITLE"]:
            path, f = split(song_file)
            # match digits, zero or one whitespace characters,
            # zero or one dot, zero or one dash,
            # zero or one whitespace characters
            f = re.sub(r"\d\s?\.?-?\s?", "", f)

            tags["TITLE"] = join(path, f).strip()

        for s in ("ARTIST", "COMPOSER"):
            tags[s] = sorted(re.split(r",\s?", tags[s]))

        return tags
