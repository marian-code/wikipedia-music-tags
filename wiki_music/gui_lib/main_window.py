"""Module containing Main GUI window class called by GUI entry point."""

import os
import subprocess  # lazy loaded
import sys
import time  # lazy loaded
import webbrowser  # lazy loaded
from threading import Thread
from typing import Optional

from wiki_music.constants.paths import MP3_TAG
from wiki_music.gui_lib import BaseGui, CoverArtSearch, DataModel, RememberDir
from wiki_music.gui_lib.qt_importer import (QAbstractItemView, QFileDialog,
                                            QInputDialog, QMessageBox, QTimer)
from wiki_music.utilities import (SharedVars, exception, log_gui, log_parser,
                                  synchronized, we_are_frozen)

log_gui.debug("finished gui imports")


class Checkers(BaseGui):
    """ Class that houses methods that periodically check for parser changes.

    Warnings
    --------
    This class is not ment to be instantiated, only inherited.
    """

    def __init__(self) -> None:

        super().__init__()

        self._remember: Optional[str] = None

    def _init_checkers(self):
        """Initializes timers for periodically repeating methods.

        See also
        --------
        :meth:`Checkers._conditions_check`
            checks if parser requires user input
        :meth:`Checkers._exception_check`
            checks foe exceptions in application and displays a messagebox
            with errors
        :meth:`Checkers._conditions_check`
            checks for parser progres descritions
        :meth:`Checkers._start_checkers`
            starts the initialized timers
        """
        self.description_timer = QTimer()
        self.description_timer.timeout.connect(self._description_check)
        self.description_timer.setInterval(400)

        self.exception_timer = QTimer()
        self.exception_timer.timeout.connect(self._exception_check)
        self.exception_timer.setInterval(500)

        self.conditions_timer = QTimer()
        self.conditions_timer.timeout.connect(self._conditions_check)
        self.conditions_timer.setSingleShot(True)

    def _start_checkers(self):
        """Initializes timers of periodically repeating methods.
        
        See also
        --------
        :meth:`Checkers._init_checkers`
            initializes timers
        """

        self.description_timer.start(200)
        self.exception_timer.start(500)
        self.conditions_timer.start(400)

    # periodically checking methods
    @exception(log_gui)
    def _conditions_check(self):
        """Provides GUI<->user interaction for the parser.

        Periodically checks if parser requires user input, if so displays
        dialog with appropriate description and input options.
        """

        def msg_to_bool(out: QMessageBox.StandardButton) -> bool:
            if out == QMessageBox.Yes:
                return True
            else:
                return False

        if SharedVars.wait:

            if SharedVars.switch == "genres":

                log_gui.debug("initialize question window")
                # TODO non-atomic
                if not self.genres:
                    text, ok = QInputDialog.getText(self,
                                                    "Text Input Dialog",
                                                    "Input genre:")
                    if ok:
                        self.GENRE = text
                    else:
                        self.GENRE = "N/A"
                else:
                    item, ok = QInputDialog.getItem(self,
                                                    "Select input dialog",
                                                    "List of genres",
                                                    self.genres, 0,
                                                    False)
                    if ok:
                        self.GENRE = item
                    else:
                        self.GENRE = "N/A"

            if SharedVars.load:
                QTimer.singleShot(0, self._parser_to_gui)

            if SharedVars.switch == "comp":
                log_gui.debug("ask to copy composers")
                msg = QMessageBox(QMessageBox.Question, "Question",
                                  "Do you want to copy artists to composers?",
                                  QMessageBox.Yes | QMessageBox.No)

                SharedVars.assign_artists = msg_to_bool(msg.exec_())

            if SharedVars.switch == "lyrics":
                log_gui.debug("ask to find lyrics")
                msg = QMessageBox(QMessageBox.Question, "Question",
                                  "Do you want to find lyrics?",
                                  QMessageBox.Yes | QMessageBox.No)

                SharedVars.write_lyrics = msg_to_bool(msg.exec_())

            SharedVars.load = False
            SharedVars.switch = ""
            SharedVars.wait = False

        if not SharedVars.done:
            self.conditions_timer.start(200)
        else:
            # announce that gui has reached the barrier
            log_gui.debug("gui reached barrier")
            # TODO barrier is a wrong thing to have in GUI
            SharedVars.barrier.wait()

            log_gui.debug("start _parser_to_gui function")
            QTimer.singleShot(0, self._parser_to_gui)

    def _exception_check(self):
        """Provides GUI displaying of exceptions.

        Periodically checks if exception occured somewhere in the app, if so
        displays message with information and if applicable option to exit the
        app
        """

        if SharedVars.has_exception:
            msg = QMessageBox(QMessageBox.Critical, "Exception",
                              SharedVars.has_exception)
            msg.setDetailedText(open(log_parser.handlers[0].baseFilename,
                                     "r").read())
            msg.exec_()
            SharedVars.has_exception = ""

        if SharedVars.has_warning:
            QMessageBox(QMessageBox.Warning, "Warning",
                        SharedVars.has_warning).exec_()
            SharedVars.has_warning = ""

        if SharedVars.ask_exit:
            msg = QMessageBox(QMessageBox.Question, "Warning",
                              "Do you want to stop the search?",
                              QMessageBox.Yes | QMessageBox.No)
            msg.setInformativeText(SharedVars.ask_exit)
            terminate = msg.exec_()

            if terminate == QMessageBox.Yes:
                SharedVars.wait_exit = False
                SharedVars.terminate_app = True

                time.sleep(0.03)
                # TODO not working
                sys.exit(self.exec_())  # TODO untested
            else:
                SharedVars.wait_exit = False
                SharedVars.ask_exit = ""

    # TODO this method should also update progessbar in status bar
    # lock must be here because there are non atomic operations i.e. +=
    @exception(log_gui)
    @synchronized(SharedVars.lock)
    def _description_check(self):
        """Shows parser progress in the bottom status bar of main window.

        Runs periodically.
        """

        if " . . ." in SharedVars.describe:
            SharedVars.describe = SharedVars.describe.replace(" . . .", "")

        self._remember = SharedVars.describe

        if SharedVars.describe.strip():
            if (self._remember == SharedVars.describe and
                "Done" not in SharedVars.describe):  # noqa E129
                SharedVars.describe += " ."
            self.statusbar.showMessage(SharedVars.describe)
        else:
            self.statusbar.showMessage("")


