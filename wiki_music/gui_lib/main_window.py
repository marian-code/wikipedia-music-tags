"""Module containing Main GUI window class called by GUI entry point."""

import logging
import os
import subprocess  # lazy loaded
import sys
import time  # lazy loaded
import webbrowser  # lazy loaded
from threading import Thread
from typing import Optional, Union

from wiki_music import __version__
from wiki_music.constants import API_KEY_MESSAGE, LOG_DIR, MP3_TAG, ROOT_DIR
from wiki_music.gui_lib import BaseGui, CoverArtSearch, DataModel, RememberDir
from wiki_music.gui_lib.qt_importer import (QAbstractItemView, QFileDialog,
                                            QInputDialog, QMessageBox,
                                            QProgressBar, QProgressDialog, Qt,
                                            QTimer)
from wiki_music.utilities import (Mp3tagNotFoundException, SharedVars,
                                  exception, synchronized, warning,
                                  we_are_frozen)

log = logging.getLogger(__name__)
log.debug("finished gui imports")


class Checkers(BaseGui):
    """Class that houses methods that periodically check for parser changes.

    Warnings
    --------
    This class is not ment to be instantiated, only inherited.
    """

    def __init__(self) -> None:

        super().__init__()

        self.progressShow: Optional[QProgressDialog] = None

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
        :meth:`Checkers._threadpool_check`
            checks for progress of function running in threadpool
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

        self.threadpool_timer = QTimer()
        self.threadpool_timer.timeout.connect(self._threadpool_check)
        self.threadpool_timer.setSingleShot(True)

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
    @exception(log)
    def _conditions_check(self):
        """Provides GUI<->user interaction for the parser.

        Periodically checks if parser requires user input, if so displays
        dialog with appropriate description and input options.
        """
        def msg_process(out: QMessageBox.StandardButton) -> Union[str, bool]:
            if out == QMessageBox.Yes:
                return True
            elif out == QMessageBox.No:
                return False
            else:
                return "d"

        if SharedVars.wait:

            if SharedVars.switch == "genres":

                log.debug("initialize question window")
                # TODO non-atomic
                if not self.genres:
                    text, ok = QInputDialog.getText(self, "Input genre",
                                                    "Input genre:")
                    if ok:
                        self.GENRE = text
                    else:
                        self.GENRE = "N/A"
                else:
                    item, ok = QInputDialog.getItem(self, "Select genre",
                                                    "List of genres",
                                                    self.genres, 0, False)
                    if ok:
                        self.GENRE = item
                    else:
                        self.GENRE = "N/A"

            if SharedVars.load:
                QTimer.singleShot(0, self._parser_to_gui)

            if SharedVars.switch == "comp":
                log.debug("ask to copy composers")
                msg = QMessageBox(QMessageBox.Question, "Question",
                                  "Do you want to copy artists to composers?",
                                  QMessageBox.Yes | QMessageBox.No)

                SharedVars.assign_artists = msg_process(msg.exec_())

            if SharedVars.switch == "lyrics":
                log.debug("ask to find lyrics")
                msg = QMessageBox(QMessageBox.Question, "Question",
                                  "Do you want to find lyrics?",
                                  QMessageBox.Yes | QMessageBox.No)

                SharedVars.write_lyrics = msg_process(msg.exec_())

                if SharedVars.write_lyrics:
                    # show download progress
                    self.progressShow = QProgressDialog("Downloading lyrics",
                                                        "", 0,
                                                        self.number_of_tracks,
                                                        self)
                    self.progressShow.setCancelButton(None)
                    self._threadpool_check()

            if SharedVars.switch == "api_key":
                log.debug("ask to get google api key")
                msg = QMessageBox(QMessageBox.Information, "Warning",
                                  API_KEY_MESSAGE.replace("\n", ""),
                                  QMessageBox.Yes | QMessageBox.No |
                                  QMessageBox.Ignore)
                # change button text
                dont_bother_button = msg.button(QMessageBox.Ignore)
                dont_bother_button.setText("Don't bother me again")

                SharedVars.get_api_key = msg_process(msg.exec_())

            if SharedVars.switch == "load_api_key":
                log.debug("ask to input google api key")
                dialog = QInputDialog(self)
                dialog.setInputMode(QInputDialog.TextInput)
                dialog.setLabelText("Key:")
                dialog.setWindowTitle("Paste goole API key")
                dialog.resize(350, 70)

                if dialog.exec_():
                    SharedVars.get_api_key = dialog.textValue()
                else:
                    SharedVars.get_api_key = None

            SharedVars.load = False
            SharedVars.switch = ""
            SharedVars.wait = False

        if not SharedVars.done:
            self.conditions_timer.start(200)
        else:
            # announce that gui has reached the barrier
            log.debug("gui reached barrier")
            # TODO barrier is a wrong thing to have in GUI
            SharedVars.barrier.wait()

            log.debug("start _parser_to_gui function")
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
            # TODO set right logging file
            path = os.path.join(LOG_DIR, "wiki_music_library.log")
            msg.setDetailedText(open(path, "r").read())
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
    @exception(log)
    @synchronized(SharedVars.lock)
    def _description_check(self):
        """Shows parser progress in the bottom status bar of main window.

        Runs periodically.
        """
        for item in ("Done", "Preload"):
            if item in SharedVars.describe:
                self.progressBar.setValue(self.progressBar.maximum())
                break
        else:
            self.progressBar.setValue(SharedVars.progress)

        self.progressBar.setFormat(SharedVars.describe)

    def _threadpool_check(self):

        self.progressShow.setValue(SharedVars.threadpool_prog)

        if self.progressShow.maximum() != SharedVars.threadpool_prog:
            self.threadpool_timer.start(50)


