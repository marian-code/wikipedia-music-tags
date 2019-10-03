import signal
import sys
try:
    import package_setup
except:
    pass  # not needed for frozen app

from wiki_music.constants.colors import GREEN, RESET
from wiki_music.library import WikipediaRunner
from wiki_music.utilities import SharedVars, input_parser, we_are_frozen


# add signal handler to exit gracefully
# upon Ctrl+C
def signal_handler(sig, frame):
    print("\nAborting by user request...")
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

    if not parser.album:
        print(GREEN + "Enter album name: " + RESET, end="")
        parser.album = str(input())
    if not parser.band:
        print(GREEN + "Enter band name: " + RESET, end="")
        parser.band = str(input())
    print(RESET)

    if only_lyrics:
        parser.run_lyrics()
    else:
        parser.run_wiki()