class Buttons(BaseGui):
    """Class for handling main window button interactions.
    
    Warnings
    --------
    This class is not ment to be instantiated, only inherited.
    """

    @exception(log_gui)
    def __open_dir__(self):
        """Opens the current search folder."""

        if self.work_dir:
            self.log.info("Opening folder...")
            os.startfile(self.work_dir)
        else:
            QMessageBox(QMessageBox.Information, "Message",
                        "You must select directory first!").exec_()

    def __select_file__(self):
        """Handle file selection in the detail tab on the right."""
        _file = QFileDialog.getOpenFileName(self,
                                            "Select song file",
                                            self.work_dir,
                                            "Audio files (*.mp3 *.flac *.m4a)"
                                            ";;All files (*)")

        self.file_detail.setText(_file[0])

    @exception(log_gui)
    def __open_browser__(self, ulr: Optional[str] = None):
        """Opens the found wikipedia page in default web browser.
        
        Parameters
        ----------
        url: Optional[str]
            force opening of input url instead of parser url
        """

        if self.url and not SharedVars.offline_debbug:
            webbrowser.open_new_tab(self.url)
        elif SharedVars.offline_debbug:
            self.log.warning("You are in offline debugging mode")
        else:
            QMessageBox(QMessageBox.Information, "Message",
                        "You must run the search first!").exec_()

    @exception(log_gui)
    def __run_Mp3tag__(self):
        """Open Mp3tag in current working directory."""

        if self.work_dir:
            subprocess.Popen([MP3_TAG, f"/fp:{self.work_dir}"])
        else:
            QMessageBox(QMessageBox.Information, "Message",
                        "You must select directory first!").exec_()

    def __entry_band__(self):
        """Connect to albumartist entry field."""
        self.ALBUMARTIST = self.band_entry_input.text()
        self.start_preload()

    def __entry_album__(self):
        """Connect to album entry field."""
        self.ALBUM = self.album_entry_input.text()
        self.start_preload()

    def __select_json__(self):
        """Connect to json checkbox."""
        SharedVars.write_json = self.json_write_sw.isChecked()

    def __select_offline_debbug__(self):
        """Connect to offline debug checkbox.
        
        Note
        ----
        If the checkbox is unselected preload is stopped.
        """
        SharedVars.offline_debbug = self.offline_debbug_sw.isChecked()
        if SharedVars.offline_debbug:
            self.stop_preload()


