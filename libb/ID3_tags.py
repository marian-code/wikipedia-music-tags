import package_setup
import taglib
from colorama import Fore, init
from wiki_music import log_tags, shared_vars

init(convert=True)


def write_tags(data: dict, lyrics_only):

    def write(tag, value=None):
        try:
            if value is None:
                value = data[tag]

            if isinstance(value, list):
                value = ", ".join(value)

            if isinstance(value, (int, float)):
                value = str(value)
            
            song.tags[tag] = value
        except AttributeError as e:
            print(Fore.LIGHTRED_EX, "Probably encoding error!", Fore.RESET)
            print("Couldn´t write tag {} to file {}".format(tag, data["file"]))
            print(e)
            shared_vars.exception = e
            log_tags.exception(e)
        except Exception as e:
            print(Fore.RED, "Error in writing tags!", Fore.RESET)
            print("Couldn´t write tag {} to file {}".format(tag, data["file"]))
            print(e)
            shared_vars.exception = e
            log_tags.exception(e)

    if data["file"] is None:
        print(data["TITLE"] + " " + data["type"] + Fore.LIGHTYELLOW_EX +
              "does not have matching file!" + Fore.RESET)
        return 0

    print(data["file"])

    if lyrics_only is False:
        print(Fore.GREEN + "Writing tags to: " + Fore.RESET, data["file"])
    else:
        print(Fore.GREEN + "Writing lyrics to: " + Fore.RESET, data["file"])

    try:
        song = taglib.File(data["file"])
    except Exception as e:
        print("Couldn´t open file {} for writing".format(data["file"]))
        print(e)
        shared_vars.exception = e
        log_tags.exception(e)

    if lyrics_only is False:

        # easy tags
        write("ALBUM")
        write("ALBUMARTIST")
        write("COMPOSER")
        write("DATE")
        write("DISCNUMBER")
        write("GENRE")
        write("COMMENT", "")
        write("TITLE", data["TITLE"] + " " + data["type"])
        write("TRACKNUMBER")

        # complicated tags
        if isinstance(data["ARTIST"], list):
            data["ARTIST"].append(data["ALBUMARTIST"])
            write("ARTIST", sorted(list(set(data["ARTIST"]))))
        elif isinstance(data["ARTIST"], str):
            if data["ARTIST"] == "" or data["ARTIST"] == " ":
                write("ALBUMARTIST")
            elif data["ALBUMARTIST"] != data["ARTIST"]:
                write("ARTIST", "{}, {}".format(data["ALBUMARTIST"],
                                                data["ARTIST"]))
            else:
                song.tags["ARTIST"] = [data["ALBUMARTIST"]]
        else:
            raise NotImplementedError("Unsupported data type for "
                                        "ARTIST tag")
    else:
        pass

    if ".m4a" in data["file"] or ".mp3" in data["file"]:
        write("LYRICS")
    else:
            write("UNSYNCEDLYRICS", data["LYRICS"])

    try:
        song.save()
    except Exception as e:
        print("Couldn´t save file {}".format(data["file"]))
        print(e)
        shared_vars.exception = e
        log_tags.exception(e)
    else:
        print(Fore.GREEN + "Tags written succesfully!", Fore.RESET)


def read_tags(song_file: str):

    def read_tag(TAG_ID):
        try:
            tag = song.tags[TAG_ID][0].strip()
        except:
            tag = ""
        finally:
            return tag

    try:
        song = taglib.File(song_file)
    except Exception as error:
        print(Fore.RED + "Can not read file:\n" + Fore.RESET + song_file)
        from wiki_music import shared_vars
        shared_vars.exception = str(error)
        log_tags.exception(error)
    else:
        album = read_tag("ALBUM")
        band = read_tag("ALBUMARTIST")
        artists = read_tag("ARTIST")
        composer = read_tag("COMPOSER")
        release_date = read_tag("DATE")
        disc_num = read_tag("DISCNUMBER")
        genre = read_tag("GENRE")
        # TODO apple losseles doesnt accept UNSYNCEDLYRICS !!
        # TODO this check might not be sufficient
        if ".m4a" in song_file or ".mp3" in song_file:
                lyrics = read_tag("LYRICS")
        else:
                lyrics = read_tag("UNSYNCEDLYRICS")
        track = read_tag("TITLE")
        number = read_tag("TRACKNUMBER")

    return (album, band, artists, composer, release_date,
            disc_num, genre, lyrics, track, number)
