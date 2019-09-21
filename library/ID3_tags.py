import re
import sys

from colorama import Fore, init
from os.path import join, split

from utilities.loggers import log_tags
from utilities.sync import SharedVars
from utilities.wrappers import exception
from wiki_music import TAGS

_version = sys.version_info

if _version.major == 3:
    if _version.minor == 6:
        from pytaglib import taglib  # pylint: disable=import-error
    if _version.minor == 7:
        import library.tags_handler as taglib
else:
    raise NotImplementedError("Wikimusic only supports python "
                              "versions=(3.6, 3.7)")

init(convert=True, autoreset=True)

__all__ = ["read_tags", "write_tags"]


@exception(log_tags)
def write_tags(data: dict, lyrics_only):

    def write(tag, value=None):

        if tag == "LYRICS":
            if not data["FILE"].endswith((".m4a", ".mp3")):
                tag = "UNSYNCEDLYRICS"
                value = data["LYRICS"]

        try:
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
        except AttributeError as e:
            print(Fore.LIGHTRED_EX, "Probably encoding error!")
            print(f'Couldn´t write tag {tag} to file {data["FILE"]}')
            print(e)
            SharedVars.exception = e
            log_tags.exception(e)
        except Exception as e:
            print(Fore.RED, "Error in writing tags!")
            print(f'Couldn´t write tag {tag} to file {data["FILE"]}')
            print(e)
            SharedVars.exception = e
            log_tags.exception(e)

    if data["FILE"] is None:
        print(data["TITLE"] + " " + data["type"] + Fore.LIGHTYELLOW_EX +
              "does not have matching file!")
        return

    if not lyrics_only:
        print(Fore.GREEN + "Writing tags to:" + Fore.RESET, data["FILE"])
    else:
        print(Fore.GREEN + "Writing lyrics to:" + Fore.RESET, data["FILE"])

    try:
        song = taglib.File(data["FILE"])
    except Exception as e:
        print(f'Couldn´t open file {data["FILE"]} for writing')
        print(e)
        SharedVars.exception = e
        log_tags.exception(e)

    if not lyrics_only:

        # preprocess data
        if isinstance(data["ARTIST"], list):
            data["ARTIST"].append(data["ALBUMARTIST"])
            data["ARTIST"] = sorted(list(set(data["ARTIST"])))
        elif isinstance(data["ARTIST"], str):
            if data["ALBUMARTIST"] != data["ARTIST"] and data["ARTIST"] != "":
                data["ARTIST"] = f'{data["ALBUMARTIST"]}, {data["ARTIST"]}'
            else:
                data["ARTIST"] = data["ALBUMARTIST"]
        else:
            raise NotImplementedError("Unsupported data type for ARTIST tag")

        data["TITLE"] = f"{data['TITLE']} {data['TYPE']}"

        # write tags
        for t in TAGS:
            write(t)

        write("COMMENT", "")
    else:
        write("LYRICS")

    try:
        song.save()
    except Exception as e:
        print(f'Couldn´t save file {data["FILE"]}')
        print(e)
        SharedVars.exception = e
        log_tags.exception(e)
    else:
        print(Fore.GREEN + "Tags written succesfully!")


@exception(log_tags)
def read_tags(song_file: str) -> tuple:

    def read_tag(TAG_ID):

        if TAG_ID == "LYRICS":
            if not song_file.endswith((".m4a", ".mp3")):
                TAG_ID = "UNSYNCEDLYRICS"

        try:
            tag = song.tags[TAG_ID][0].strip()
        except:
            tag = ""
        finally:
            if TAG_ID in ("ARTIST", "COMPOSER"):
                return sorted(re.split(r",\s?", tag))
            else:
                return tag

    try:
        song = taglib.File(song_file)
    except Exception as e:
        print(Fore.RED + "Can not read file: " + Fore.RESET + song_file)
        SharedVars.exception = str(e)
        log_tags.exception(e)
    else:
        tags_dict = dict()

        for t in TAGS:
            tags_dict[t] = read_tag(t)

        # if no title was loadaed use filename
        if tags_dict["TITLE"] in ("", " ", None):
            path, f = split(song_file)
            # match digits, zero or one whitespace characters, zero or one dot,
            # zero or one dash, zero or one whitespace characters
            f = re.sub(r"\d\s?\.?-?\s?", "", f)

            tags_dict["TITLE"] = join(path, f)

    return tags_dict
