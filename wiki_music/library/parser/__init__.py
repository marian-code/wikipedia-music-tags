"""Toplevel parser script that can run wikipedia search."""

import logging
from pathlib import Path
from time import sleep
from typing import Union

from wiki_music.constants.colors import CYAN, GREEN, RESET
from wiki_music.utilities import (Action, exception, flatten_set, to_bool,
                                  we_are_frozen)

from .process_page import WikipediaParser

log = logging.getLogger(__name__)


class WikipediaRunner(WikipediaParser):
    r"""Toplevel Wikipedia Parser class.

    Inherits all other parser subclasses. This is the class that is intended
    for user interaction. Its methods know how to run the parser in order to
    produce meaningfull results.

    Warnings
    --------
    This is the only parser class that is ment for user interaction. Calling
    its subclasses directly might result in unexpected behaviour.

    Parameters
    ----------
    album: str
        album name
    albumartist: str
        band name
    work_dir: str
        directory with music files
    with_log: bool
        If parser should output its progress to logger, only for CLI mode
    GUI: bool
        if True - assume app is running in GUI mode\n
        if False - assume app is running in CLI mode
    protected_vars: bool
        whether to initialize protected variables or not
    """

    def __init__(self, album: str = "", albumartist: str = "",
                 work_dir: Union[str, Path] = "", with_log: bool = False,
                 GUI: bool = True, protected_vars: bool = True,
                 offline_debug: bool = False,
                 write_yaml: bool = False) -> None:

        log.debug("init parser runner")

        super().__init__(protected_vars=protected_vars, GUI=GUI)
        self._GUI = GUI
        self.with_log = with_log
        self.ALBUM = album
        self.ALBUMARTIST = albumartist
        self.work_dir = Path(work_dir)
        self.offline_debug = offline_debug
        self.write_yaml = write_yaml

        log.debug("init parser runner done")

    @exception(log)
    def run_wiki(self):
        """Runs the whole wikipedia search, together with lyrics finding."""
        if self._GUI:
            self._run_wiki_gui()
        else:
            self._run_wiki_nogui()

    def _run_wiki_gui(self):
        """Runs wikipedia search with specifics of the GUI mode."""
        # download wikipedia page
        if not self.offline_debug:
            self._log.info(f"Searching for: {self.ALBUM} by "
                           f"{self.ALBUMARTIST}")
        else:
            self._log.info("Using offline cached page insted of web page")

        error_msg = self.get_wiki()
        if error_msg:
            self._log.exception(error_msg)
            return

        else:
            self._log.info(f"Found at: {self.url}")
            self._log.info("Cooking Soup")

            error_msg = self.cook_soup()
            if error_msg:
                self._log.exception(error_msg)
                return
            else:
                self._log.info("Soup ready")

        # find release date
        self._log.info(f"Found release date: {self.get_release_date()}")

        # find list of genres
        self.get_genres()
        self._log.info(f"Found genre(s): {', '.join(self.genres)}")

        # download cover art from wikipedia
        self._log.info("Downloading cover art")
        self.get_cover_art()

        if not we_are_frozen():
            # basic html textout for debug
            self.basic_out()

        # print out page contents
        self._log.info(f"Found page contents: "
                       f"{', '.join(self.get_contents())}")

        # extract track list
        self._log.info("Extracting tracks")
        self.get_tracks()

        # extract personel names
        self._log.info("Extracting additional personnel")
        self.get_personnel()

        # extract writers, composers
        self._log.info("Extracting composers")
        self.get_composers()

        if not we_are_frozen():
            # save to files
            self._log.info("Writing to disc")
            self.disk_write()

        # select genre
        self._log.info("Select genre")
        if not self.GENRE:
            if len(self.genres) == 1:
                msg = "Input genre"
            else:
                msg = "Select genre"
            a = Action("genres", msg, options=self.genres)
            self.GENRE = a.response

        # decide what to do with artists
        self._log.info("Assign artists to composers")

        a = Action("composers", "Do you want to copy artists to composers?",
                   load=True)
        if a.response:
            self.merge_artist_composers()

        # decide if you want to find lyrics
        self._log.info("Searching for Lyrics")
        a = Action("lyrics", "Do you want to find lyrics?")
        self.save_lyrics(a.response)

        self._log.info("Done")

    def _run_wiki_nogui(self):
        """Runs wikipedia search with specifics of the CLI mode."""
        # download wikipedia page
        if not self.offline_debug:

            self._log_print(msg_WHITE="Accessing Wikipedia...")

            print("Searching for: " + GREEN + self.ALBUM + RESET + " by " +
                  GREEN + self.ALBUMARTIST)

        else:
            self._log_print(msg_GREEN="Using offline cached page insted "
                            "of web page")

        error_msg = self.get_wiki()
        if error_msg:
            self._log_print(msg_GREEN=error_msg, level="WARN")
            return

        else:
            self._log_print(msg_GREEN="Found at: ", msg_WHITE=self.url)

            self._log_print(msg_WHITE="Cooking Soup")

            error_msg = self.cook_soup()
            if error_msg:
                self._log_print(msg_GREEN=error_msg, level="WARN")

                return
            else:
                self._log_print(msg_WHITE="Soup ready")

        # find release date
        self._log_print(msg_GREEN="Found release date:",
                        msg_WHITE=self.get_release_date())

        # find list of genres
        self.get_genres()
        self._log_print(msg_GREEN="Found genre(s)",
                        msg_WHITE="\n".join(self.genres))

        if not we_are_frozen():
            # basic html textout for debug
            self.basic_out()

        # get and print out page contents
        self._log_print(msg_GREEN="Found page contents",
                        msg_WHITE="\n".join(self.get_contents()))

        # extract track list
        self.get_tracks()

        # extract personel names
        self._log_print(msg_GREEN="Extracting additional personnel")
        self.get_personnel()

        # print out additional personnel
        self._log_print(msg_GREEN="Found aditional personel")
        if not we_are_frozen():
            print(self.personnel_2_str())

        # extract writers, composers
        self._log_print(msg_GREEN="Extracting composers")

        self._log_print(msg_GREEN="Found composers",
                        msg_WHITE="\n".join(flatten_set(self.get_composers())))

        if not we_are_frozen():
            # save to files
            self._log_print(msg_WHITE="Writing to disk")
            self.disk_write()

        # print out found tracklist
        self._log_print(msg_GREEN="Found Track list(s)")
        self.print_tracklist()

        # select genre
        if not self.GENRE:
            if not self.genres:
                print(CYAN + "Input genre:", end="")
                self.genre = input()
            else:
                print(CYAN + "Specify which genre you want to write: [1.]")
                for i, gen in enumerate(self.genres, 1):
                    print(f"{i}. {gen}")

                print("Input number:", CYAN, end="")
                index = input()
                try:
                    index = int(index) - 1
                except ValueError:
                    index = 0

                self.GENRE = self.genres[index]

        # decide what to do with artists
        print(CYAN + "Do you want to assign artists to composers? ([y]/n)",
              RESET, end=" ")
        if to_bool(input()):
            self.merge_artist_composers()

        # decide if you want to find lyrics
        print(CYAN + "\nDo you want to find and save lyrics? ([y]/n): " +
              RESET, end="")

        # download lyrics
        self.save_lyrics(to_bool(input()))

        print(CYAN + "Write data to ID3 tags? ([y]/n): " + RESET, end="")
        if to_bool(input()):
            if not self.write_tags():
                self._log_print(
                    msg_WHITE="Cannot write tags because there are no "
                    "coresponding files")
            else:
                self._log_print(msg_GREEN="Done")

    @exception(log)
    def run_lyrics(self):
        """Runs only the lyrics search."""
        if self._GUI:
            self._run_lyrics_gui()
        else:
            self._run_lyrics_nogui()

    def _run_lyrics_gui(self):
        """Runs only lyrics search with specifics of the GUI mode."""
        self._log.info("Searching for lyrics")

        self.save_lyrics(find=True)

        self._log.info("Done")

    def _run_lyrics_nogui(self):
        """Runs only lyrics search with specifics of the CLI mode."""
        self.read_files()

        # find lyrics
        self._log_print(msg_GREEN="Searching for lyrics")

        self.save_lyrics()

        if not self.write_tags():
            self._log_print(msg_WHITE="Cannot write tags because there are no "
                            "coresponding files")
        else:
            self._log_print(msg_GREEN="Done")

    def _log_print(self,
                   msg_GREEN: str = "",
                   msg_WHITE: str = "",
                   level: str = "INFO"):
        """Redirects the input to sandard print function and to logger.

        Parameters
        ----------
        msg_GREEN: str
            message that shoul be highlighted in green in print output
        msg_WHITE: str
            message that should be left with the default font color
        level: str
            logger level for output message
        """
        if msg_GREEN != "":
            print(GREEN + "\n" + msg_GREEN)
        if msg_WHITE != "":
            print(msg_WHITE)

        if self.with_log:
            msg_GREEN = msg_GREEN + msg_WHITE

            if level == "INFO":
                log.info(msg_GREEN)
            if level == "WARN":
                log.warning(msg_GREEN)
