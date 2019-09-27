import signal
import sys

import package_setup
from wiki_music.constants.colors import GREEN, RESET
from wiki_music.library import WikipediaRunner
from wiki_music.utilities import SharedVars, input_parser, we_are_frozen

if __name__ == "__main__":
    from utilities.utils import clean_logs
    clean_logs()


# add signal handler to exit gracefully
# upon Ctrl+C
def signal_handler(sig, frame):
    print('Captured Ctrl+C, exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":

    parser = WikipediaRunner(GUI=False)

    (SharedVars.write_json, SharedVars.offline_debbug, only_lyrics,
     album, band, work_dir, with_log) = input_parser()

    parser.album = album
    parser.band = band
    parser.work_dir = work_dir
    parser.with_log = with_log
    parser.list_files()

    if parser.album is None:
        print(GREEN + "Enter album name: " + RESET, end="")
        parser.album = str(input())
    if parser.band is None:
        print(GREEN + "Enter band name: " + RESET, end="")
        parser.band = str(input())
    print(RESET)

    if only_lyrics:
        parser.run_lyrics()
        if not we_are_frozen():
            input("\nPRESS ENTER TO CONTINUE...")
    else:
        parser.run_wiki()
        if not we_are_frozen():
            input("\nPRESS ENTER TO CONTINUE...")
