from lazy_import import lazy_callable

from wiki_music.constants.colors import CYAN, GREEN, RESET
from wiki_music.utilities import (SharedVars, exception, flatten_set, log_app,
                                  log_parser, to_bool, we_are_frozen)

from .process_page import WikipediaParser

sleep = lazy_callable("time.sleep")


class WikipediaRunner(WikipediaParser):

    def __init__(self, GUI: bool = True, protected_vars: bool = True) -> None:

        super().__init__(protected_vars=protected_vars)
        self.GUI = GUI
        self.with_log = False

    @exception(log_parser)
    def run_wiki(self):
        if self.GUI:
            self._run_wiki_gui()
        else:
            self._run_wiki_nogui()

    def _run_wiki_gui(self):

        def wait_select(switch: str):
            SharedVars.switch = switch
            SharedVars.wait = True
            while SharedVars.wait:
                sleep(0.1)

        # download wikipedia page
        if not SharedVars.offline_debbug:
            self.log.info(f"Searching for: {self.album} by {self.band}")
        else:
            self.log.info("Using offline cached page insted of web page")

        error_msg = self.get_wiki()
        if error_msg:
            self.log.exception(error_msg)
            return

        else:
            self.log.info(f"Found at: {self.url}")
            self.log.info("Cooking Soup")

            error_msg = self.cook_soup()
            if error_msg:
                self.log.exception(error_msg)
                return
            else:
                self.log.info("Soup ready")

        # get page contents
        self.get_contents()

        # find release date
        self.get_release_date()
        self.log.info(f"Found release date {self.release_date}")

        # find list of genres
        self.get_genres()
        self.log.info(f"Found genre(s): {', '.join(self.genres)}")

        # download cover art from wikipedia
        self.log.info("Downloading cover art")
        self.get_cover_art()

        if not we_are_frozen():
            # basic html textout for debug
            self.basic_out()

        # print out page contents
        self.log.info(f"Found page contents: {', '.join(self.contents)}")

        # extract track list
        self.log.info("Extracting tracks")
        self.get_tracks()

        # extract personel names
        self.log.info("Extracting additional personnel")
        self.get_personnel()

        # complete artists names
        self.complete()

        # look for aditional artists in brackets behind track names and
        # complete artists names again with new info
        self.log.info("Getting tracks info")
        self.info_tracks()

        # extract writers, composers
        self.log.info("Extracting composers")
        self.get_composers()

        # complete artists names
        self.complete()

        if not we_are_frozen():
            # save to files
            self.log.info("Writing to disc")
            self.disk_write()

        # merge artists and personel which have some apperences
        self.log.info("merge artists and personnel")
        self.merge_artist_personnel()

        # select genre
        self.log.info("Select genre")
        if not self.selected_genre:
            wait_select("genres")

        # decide what to do with artists
        self.log.info("Assign artists to composers")

        # first load already known values to GUI
        # wait must be set before load,
        # otherwise if statement in gui wont be entered
        SharedVars.wait = True
        SharedVars.load = True
        while SharedVars.wait:
            sleep(0.1)

        wait_select("comp")
        if SharedVars.assign_artists:
            self.merge_artist_composers()

        # decide if you want to find lyrics
        self.log.info("Searching for Lyrics")
        wait_select("lyrics")
        self.save_lyrics()

        SharedVars.done = True
        # announce that main app thread has reached the barrier
        SharedVars.barrier.wait()
        
        self.log.info("Done")

    def _run_wiki_nogui(self):

        # download wikipedia page
        if not SharedVars.offline_debbug:

            self.log_print(msg_WHITE="Accessing Wikipedia...")

            print("Searching for: " + GREEN + self.album + RESET +
                  " by " + GREEN + self.band)

        else:
            self.log_print(msg_GREEN="Using offline cached page insted "
                                     "of web page")

        error_msg = self.get_wiki()
        if error_msg:
            self.log_print(msg_GREEN=error_msg, level="WARN")
            return

        else:
            self.log_print(msg_GREEN="Found at: ", msg_WHITE=self.url)

            self.log_print(msg_WHITE="Cooking Soup")

            error_msg = self.cook_soup()
            if error_msg:
                self.log_print(msg_GREEN=error_msg, level="WARN")

                return
            else:
                self.log_print(msg_WHITE="Soup ready")

        # get page contents
        self.get_contents()

        # find release date
        self.get_release_date()
        self.log_print(msg_GREEN="Found release date",
                       msg_WHITE=self.release_date)

        # find list of genres
        self.get_genres()
        self.log_print(msg_GREEN="Found genre(s)",
                       msg_WHITE="\n".join(self.genres))

        if not we_are_frozen():
            # basic html textout for debug
            self.basic_out()

        # print out page contents
        self.log_print(msg_GREEN="Found page contents",
                msg_WHITE="\n".join(self.contents))

        # extract track list
        self.get_tracks()

        # extract personel names
        self.log_print(msg_GREEN="Extracting additional personnel")
        self.get_personnel()

        # print out additional personnel
        self.log_print(msg_GREEN="Found aditional personel")
        if not we_are_frozen():
            print(self.personnel_2_str())

        # complete artists names
        self.complete()

        # look for aditional artists in brackets behind track names and
        # complete artists names again with new info
        self.info_tracks()

        # extract writers, composers
        self.log_print(msg_GREEN="Extracting composers")
        self.get_composers()

        # complete artists names
        self.complete()

        self.log_print(msg_GREEN="Found composers",
                msg_WHITE="\n".join(flatten_set(self.composers)))

        if not we_are_frozen():
            # save to files
            self.log_print(msg_WHITE="Writing to disk")
            self.disk_write()

            # print out found tracklist
            self.log_print(msg_GREEN="Found Track list(s)")
            self.print_tracklist()

        # merge artists and personel which have some apperences
        self.merge_artist_personnel()

        # select genre
        if not self.selected_genre:
            if not self.genres:
                print(CYAN + "Input genre:", end="")
                self.genre = input()
            else:
                print(CYAN + "Specify which genre you want to write:")
                for i, gen in enumerate(self.genres, 1):
                    print(f"{i}. {gen}")

                print("Input number:", CYAN, end="")
                index = int(input()) - 1

                self.selected_genre = self.genres[index]

        # decide what to do with artists
        print(CYAN + "Do you want to assign artists to composers? (y/n)",
              RESET, end=" ")
        if to_bool(input()):
            self.merge_artist_composers()

        # decide if you want to find lyrics
        print(CYAN + "\nDo you want to find and save lyrics? (y/n): " +
              RESET, end="")
        SharedVars.write_lyrics = to_bool(input())

        # download lyrics
        self.save_lyrics()
        
        print(CYAN + "Write data to ID3 tags? (y/n): " + RESET, end="")
        if to_bool(input()):
            if not self.write_tags(lyrics_only=False):
                self.log_print(msg_WHITE="Cannot write tags because there are no "
                                    "coresponding files")
            else:
                self.log_print(msg_GREEN="Done")

    @exception(log_parser)
    def run_lyrics(self):
        if self.GUI:
            self._run_lyrics_gui()
        else:
            self._run_lyrics_nogui()

    def _run_lyrics_gui(self):

        self.log.info("Searching for lyrics")

        self.save_lyrics()

        self.log.info("Done")
        SharedVars.done = True
        self.log.info("wait barrier")

        # announce that main app thread has reached the barrier
        SharedVars.barrier.wait()

    def _run_lyrics_nogui(self):

        self.read_files()

        # find lyrics
        self.log_print(msg_GREEN="Searching for lyrics")

        self.save_lyrics()
        
        if not self.write_tags(lyrics_only=True):
            self.log_print(msg_WHITE="Cannot write tags because there are no "
                                "coresponding files")
        else:
            self.log_print(msg_GREEN="Done")

    def log_print(self, msg_GREEN: str = "", msg_WHITE: str = "",
                  level: str = "INFO"):

        if msg_GREEN != "":
            print(GREEN + "\n" + msg_GREEN)
        if msg_WHITE != "":
            print(msg_WHITE)

        if self.with_log:
            msg_GREEN = msg_GREEN + msg_WHITE

            if level == "INFO":
                log_app.info(msg_GREEN)
            if level == "WARN":
                log_app.warning(msg_GREEN)