import package_setup
import lazy_import
import signal
from utils import (list_files, to_bool, we_are_frozen,
                   win_naming_convetion, flatten_set)

if __name__ == '__main__':
    from utils import clean_logs
    clean_logs()

from wiki_music import parser, shared_vars, log_app, info_exchange


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

write_tags = lazy_import.lazy_callable("libb.ID3_tags.write_tags")
read_tags = lazy_import.lazy_callable("libb.ID3_tags.read_tags")
save_lyrics = lazy_import.lazy_callable("libb.lyrics.save_lyrics")

init(convert=True)

log_app.info("finished imports")


def artists_assign(composers: list, artists: list) -> (list, list):

    for i in range(len(composers)):
        composers[i] = composers[i] + artists[i]
        # filter empty entries and sort
        composers[i] = sorted(list(filter(None, set(composers[i]))))
    artists = [[""] for _ in range(len(composers))]

    return composers, artists


def genre_select(genres: list, GUI: bool) -> str:

    if len(genres) == 0:
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

    if we_are_frozen() is False and print_out is True:
        if msg_GREEN != "":
            print(Fore.GREEN + "\n" + msg_GREEN + Fore.RESET)
        if msg_WHITE != "":
            print(msg_WHITE)

    log_app.info(msg_GREEN)
    if describe_both is False:
        shared_vars.describe = msg_GREEN
    else:
        shared_vars.describe = msg_GREEN + msg_WHITE


def exception(function):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            e = "Unhandled golbal exception: " + str(e)
            print(e)
            log_app.exception(e)
            shared_vars.exception = e

    return wrapper


@exception
def MAIN(band, album, work_dir, GUI):

    parser.album = album.title()
    parser.band = band.title()
    parser.debug_folder = win_naming_convetion(parser.album, dir_name=True)

    # download wikiedia page
    if shared_vars.offline_debbug is False:
        print("Accessing Wikipedia...")
        shared_vars.describe = "Accessing Wikipedia"

        print("Searching for: " + Fore.GREEN + parser.album + Fore.WHITE +
              " by " + Fore.GREEN + parser.band + Fore.WHITE)
        shared_vars.describe = ("Searching for: " + parser.album +
                                " by " + parser.band)

        parser.WIKI()

        log_print(msg_GREEN="Found at: ",
                  msg_WHITE=str(parser.url),
                  describe_both=True)

    else:
        fname = os.path.join(parser.album, 'page.pkl')
        try:
            infile = open(fname, 'rb')
            parser.page = pickle.load(infile)
        except FileNotFoundError as e:
            print(e)
            log_app.exception(e)
            shared_vars.exception = e
            sys.exit(0)

        log_print(msg_GREEN="Using offline file insted of web page")

    log_print(msg_WHITE="Cooking Soup")
    parser.cook_soup()
    log_print(msg_WHITE="Soup ready")

    if parser.check_BAND() is False:
        shared_vars.wait_exit = True
        while shared_vars.wait_exit is True:
            time.sleep(0.01)

        # If user wants to terminate program, the GUI
        #  makes the application thread throw exception and exit
        assert shared_vars.terminate_app is False
    else:
        log_print(msg_WHITE="Band check OK, parsing")

    # find release date
    parser.RELEASE_DATE()
    log_print(msg_GREEN="Found release date",
              msg_WHITE=parser.release_date)

    # find list of genres
    parser.GENRES()
    log_print(msg_GREEN="Found genre(s)",
              msg_WHITE="\n".join(parser.genres))

    if GUI is True:
        # download cover art from wikipedia
        parser.COVER_ART()
        log_print(msg_GREEN="Found cover art")

    if we_are_frozen() is False:
        print("Creating directory to store results")
        shared_vars.describe = "Creating directory to store results"

        # create work dir
        if not os.path.exists(parser.debug_folder):
            os.makedirs(parser.debug_folder)

        # basic html textout for debug
        parser.BASIC_OUT()

    # get page contents
    parser.CONTENTS()

    # print out page contents
    log_print(msg_GREEN="Found page contents",
              msg_WHITE="\n".join(parser.contents))

    # extract track list
    parser.TRACKS()

    # print out tracklist
    log_print(msg_GREEN="Found Track list(s)")
    i = 1
    for data in parser.data_collect:
        print("Tracklist " + str(i) + ": " + data[0][0])
        i += 1

    # process track list
    log_print(msg_GREEN="Processing tracks", print_out=False)
    parser.process_TRACKS()

    # extract personel names
    log_print(msg_GREEN="Extracting additional personnel", print_out=False)
    parser.PERSONNEL()

    # print out additional personnel
    log_print(msg_GREEN="Found aditional personel")
    if we_are_frozen() is False:
        parser.print_personnel()

    # complete artists names
    log_app.info("complete 1")
    parser.COMPLETE()

    # look for aditional artists in brackets behind track names and
    # complete artists names again with new info
    log_app.info("info tracks")
    parser.info_TRACKS()

    # extract writers, composers
    log_print(msg_GREEN="Extracting composers", print_out=False)
    parser.COMPOSERS()
    log_print(msg_GREEN="Found composers",
              msg_WHITE="\n".join(flatten_set(parser.composers)))

    # complete artists names
    log_app.info("complete 2")
    parser.COMPLETE()

    if we_are_frozen() is False:
        # save to files
        log_app.info("disc write")
        parser.DISK_WRITE()

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
    elif GUI is False:
        parser.selected_genre = genre_select(parser.genres, GUI=GUI)
    else:
        if len(parser.genres) == 0:
            shared_vars.describe = "Input genre"
        else:
            shared_vars.describe = "Select genre"

        shared_vars.switch = "genres"
        shared_vars.wait = True
        log_app.info("waiting for input from gui")

        while shared_vars.wait is True:
            time.sleep(0.1)

    log_app.info("decide artists")
    # decide what to do with artists
    if GUI is False:
        print(Fore.CYAN +
              "Do you want to assign artists to composers? (y/n)",
              Fore.RESET, end=" ")
        shared_vars.assign_artists = to_bool(input())
    else:
        shared_vars.describe = "Assign artists to composers"

        # first load already known values to GUI
        # wait must be set before load,
        # otherwise if statement in gui wont be entered
        shared_vars.wait = True
        shared_vars.load = True

        while shared_vars.wait is True:
            time.sleep(0.1)

        shared_vars.switch = "comp"
        shared_vars.wait = True
        while shared_vars.wait is True:
            time.sleep(0.1)

    if shared_vars.assign_artists is True:
        parser.composers, parser.artists = artists_assign(parser.composers,
                                                          parser.artists)

    log_app.info("decide lyrics")
    # decide if you want to find lyrics
    if GUI is False:
        print(Fore.CYAN +
              "\nDo you want to find and save lyrics? (y/n): " +
              Fore.RESET, end="")
        shared_vars.write_lyrics = to_bool(input())
    else:
        print("\n")
        shared_vars.describe = "Searching for Lyrics"
        shared_vars.switch = "lyrics"
        shared_vars.wait = True
        while shared_vars.wait is True:
            time.sleep(0.1)

    # download lyrics
    if shared_vars.write_lyrics is True:
        save_lyrics()
    else:
        parser.lyrics = [""]*len(parser.tracks)

    shared_vars.done = True

    # put data to list of dicts
    dict_data, writeable = parser.data_to_dict()

    # announce that main app thread has reached the barrier
    if GUI is True:
        shared_vars.barrier.wait()

    if writeable is True and GUI is False:
        print(Fore.CYAN + "Write data to ID3 tags? (y/n): " +
              Fore.RESET, end="")
        write = to_bool(input())

        if write is True:
            # write data to ID3 tags
            for data in dict_data:
                write_tags(data, lyrics_only=False)

    log_print(msg_GREEN="Done")

    if we_are_frozen() is True and GUI is False:
        input("\nPRESS ENTER TO CONTINUE...")
    return 0