class Buttons(BaseGui):
    """Class for handling main window button interactions.

    Warnings
    --------
    This class is not ment to be instantiated, only inherited.
    """

    @exception(log)
    def _open_dir(self, folder: str = ""):
        """Opens the current search folder, or the one from input.
        
        Parameters
        ----------
        folder: str
            force opening this folder instead of working directory
        """
        if folder:
            self._log.info("Opening folder...")
            os.startfile(folder)
        elif self.work_dir:
            self._log.info("Opening folder...")
            os.startfile(self.work_dir)
        else:
            QMessageBox(QMessageBox.Information, "Message",
                        "You must select directory first!").exec_()

    def _select_file(self, description: str = "Select song file",
                     file_types: str = "Audio files (*.mp3 *.flac *.m4a)"
                     ) -> str:
        """Handle file selection.

        Parameters
        ----------
        description: str
            window title
        file_types: str
            string with allowed types

        Returns
        -------
        str
            path to selected file
        """
        _file = QFileDialog.getOpenFileName(self, description, self.work_dir,
                                            f"{file_types};;All files (*)")

        self.file_detail.setText(_file[0])
        return _file[0]

    @exception(log)
    def _open_browser(self, url: Optional[str] = None):
        """Opens the found wikipedia page in default web browser.

        Parameters
        ----------
        url: Optional[str]
            force opening of input url instead of parser wikipedia url
        """
        if url:
            webbrowser.open_new_tab(url)
        else:
            if self.url and not SharedVars.offline_debbug:
                webbrowser.open_new_tab(self.url)
            elif SharedVars.offline_debbug:
                self._log.warning("You are in offline debugging mode")
            else:
                QMessageBox(QMessageBox.Information, "Message",
                            "You must run the search first!").exec_()

    @exception(log)
    @warning(log)
    def _run_Mp3tag(self):
        """Open Mp3tag in current working directory.

        Warnings
        --------
        This action works only in Windods if Mp3tag is not installed in the
        right directory a dialog to set the path is displayed.
        """
        global MP3_TAG
        path_file = os.path.join(ROOT_DIR, "files", "MP3_TAG_PATH.txt")

        if os.path.isfile(path_file):
            with open(path_file, "r") as f:
                MP3_TAG = f.read().strip()

        if not MP3_TAG:
            msg = QMessageBox(QMessageBox.Warning, "Unable to locate Mp3tag",
                              "Mp3tag is a complementary app to this one. "
                              "Do you want to set its location?",
                              QMessageBox.Yes | QMessageBox.No)
            if msg.exec_() == QMessageBox.No:
                return

        if sys.platform == "win32":
            if self.work_dir:
                try:
                    subprocess.Popen([MP3_TAG, f"/fp:{self.work_dir}"])
                except (FileNotFoundError, OSError):
                    # get loaction from user
                    MP3_TAG = self._select_file(
                        description="Mp3tag was not found, Select Mp3tag.exe "
                                    "executable path",
                        file_types="Executable files (*.exe)")

                    # write to file for later uses
                    with open(path_file, "w") as f:
                        f.write(MP3_TAG)
                    # run again
                    self._run_Mp3tag()
            else:
                QMessageBox(QMessageBox.Information, "Message",
                            "You must select directory first!").exec_()
        else:
            raise Mp3tagNotFoundException("Mp3tag is supported only on "
                                          "Windows")

    def _show_help(self, help_type):

        if help_type == "index":
            self._open_browser("https://wikipedia-music-tags.readthedocs.io"
                               "/en/latest/index.html")
        elif help_type == "git":
            self._open_browser("https://github.com/marian-code/"
                               "wikipedia-music-tags")
        elif help_type == "version":
            QMessageBox(QMessageBox.Information, "Message",
                        f"You are using version: {__version__}").exec_()
        elif help_type == "logs":
            self._open_dir(LOG_DIR)


    def _entry_band(self):
        """Connect to albumartist entry field."""
        self.ALBUMARTIST = self.band_entry_input.text()

    def _entry_album(self):
        """Connect to album entry field."""
        self.ALBUM = self.album_entry_input.text()

    def _select_json(self):
        """Connect to json checkbox."""
        SharedVars.write_json = self.json_write_sw.isChecked()

    def _select_offline_debbug(self):
        """Connect to offline debug checkbox.

        Note
        ----
        Restarts the preload with right settings.
        """
        SharedVars.offline_debbug = self.offline_debbug_sw.isChecked()
        if SharedVars.offline_debbug and self._input_is_present():
            self.start_preload()


