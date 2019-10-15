"""wiki_music CLI entry point."""

import logging
import signal
import sys

from wiki_music.constants.colors import GREEN, RESET
from wiki_music.library import WikipediaRunner
from wiki_music.utilities import SharedVars, input_parser, set_log_handles


# add signal handler to exit gracefully upon Ctrl+C
def signal_handler(sig, frame):
    print("\nAborting by user request...")
    sys.exit()


def main():

    signal.signal(signal.SIGINT, signal_handler)

    (SharedVars.write_json, SharedVars.offline_debbug, only_lyrics,
     album, band, work_dir, with_log, debug) = input_parser()

    if debug:
        set_log_handles(logging.DEBUG)
    else:
        set_log_handles(logging.WARNING)

    if not album:
        print(GREEN + "Enter album name: " + RESET, end="")
        album = str(input())
    if not band:
        print(GREEN + "Enter band name: " + RESET, end="")
        band = str(input())
    print(RESET)

    parser = WikipediaRunner(GUI=False)

    parser.album = album
    parser.band = band
    parser.work_dir = work_dir
    parser.with_log = with_log
    parser.list_files()

    if only_lyrics:
        parser.run_lyrics()
    else:
        parser.run_wiki()


if __name__ == "__main__":
    main()
