import package_setup

if __name__ == "__main__":
    from utilities.utils import clean_logs
    clean_logs()

import lazy_import
import signal
from utilities.utils import (list_files, to_bool, we_are_frozen,
                             win_naming_convetion, flatten_set)

from utilities.loggers import log_app
from utilities.sync import SharedVars
from utilities.wrappers import exception
from wiki_music import parser


# add signal handler to exit gracefully
# upon Ctrl+C
def signal_handler(sig, frame):
    print('Captured Ctrl+C, exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

log_app.info("starting imports")

Fore = lazy_import.lazy_callable("colorama.Fore")
init = lazy_import.lazy_callable("colorama.init")
time = lazy_import.lazy_module("time")
os = lazy_import.lazy_module("os")
re = lazy_import.lazy_module("re")
sys = lazy_import.lazy_module("sys")
pickle = lazy_import.lazy_module("pickle")
functools = lazy_import.lazy_module("functools")

write_tags = lazy_import.lazy_callable("library.write_tags")
read_tags = lazy_import.lazy_callable("library.read_tags")
save_lyrics = lazy_import.lazy_callable("library.save_lyrics")

init(convert=True)

__all__ = ["get_lyrics", "get_wiki"]

log_app.info("finished imports")


def artists_assign(composers: list, artists: list) -> (list, list):

    for i in range(len(composers)):
        composers[i] = composers[i] + artists[i]
        # filter empty entries and sort
        composers[i] = sorted(list(filter(None, set(composers[i]))))
    artists = [[""] for _ in composers]

    return composers, artists


def genre_select(genres: list, GUI: bool) -> str:

    if not genres:
        print("\nInput genre:", Fore.CYAN, end="")
        genre = input()
        print(Fore.RESET)
    else:
        print(Fore.CYAN, "\nSpecify which genre you want to write:",
              Fore.RESET)
        for i in range(len(genres)):
            print(str(i + 1) + ". " + genres[i])

        print("Input number:", Fore.CYAN, end="")
        index = int(input()) - 1
        print(Fore.RESET)

        genre = genres[index]

    return genre


def log_print(msg_GREEN="", msg_WHITE="", print_out=True, describe_both=False):

    if not we_are_frozen() and print_out:
        if msg_GREEN != "":
            print(Fore.GREEN + "\n" + msg_GREEN + Fore.RESET)
        if msg_WHITE != "":
            print(msg_WHITE)

    log_app.info(msg_GREEN)
    if not describe_both:
        SharedVars.describe = msg_GREEN
    else:
        SharedVars.describe = msg_GREEN + msg_WHITE


@exception(log_app)
def get_wiki(GUI):

    # download wikipedia page
    if not SharedVars.offline_debbug:

        while parser.preload_running:
            time.sleep(0.05)

        print("Accessing Wikipedia...")
        SharedVars.describe = "Accessing Wikipedia"

        print("Searching for: " + Fore.GREEN + parser.album + Fore.WHITE +
              " by " + Fore.GREEN + parser.band + Fore.WHITE)
        SharedVars.describe = ("Searching for: " + parser.album +
                               " by " + parser.band)

        if not parser.wiki_downloaded:
            parser.get_wiki()

        log_print(msg_GREEN="Found at: ", msg_WHITE=str(parser.url),
                  describe_both=True)

    else:
        fname = os.path.join("output", parser.album, 'page.pkl')
        if os.path.isfile(fname):
            infile = open(fname, 'rb')
            parser.page = pickle.load(infile)
            log_print(msg_GREEN="Using offline cached page insted of web page")
        else:
            msg = ("Cannot find cached offline version of page. "
                   "Trying to get online version...")
            log_app.warning(msg)
            SharedVars.warning = msg
            log_print(msg_GREEN=msg)
            SharedVars.offline_debbug = False
            get_wiki(GUI)

    log_print(msg_WHITE="Cooking Soup")
    if not parser.soup_ready:
        parser.cook_soup()
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
        print("Creating directory to store results")
        SharedVars.describe = "Creating directory to store results"

        # create work dir
        if not os.path.exists(parser.debug_folder):
            os.makedirs(parser.debug_folder)

        # basic html textout for debug
        parser.basic_out()

    # print out page contents
    log_print(msg_GREEN="Found page contents",
              msg_WHITE="\n".join(parser.contents))

    # extract track list
    parser.get_tracks()

    # print out tracklist
    log_print(msg_GREEN="Found Track list(s)")

    for i, data in enumerate(parser.data_collect):
        print(f"Tracklist {i + 1}: {data[0][0]}")

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
        parser.selected_genre = genre_select(parser.genres, GUI=GUI)
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
        print(Fore.CYAN +
              "Do you want to assign artists to composers? (y/n)",
              Fore.RESET, end=" ")
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
        print(Fore.CYAN + "\nDo you want to find and save lyrics? (y/n): " +
              Fore.RESET, end="")
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

    # put data to list of dicts
    dict_data, writeable = parser.data_to_dict()

    # announce that main app thread has reached the barrier
    if GUI:
        SharedVars.barrier.wait()

    if writeable and not GUI:
        print(Fore.CYAN + "Write data to ID3 tags? (y/n): " +
              Fore.RESET, end="")
        write = to_bool(input())

        if write:
            # write data to ID3 tags
            for data in dict_data:
                write_tags(data, lyrics_only=False)

    log_print(msg_GREEN="Done")

    if we_are_frozen() and not GUI:
        input("\nPRESS ENTER TO CONTINUE...")
    return


@exception(log_app)
def get_lyrics(GUI):

    log_app.info("starting get_lyrics function")

    if not GUI:
        parser.read_files()

    if parser.album == "" or parser.album == " " or parser.album is None:
        print("No album tag was found, enter album name: " +
              Fore.GREEN, end="")
        parser.album = str(input())
        print(Fore.RESET)
    if parser.band == "" or parser.band == " " or parser.band is None:
        print("No artist tag was found, enter band name: " +
              Fore.GREEN, end="")
        parser.band = str(input())
        print(Fore.RESET)

    # find lyrics
    log_print(msg_GREEN="Searching for lyrics")

    save_lyrics(parser)

    log_app.info("data to dict")

    # put data to list of dicts
    dict_data, writeable = parser.data_to_dict()

    log_app.info("announcing done")
    SharedVars.describe = "Done"

    SharedVars.done = True

    log_app.info("wait barrier")

    # announce that main app thread has reached the barrier
    if GUI:
        SharedVars.barrier.wait()

    log_app.info("write data to tags")

    if writeable and not GUI:
        print(Fore.CYAN + "Write data to ID3 tags? (y/n): " +
              Fore.RESET, end="")
        write = to_bool(input())

        if write:

            # write data to ID3 tags
            for data in dict_data:
                write_tags(data, lyrics_only=True)

    log_print(msg_GREEN="Done")

    if we_are_frozen() and not GUI:
        input("\nPRESS ENTER TO CONTINUE...")

    return 0

if __name__ == "__main__":

    print(Fore.CYAN + "Download only lyrics? (y/n)", Fore.RESET, end="")
    only_lyrics = to_bool(input())
    print(Fore.CYAN + "Write json save file? (y/n)", Fore.RESET, end="")
    SharedVars.write_json = to_bool(input())
    print(Fore.CYAN + "Offline debbug? (y/n)", Fore.RESET, end="")
    SharedVars.offline_debbug = to_bool(input())

    parser.work_dir = os.getcwd()
    parser.files = list_files(parser.work_dir)

    if only_lyrics:
        get_lyrics(GUI=False)
    else:
        print("Enter album name: " + Fore.GREEN, end="")
        parser.album = str(input())
        print(Fore.RESET + "Enter band name: " + Fore.GREEN, end="")
        parser.band = str(input())
        print(Fore.RESET)
        get_wiki(GUI=False)
