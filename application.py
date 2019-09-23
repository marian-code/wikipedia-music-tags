import signal

from lazy_import import lazy_callable, lazy_module

import package_setup
from wiki_music import parser
from wiki_music.constants.colors import CYAN, GREEN, RESET
from wiki_music.utilities import (SharedVars, exception, flatten_set,
                                  input_parser, log_app, to_bool,
                                  we_are_frozen)

if __name__ == "__main__":
    from utilities.utils import clean_logs
    clean_logs()


# add signal handler to exit gracefully
# upon Ctrl+C
def signal_handler(sig, frame):
    print('Captured Ctrl+C, exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

log_app.info("starting imports")

time = lazy_module("time")
sys = lazy_module("sys")
save_lyrics = lazy_callable("library.save_lyrics")

log_app.info("finished imports")

__all__ = ["get_lyrics", "get_wiki"]


def artists_assign(composers: list, artists: list) -> (list, list):

    for i in range(len(composers)):
        composers[i] = composers[i] + artists[i]
        # filter empty entries and sort
        composers[i] = sorted(list(filter(None, set(composers[i]))))
    artists = [[""] for _ in composers]

    return composers, artists


def genre_select(genres: list) -> str:

    if not genres:
        print(CYAN + "Input genre:", end="")
        genre = input()
    else:
        print(CYAN + "Specify which genre you want to write:")
        for i, gen in enumerate(genres, 1):
            print(f"{i}. {gen}")

        print("Input number:", CYAN, end="")
        index = int(input()) - 1

        genre = genres[index]

    return genre


def log_print(msg_GREEN="", msg_WHITE="", print_out=True, describe_both=False,
              level="INFO"):

    if not we_are_frozen() and print_out:
        if msg_GREEN != "":
            print(GREEN + "\n" + msg_GREEN)
        if msg_WHITE != "":
            print(msg_WHITE)

    if describe_both:
        msg = msg_GREEN + msg_WHITE
    else:
        msg = msg_GREEN

    if level == "INFO":
        log_app.info(msg_GREEN)
        SharedVars.info(msg)
    if level == "WARN":
        log_app.warning(msg_GREEN)
        SharedVars.warning = msg


def write_data(lyrics_only=False):

    print(CYAN + "Write data to ID3 tags? (y/n): " + RESET, end="")
    write = to_bool(input())

    if write:
        log_app.info("write data to tags")
        if not parser.write_tags(lyrics_only=lyrics_only):
            log_print(msg_WHITE="Cannot write tags because there are no "
                                "coresponding files")
        else:
            log_print(msg_GREEN="Done")


@exception(log_app)
def get_wiki(GUI: bool):

    # download wikipedia page
    if not SharedVars.offline_debbug:

        log_print(msg_WHITE="Accessing Wikipedia...")

        print("Searching for: " + GREEN + parser.album + RESET +
              " by " + GREEN + parser.band)
        SharedVars.describe = (f"Searching for: {parser.album} "
                               f"by {parser.band}")

    else:
        log_print(msg_GREEN="Using offline cached page insted of web page")

    error_msg = parser.get_wiki()
    if error_msg is not None:
        log_print(msg_GREEN=error_msg, level="WARN")
        return

    else:
        log_print(msg_GREEN="Found at: ", msg_WHITE=parser.url,
                  describe_both=True)

        log_print(msg_WHITE="Cooking Soup")

        error_msg = parser.cook_soup()
        if error_msg is not None:
            log_print(msg_GREEN=error_msg, level="WARN")

            return
        else:
            log_print(msg_WHITE="Soup ready")

    # get page contents
    parser.get_contents()

    # find release date
    parser.get_release_date()
    log_print(msg_GREEN="Found release date", msg_WHITE=parser.release_date)

    # find list of genres
    parser.get_genres()
    log_print(msg_GREEN="Found genre(s)", msg_WHITE="\n".join(parser.genres))

    if GUI:
        # download cover art from wikipedia
        parser.get_cover_art()
        log_print(msg_GREEN="Found cover art")

    if not we_are_frozen():
        log_print(msg_WHITE="Creating directory to store results")

        # basic html textout for debug
        parser.basic_out()

    # print out page contents
    log_print(msg_GREEN="Found page contents",
              msg_WHITE="\n".join(parser.contents))

    # extract track list
    parser.get_tracks()

    # print out tracklist
    log_print(msg_GREEN="Found Track list(s)")

    for i, data in enumerate(parser.data_collect, 1):
        print(f"Tracklist {i}: {data[0][0]}")

    # process track list
    log_print(msg_GREEN="Processing tracks", print_out=False)
    parser.process_tracks()

    # extract personel names
    log_print(msg_GREEN="Extracting additional personnel", print_out=False)
    parser.get_personnel()

    # print out additional personnel
    log_print(msg_GREEN="Found aditional personel")
    if not we_are_frozen():
        print(parser.personnel_2_str())

    # complete artists names
    log_app.info("complete 1")
    parser.complete()

    # look for aditional artists in brackets behind track names and
    # complete artists names again with new info
    log_app.info("info tracks")
    parser.info_tracks()

    # extract writers, composers
    log_print(msg_GREEN="Extracting composers", print_out=False)
    parser.get_composers()

    # complete artists names
    log_app.info("complete 2")
    parser.complete()

    log_print(msg_GREEN="Found composers",
              msg_WHITE="\n".join(flatten_set(parser.composers)))

    if not we_are_frozen():
        # save to files
        log_app.info("disc write")
        parser.disk_write()

        # print out found tracklist
        log_print(msg_GREEN="Found Track list(s)")
        parser.print_tracklist()

    # merge artists and personel which have some apperences
    # TODO not all personnel are inevitably artists some might be composers
    log_app.info("merge artists and personnel")
    parser.merge_artist_personnel()

    log_app.info("select genre")
    # select genre
    if len(parser.genres) == 1:
        parser.selected_genre = parser.genres[0]
    elif not GUI:
        parser.selected_genre = genre_select(parser.genres)
    else:
        if not parser.genres:
            SharedVars.describe = "Input genre"
        else:
            SharedVars.describe = "Select genre"

        SharedVars.switch = "genres"
        SharedVars.wait = True
        log_app.info("waiting for input from gui")

        while SharedVars.wait:
            time.sleep(0.1)

    log_app.info("decide artists")
    # decide what to do with artists
    if not GUI:
        print(CYAN + "Do you want to assign artists to composers? (y/n)",
              RESET, end=" ")
        SharedVars.assign_artists = to_bool(input())
    else:
        SharedVars.describe = "Assign artists to composers"

        # first load already known values to GUI
        # wait must be set before load,
        # otherwise if statement in gui wont be entered
        SharedVars.wait = True
        SharedVars.load = True

        while SharedVars.wait:
            time.sleep(0.1)

        SharedVars.switch = "comp"
        SharedVars.wait = True
        while SharedVars.wait:
            time.sleep(0.1)

    if SharedVars.assign_artists:
        parser.composers, parser.artists = artists_assign(parser.composers,
                                                          parser.artists)

    log_app.info("decide lyrics")
    # decide if you want to find lyrics
    if not GUI:
        print(CYAN + "\nDo you want to find and save lyrics? (y/n): " +
              RESET, end="")
        SharedVars.write_lyrics = to_bool(input())
    else:
        print("\n")
        SharedVars.describe = "Searching for Lyrics"
        SharedVars.switch = "lyrics"
        SharedVars.wait = True
        while SharedVars.wait:
            time.sleep(0.1)

    # download lyrics
    if SharedVars.write_lyrics:
        save_lyrics(parser)
    else:
        parser.lyrics = [""] * len(parser.tracks)

    SharedVars.done = True

    # announce that main app thread has reached the barrier
    if GUI:
        SharedVars.barrier.wait()
    else:
        write_data()

    if we_are_frozen() and not GUI:
        input("\nPRESS ENTER TO CONTINUE...")


@exception(log_app)
def get_lyrics(GUI: bool):

    log_app.info("starting get_lyrics function")

    if not GUI:
        parser.read_files()

    # find lyrics
    log_print(msg_GREEN="Searching for lyrics")

    save_lyrics(parser)

    log_app.info("announcing done")
    SharedVars.describe = "Done"

    SharedVars.done = True

    log_app.info("wait barrier")

    # announce that main app thread has reached the barrier
    if GUI:
        SharedVars.barrier.wait()
    else:
        write_data(lyrics_only=True)

    if not we_are_frozen() and not GUI:
        input("\nPRESS ENTER TO CONTINUE...")

if __name__ == "__main__":

    (SharedVars.write_json, SharedVars.offline_debbug, only_lyrics,
     parser.album, parser.band, parser.work_dir) = input_parser()

    parser.list_files()

    if parser.album is None:
        print(GREEN + "Enter album name: " + RESET, end="")
        parser.album = str(input())
    if parser.band is None:
        print(GREEN + "Enter band name: " + RESET, end="")
        parser.band = str(input())
    print(RESET)

    if only_lyrics:
        get_lyrics(GUI=False)
    else:
        get_wiki(GUI=False)
