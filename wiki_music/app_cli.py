"""wiki_music CLI entry point."""

import logging
from atexit import register

from wiki_music.constants.colors import GREEN, RESET
from wiki_music.library import WikipediaRunner
from wiki_music.utilities import (input_parser, set_log_handles,
                                  set_signal_handler, exit_cleaner)


def main():
    """CLI application entry point."""
    # register Ctrl-C signal handler
    set_signal_handler()

    # register exit cleaner
    register(exit_cleaner)

    # read command line input
    args = input_parser()

    # setup loggers
    if args["debug"]:
        set_log_handles(logging.DEBUG)
    else:
        set_log_handles(logging.WARNING)

    # remove keys that won't be used to init WikipediaRunner
    args.pop("debug")
    lyrics_only = args.pop("lyrics_only")

    # get input if it was not specified on command line
    if not lyrics_only:
        if not args["album"]:
            print(GREEN + "Enter album name: " + RESET, end="")
            args["album"] = str(input())
        if not args["band"]:
            print(GREEN + "Enter band name: " + RESET, end="")
            args["band"] = str(input())
        print(RESET)

    # instantiate parser
    parser = WikipediaRunner(**args, GUI=False)

    # run search
    if lyrics_only:
        parser.run_lyrics()
    else:
        parser.run_wiki()

    input("\nPress ENTER to continue")


if __name__ == "__main__":
    main()