@exception
def LYRICS(work_dir, GUI):

    log_app.info("starting LYRICS function")

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

    save_lyrics()

    log_app.info("data to dict")

    # put data to list of dicts
    dict_data, writeable = parser.data_to_dict()

    log_app.info("announcing done")
    shared_vars.describe = "Done"

    shared_vars.done = True

    log_app.info("wait barrier")

    # announce that main app thread has reached the barrier
    if GUI is True:
        shared_vars.barrier.wait()

    log_app.info("write data to tags")

    if writeable is True and GUI is False:
        print(Fore.CYAN + "Write data to ID3 tags? (y/n): " +
              Fore.RESET, end="")
        write = to_bool(input())

        if write is True:

            # write data to ID3 tags
            for data in dict_data:
                write_tags(data, lyrics_only=True)

    log_print(msg_GREEN="Done")

    if we_are_frozen() is True and GUI is False:
        input("\nPRESS ENTER TO CONTINUE...")

    return 0

if __name__ == "__main__":

    print(Fore.CYAN + "Download only lyrics? (y/n)", Fore.RESET, end="")
    only_lyrics = str(input())
    print(Fore.CYAN + "Write json save file? (y/n)", Fore.RESET, end="")
    shared_vars.write_json = to_bool(input())
    print(Fore.CYAN + "Offline debbug? (y/n)", Fore.RESET, end="")
    shared_vars.offline_debbug = to_bool(input())

    parser.work_dir = os.getcwd()
    parser.files = list_files(parser.work_dir)

    if to_bool(only_lyrics) is True:
        LYRICS(parser.work_dir, GUI=False)
    else:
        print("Enter album name: " + Fore.GREEN, end="")
        album = str(input())
        print(Fore.RESET + "Enter band name: " + Fore.GREEN, end="")
        band = str(input())
        print(Fore.RESET)
        MAIN(band, album, parser.work_dir, GUI=False)


# ####################################################################x
# GOOGLE LYRICS API
# AIzaSyAlcmHItgtDPmCLqvqwKdmnceMXuBQHnuI
