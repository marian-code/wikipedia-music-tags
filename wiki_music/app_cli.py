"""wiki_music CLI entry point."""

import logging
import signal
import sys
from typing import TypeVar

from wiki_music.constants.colors import GREEN, RESET
from wiki_music.library import WikipediaRunner
from wiki_music.utilities import input_parser, set_log_handles


# add signal handler to exit gracefully upon Ctrl+C
def signal_handler(signalnum: int, frame: TypeVar("Frame")):
    """Handle Ctrl-C signals(KeyboardInterupt) gracefully.

    Parameters
    ----------
    signalnum: int
        signam identifier
    frame: Frame
        current stack frame
    """
    print("\nAborting by user request...")
    sys.exit()


def main():
    """CLI application entry point."""
    # register sinal handler
    signal.signal(signal.SIGINT, signal_handler)

    # read command line input
    (write_yaml, offline_debug, only_lyrics,
     album, band, work_dir, with_log, debug) = input_parser()

    # setup loggers
    if debug:
        set_log_handles(logging.DEBUG)
    else:
        set_log_handles(logging.WARNING)

    # get input if it was not specified on command line
    if not only_lyrics:
        if not album:
            print(GREEN + "Enter album name: " + RESET, end="")
            album = str(input())
        if not band:
            print(GREEN + "Enter band name: " + RESET, end="")
            band = str(input())
        print(RESET)

    # instantiate parser
    parser = WikipediaRunner(album=album, albumartist=band, work_dir=work_dir,
                             with_log=with_log, GUI=False,
                             offline_debug=offline_debug,
                             write_yaml=write_yaml)

    # run search
    if only_lyrics:
        parser.run_lyrics()
    else:
        parser.run_wiki()

    input("\nPress ENTER to continue")


if __name__ == "__main__":
    main()