class Window(DataModel, Checkers, Buttons, CoverArtSearch):

    def __init__(self):

        log_gui.debug("init superclass")
        super().__init__()

        log_gui.debug("setup overlay")
        # set overlay functions
        self.__setup_overlay__()

        log_gui.debug("start checkers")
        # start checkers
        self._init_checkers()
        self._start_checkers()

    # setup methods
    def __setup_overlay__(self):
        """Sets up GUI input elements siganl connections."""

        # map buttons to functions
        # must use lambda otherwise wrapper doesnt work correctly
        self.browse_button.clicked.connect(lambda: self.__select_dir__())
        self.wiki_search_button.clicked.connect(lambda: self.__run_search__())
        self.coverArt.clicked.connect(lambda: self.cover_art_search())
        self.lyrics_button.clicked.connect(
            lambda: self.__run_lyrics_search__())
        self.toolButton.clicked.connect(lambda: self.__select_file__())

        # connect the album and band entry field to preload function
        self.band_entry_input.editingFinished.connect(self.__entry_band__)
        self.album_entry_input.editingFinished.connect(self.__entry_album__)

        # create table-proxy mapping for sorting
        self.tableView.setModel(self.proxy)
        self.tableView.setSortingEnabled(True)

        # show table
        self.tableView.show()

        # enable drag and drop ordering of columns in table
        self.tableView.horizontalHeader().setSectionsMovable(True)
        self.tableView.horizontalHeader().setDragEnabled(True)
        self.tableView.horizontalHeader().setDragDropMode(
            QAbstractItemView.InternalMove)

        # connect to signal that is emited when table cell is clicked
        self.tableView.clicked.connect(self._detail)

        # connect menubar actions to functions
        # must use lambda otherwise wrapper doesnt work correctly
        self.actionDirectory.triggered.connect(lambda: self.__open_dir__())
        self.actionWikipedia.triggered.connect(lambda: self.__open_browser__())
        self.actionMp3_Tag.triggered.connect(lambda: self.__run_Mp3tag__())
        self.actionAll_Tags.triggered.connect(lambda: self.__save_all__())
        # TODO get rid of save only lyrics button, we now save inteligently
        # TODO only changed tags
        self.actionOnly_Lyrics.triggered.connect(lambda: self.__save_all__())

        # menubar buttons taht are not implemented
        self.actionNew.triggered.connect(self._do_nothing)
        self.actionOpen.triggered.connect(self._do_nothing)
        self.actionExit.triggered.connect(self._do_nothing)
        self.actionSave.triggered.connect(self._do_nothing)

        self.actionHelp_Index.triggered.connect(self._do_nothing)
        self.actionAbout.triggered.connect(self._do_nothing)
        self.actionGit.triggered.connect(self._do_nothing)

        if we_are_frozen():
            # show switches only if not frozen
            self.offline_debbug_sw.hide()
            self.json_write_sw.hide()
        else:
            # connect switches to functions
            self.offline_debbug_sw.stateChanged.connect(
                self.__select_offline_debbug__)
            self.json_write_sw.stateChanged.connect(self.__select_json__)

    # methods that bind to gui elements
    @exception(log_gui)
    def __save_all__(self):
        """Save changes to file tags, after saving reload files from disk."""

        # first stop any running preload, as it is not needed any more
        self.stop_preload()

        # TODO non-atomic
        if not self.save_ready:
            QMessageBox(QMessageBox.Information, "Info",
                        "You must run the search first!").exec_()
        else:
            if self.work_dir == "":
                QMessageBox(QMessageBox.Information, "Info",
                            "You must specify directory with files!").exec_()
                return

            if not self.write_tags():
                msg = ("Cannot write tags because there are no "
                       "coresponding files")
                QMessageBox(QMessageBox.Information, "Info", msg)
                self.log.info(msg)

            # reload files from disc after save
            self.reinit_parser()
            self.read_files()
            self._parser_to_gui()

    @exception(log_gui)
    def __select_dir__(self):
        """Select working directory, read found files and start preload."""

        with RememberDir(self) as rd:
            self.work_dir = rd.get_dir()

        # TODO non-atomic
        # read files and start preload
        self.read_files()
        self.start_preload()

        self._parser_to_gui()

    def __check_input_is_present__(self) -> bool:
        """Check if apropriate input to conduct search is present.

        Returns
        -------
        bool
            true if all requested inputs are present
        """

        group = [self.ALBUMARTIST, self.ALBUM, self.work_dir]
        if all(group):
            return True
        else:
            alb, bnd, wkd, inp, com, _and = [""] * 6
            if not self.ALBUM:
                alb = " album"
            if not self.ALBUMARTIST:
                bnd = " band"
            if not self.work_dir:
                wkd = " select working directory"

            if any([alb, bnd]):
                inp = "input"
            if all([alb, bnd, wkd]):
                com = ","
            elif all([alb, bnd]):
                com = " and"
            if all([alb, wkd]) or all([wkd, bnd]):
                _and = " and"

            msg = f"You must {inp}{alb}{com}{bnd}{_and}{wkd}"

            message = QMessageBox()
            message.setIcon(QMessageBox.Information)
            message.setWindowTitle("Message")
            message.setText(msg)

            return False

    @exception(log_gui)
    def __run_search__(self):
        """Start wikipedia search in background thread."""

        if not self.__check_input_is_present__():
            return

        log_gui.info("starting wikipedia search")

        # TODO non-atomic
        self.reinit_parser()
        self._start_checkers()

        main_app = Thread(target=self._parser.run_wiki, name="WikiSearch")
        main_app.daemon = True
        main_app.start()

    @exception(log_gui)
    def __run_lyrics_search__(self):
        """Start only lyric search in background thread."""

        self.stop_preload()

        if not self.__check_input_is_present__():
            return

        log_gui.info("starting lyrics search")

        self._start_checkers()
        main_app = Thread(target=self._parser.run_lyrics, name="LyricsSearch")
        main_app.start()