class Window(DataModel, Checkers, Buttons, CoverArtSearch):
    """Toplevel GUI class, main winndow with all its functionality."""

    def __init__(self, debug):

        log.debug("init superclass")
        super().__init__()

        # whether to show debuggingoptions in gui
        self._DEBUG = debug

        log.debug("setup overlay")
        # set overlay functions
        self._setup_overlay()

        log.debug("start checkers")
        # start checkers
        self._init_checkers()
        self._start_checkers()

    # setup methods
    def _setup_overlay(self):
        """Sets up GUI input elements siganl connections."""
        # map buttons to functions
        # must use lambda otherwise wrapper doesnt work correctly
        self.browse_button.clicked.connect(lambda: self._select_dir())
        self.wiki_search_button.clicked.connect(lambda: self._run_search())
        self.coverArt.clicked.connect(lambda: self.cover_art_search())
        self.lyrics_button.clicked.connect(lambda: self._run_lyrics_search())
        self.toolButton.clicked.connect(lambda: self._select_file())

        # connect the album and band entry field to preload function
        self.band_entry_input.editingFinished.connect(self._entry_band)
        self.album_entry_input.editingFinished.connect(self._entry_album)

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
        self.actionDirectory.triggered.connect(lambda: self._open_dir())
        self.actionWikipedia.triggered.connect(lambda: self._open_browser())
        self.actionMp3_Tag.triggered.connect(lambda: self._run_Mp3tag())

        # save action
        self.actionAll_Tags.triggered.connect(lambda: self._save_all())

        # show help
        self.actionHelp.triggered.connect(lambda: self._show_help("index"))
        self.actionGit.triggered.connect(lambda: self._show_help("git"))
        self.actionLogs.triggered.connect(lambda: self._show_help("logs"))
        self.actionVersion.triggered.connect(
            lambda: self._show_help("version"))

        # search actons
        self.actionWikipedia.triggered.connect(lambda: self._run_search())
        self.actionLyrics.triggered.connect(lambda: self.cover_art_search())
        self.actionCoverArt.triggered.connect(
            lambda: self._run_lyrics_search())

        # main actions
        self.actionOpen.triggered.connect(lambda: self._select_dir())

        # TODO menubar buttons taht are not implemented
        self.actionNew.triggered.connect(self._do_nothing)
        self.actionExit.triggered.connect(self._do_nothing)
        self.actionSave.triggered.connect(self._do_nothing)

        # add starusbar to progress bar
        self.progressBar = QProgressBar()
        self.progressBar.setTextVisible(True)
        self.progressBar.setAlignment(Qt.AlignCenter)
        self.progressBar.setFormat("")

        self.statusbar.addPermanentWidget(self.progressBar)

        if not self._DEBUG:
            self.offline_debbug_sw.hide()
            self.json_write_sw.hide()
        else:
            # connect switches to functions
            self.offline_debbug_sw.stateChanged.connect(
                self._select_offline_debbug)
            self.json_write_sw.stateChanged.connect(self._select_json)

    # methods that bind to gui elements
    @exception(log)
    def _save_all(self):
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

            # show save progress
            self.progressShow = QProgressDialog("Writing tags", "", 0,
                                                self.number_of_tracks, self)
            self.progressShow.setCancelButton(None)
            self._threadpool_check()

            if not self.write_tags():
                msg = ("Cannot write tags because there are no "
                       "coresponding files")
                QMessageBox(QMessageBox.Information, "Info", msg)
                self._log.info(msg)

            # reload files from disc after save
            self.reinit_parser()
            self.read_files()
            self._parser_to_gui()

    @exception(log)
    def _select_dir(self):
        """Select working directory, read found files and start preload."""
        with RememberDir(self) as rd:
            self.work_dir, load_ok = rd.get_dir()

        # if dialog was canceled, return imediatelly
        if not load_ok:
            return

        self._init_progress_bar(0, 2)

        # TODO non-atomic
        # read files and start preload
        self.read_files()
        self.start_preload()

        self._parser_to_gui()

    def _init_progress_bar(self, minimum: int, maximum: int):
        """Resets main progresbar to 0 and sets range.

        Parameters
        ----------
        minimum: int
            minimal progressbar value
        maximum: int
            maximum progressbar value
        """
        SharedVars.progress = minimum
        self.progressBar.setRange(minimum, maximum)
        self.progressBar.setValue(minimum)

    @exception(log)
    def _run_search(self):
        """Start wikipedia search in background thread."""
        if not self._input_is_present(with_warn=True):
            return

        self._init_progress_bar(0, 16)

        log.info("starting wikipedia search")

        # TODO non-atomic
        self.reinit_parser()
        self._start_checkers()

        main_app = Thread(target=self._parser.run_wiki, name="WikiSearch")
        main_app.daemon = True
        main_app.start()

    @exception(log)
    def _run_lyrics_search(self):
        """Start only lyric search in background thread."""
        self.stop_preload()

        if not self._input_is_present(with_warn=True):
            return

        self._init_progress_bar(0, 2)

        # show download progress
        self.progressShow = QProgressDialog("Downloading lyrics", "", 0,
                                            self.number_of_tracks, self)
        self.progressShow.setCancelButton(None)
        self._threadpool_check()

        log.info("starting lyrics search")

        SharedVars.write_lyrics = True

        self._start_checkers()
        main_app = Thread(target=self._parser.run_lyrics, name="LyricsSearch")
        main_app.daemon = True
        main_app.start()
