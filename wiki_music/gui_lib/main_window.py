"""Module containing Main GUI window class called by GUI entry point."""

import logging
import os  # lazy loaded
import subprocess  # lazy loaded
import sys
import time  # lazy loaded
import webbrowser  # lazy loaded
from threading import Thread
from typing import List, Optional, Union, TYPE_CHECKING

from wiki_music import __version__
from wiki_music.constants import LOG_DIR, ROOT_DIR
from wiki_music.gui_lib import BaseGui, CoverArtSearch, DataModel, RememberDir
from wiki_music.gui_lib.qt_importer import (QAbstractItemView, QFileDialog,
                                            QInputDialog, QMessageBox,
                                            QProgressBar, QProgressDialog, Qt,
                                            QTimer)
from wiki_music.utilities import (NLTK, GoogleApiKey, Mp3tagNotFoundException,
                                  GuiLoggger, YmlSettings, exception, warning)

from wiki_music.utilities import Action, Progress, Control, ThreadPoolProgress

if TYPE_CHECKING:
    from wiki_music.gui_lib import CustomQTableView

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
        self.conditions_timer.setInterval(200)

        self.threadpool_timer = QTimer()
        self.threadpool_timer.timeout.connect(self._threadpool_check)
        self.threadpool_timer.setSingleShot(True)
        self.threadpool_timer.setTimerType(Qt.PreciseTimer)

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

    def _question(self, message: str, ignore_button: bool = False
                  ) -> Union[str, bool]:
        """Create dialog and request response from user.

        Parameters
        ----------
        message: str
            text of the message to show in dialog
        ignore_button: bool
            whether to show ignore button
        """
        if ignore_button:
            buttons = QMessageBox.Yes | QMessageBox.No | QMessageBox.Ignore
            msg_type = (QMessageBox.Information, "Information")
        else:
            buttons = QMessageBox.Yes | QMessageBox.No
            msg_type = (QMessageBox.Question, "Question")

        msg = QMessageBox(*msg_type, message, buttons)

        if ignore_button:
            # change button text
            dont_bother_button = msg.button(QMessageBox.Ignore)
            dont_bother_button.setText("Don't bother me again")

        # exec dialog
        out = msg.exec_()

        if out == QMessageBox.Yes:
            return True
        elif out == QMessageBox.No:
            return False
        elif out == QMessageBox.Ignore:
            return "d"
        else:
            raise Exception("Wrong messagebox option")

    # periodically checking methods
    @exception(log)
    def _conditions_check(self):
        """Provides GUI<->user interaction for the parser.

        Periodically checks if parser requires user input, if so displays
        dialog with appropriate description and input options.
        """

        action = Action.get_nowait()
        if action:
            self._log.debug(f"got action to carry out: {action.switch}")

            # first load values to GUI from parser
            if action.load:
                self._log.debug("loading vaues to GUI first")
                self._parser_to_gui()

            if action.switch == "genres":

                if not action.options:
                    item, ok = QInputDialog.getText(self, action.message,
                                                    "Input genre:")
                else:
                    item, ok = QInputDialog.getItem(self, action.message,
                                                    "List of genres",
                                                    action.options, 0, False)
                if ok:
                    action.response = item
                else:
                    action.response = "N/A"

            elif action.switch == "composers":
                action.response = self._question(action.message)

            elif action.switch == "lyrics":
                answer = self._question(action.message)
                action.response = answer

                if answer:
                    # show download progress
                    self.progressShow = QProgressDialog("Downloading lyrics",
                                                        "", 0,
                                                        self.number_of_tracks,
                                                        self)
                    self.progressShow.setCancelButton(None)
                    self._threadpool_check()

            elif action.switch == "load_api_key":
                dialog = QInputDialog(self)
                dialog.setInputMode(QInputDialog.TextInput)
                dialog.setLabelText("Key:")
                dialog.setWindowTitle("Paste goole API key here")
                dialog.resize(350, 70)

                if dialog.exec_():
                    action.response = dialog.textValue()
                else:
                    action.response = None

            elif action.switch in ("nltk_data", "api_key"):
                action.response = self._question(action.message,
                                                 ignore_button=True)

            elif action.switch == "download_nltk_data":
                folder = QFileDialog.getExistingDirectory(
                    self, "Set directory for nltk data", action.message)

                if folder:
                    action.response = folder
                else:
                    action.response = action.message
            elif action.switch == "load":
                # if we want to only load values to gui
                pass
            else:
                raise Exception(f"Requested unknown action: {action.switch}")

            # runs esentially in loop calling itself until all data are gone
            # from queue
            self._conditions_check()

    def _exception_check(self):
        """Provides GUI displaying of exceptions.

        Periodically checks if exception occured somewhere in the app, if so
        displays message with information and if applicable option to exit the
        app
        """
        action = Control.get_nowait()
        if action:
            if action.switch == "exception":
                msg = QMessageBox(QMessageBox.Critical, "Exception",
                                  action.message)
                path = LOG_DIR / "wiki_music_library.log"
                msg.setDetailedText(path.read_text())
                msg.exec_()

            elif action.switch == "warning":
                QMessageBox(QMessageBox.Warning, "Warning",
                            action.message).exec_()

            elif action.switch == "ask_to_exit":
                msg = QMessageBox(QMessageBox.Question, "Warning",
                                  "Do you want to stop the search?",
                                  QMessageBox.Yes | QMessageBox.No)
                msg.setInformativeText(action.message)

                # might be tricky, parser is not guaranted to read the
                # response before this GUI method pools the queue again
                # but 500 ms should be enough time
                action.response = msg.exec_()
            # TODO unntested
            elif action.switch == "deconstruct":
                sys.exit(self.exec_())
            else:
                raise Exception(f"Requested unknown control handling: "
                                f"{action.switch}")

    @exception(log)
    def _description_check(self):
        """Shows parser progress in the bottom status bar of main window.

        Runs periodically.
        """
        progress = Progress.get_nowait()
        if progress:
            for item in ("Done", "Preload"):
                if item in progress.description:
                    self.progressBar.setValue(self.progressBar.maximum())
                    break
            else:
                self.progressBar.setValue(progress.actual)

            self.progressBar.setFormat(progress.description)

    def _threadpool_check(self):

        progress = ThreadPoolProgress.get_nowait()
        if progress:
            self.progressShow.setValue(progress.actual)
            self.progressShow.setMaximum(progress.max)

            if progress.actual == progress.max:
                return

        self.threadpool_timer.start(10)


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
            if self.url and not self.offline_debug:
                webbrowser.open_new_tab(self.url)
            elif self.offline_debug:
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
        if not sys.platform.startswith("win32"):
            raise Mp3tagNotFoundException("Mp3tag is supported only on "
                                          "Windows")

        MP3_TAG = YmlSettings.read("Mp3tag_path", None)

        if not MP3_TAG:
            msg = QMessageBox(QMessageBox.Warning, "Unable to locate Mp3tag",
                              "Mp3tag is a complementary app to this one. "
                              "Do you want to set its location?",
                              QMessageBox.Yes | QMessageBox.No)
            if msg.exec_() == QMessageBox.No:
                return

        if self.work_dir:
            try:
                subprocess.Popen([MP3_TAG, f"/fp:{self.work_dir}"])
            except (FileNotFoundError, OSError, TypeError):
                # get loaction from user
                MP3_TAG = self._select_file(
                    description="Mp3tag was not found, Select Mp3tag.exe "
                                "executable path",
                    file_types="Executable files (*.exe)")

                YmlSettings.write("Mp3tag_path", MP3_TAG)
                # run again
                self._run_Mp3tag()
        else:
            QMessageBox(QMessageBox.Information, "Message",
                        "You must select directory first!").exec_()

    def _show_help(self, help_type: str):
        """Show app help information: index, git, version or logs.

        Parameters
        ----------
        help_type: str
            which help option to show
        """
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
        if self.ALBUMARTIST:
            self.start_preload()

    def _entry_album(self):
        """Connect to album entry field."""
        self.ALBUM = self.album_entry_input.text()
        if self.ALBUM:
            self.start_preload()

    def _select_yaml(self):
        """Connect to  checkbox."""
        self.write_yaml = self.write_yaml_sw.isChecked()

    def _select_offline_debbug(self):
        """Connect to offline debug checkbox.

        Note
        ----
        Restarts the preload with right settings.
        """
        self.offline_debug = self.offline_debbug_sw.isChecked()
        if self._input_is_present():
            self.start_preload()


class Window(DataModel, Checkers, Buttons, CoverArtSearch):
    """Toplevel GUI class, main winndow with all its functionality."""

    tableView: "CustomQTableView"

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
        self.wiki_search_button.clicked.connect(lambda: self._wiki_search())
        self.coverArt.clicked.connect(lambda: self.cover_art_search())
        self.lyrics_button.clicked.connect(lambda: self._lyrics_search())
        self.toolButton.clicked.connect(lambda: self._select_file())

        # connect the album and band entry field to preload function
        self.band_entry_input.editingFinished.connect(self._entry_band)
        self.album_entry_input.editingFinished.connect(self._entry_album)

        # create table-proxy mapping for sorting
        self.tableView.setModel(self.proxy)
        self.tableView.setSortingEnabled(True)

        # show table
        self.tableView.show()

        # enable dragging files and dirs into the table
        self.tableView.FileDropped.connect(self._load_dropped_dir)

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
        self.actionAll_Tags.triggered.connect(
            lambda: self._save_tags(selected=False))
        self.actionSelected_Tags.triggered.connect(
            lambda: self._save_tags(selected=True))

        # show help
        self.actionHelp.triggered.connect(lambda: self._show_help("index"))
        self.actionGit.triggered.connect(lambda: self._show_help("git"))
        self.actionLogs.triggered.connect(lambda: self._show_help("logs"))
        self.actionVersion.triggered.connect(
            lambda: self._show_help("version"))

        # settings
        self.actionNltkData.triggered.connect(
            lambda: NLTK.download_data(in_thread=True))
        self.actionGetApiKey.triggered.connect(
            lambda: GoogleApiKey.get(True, in_thread=True))

        # search actons
        self.actionWikipedia.triggered.connect(lambda: self._wiki_search())
        self.actionLyrics.triggered.connect(lambda: self.cover_art_search())
        self.actionCoverArt.triggered.connect(lambda: self._lyrics_search())

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
            self.write_yaml_sw.hide()
        else:
            # connect switches to functions
            self.offline_debbug_sw.stateChanged.connect(
                self._select_offline_debbug)
            self.write_yaml_sw.stateChanged.connect(self._select_yaml)

    def _selected_table_rows(self) -> List[int]:
        """Returns indeces of selected table rows.

        Returns
        -------
        List[int]
            indeces of selected rows
        """
        indeces = self.tableView.selectionModel().selectedRows()
        return [self.proxy.mapToSource(i).row() for i in indeces]

    # methods that bind to gui elements
    @exception(log)
    def _save_tags(self, selected: bool = False):
        """Save changes to file tags, after saving reload files from disk."""
        # first stop any running preload, as it is not needed any more
        self.stop_preload()

        # TODO non-atomic
        if not self.save_ready:
            QMessageBox(QMessageBox.Information, "Info",
                        "You must run the search first!").exec_()
        else:
            if not self.work_dir:
                QMessageBox(QMessageBox.Information, "Info",
                            "You must specify directory with files!").exec_()
                return

            indeces = self._selected_table_rows()

            # show save progress
            self.progressShow = QProgressDialog("Writing tags", "", 0,
                                                len(indeces), self)
            self.progressShow.setCancelButton(None)
            self._threadpool_check()

            if not self.write_tags(indeces):
                msg = ("Cannot write tags because there are no "
                       "coresponding files")
                QMessageBox(QMessageBox.Information, "Info", msg)
                self._log.info(msg)

            # reload files from disc after save
            self.reinit_parser()
            self.read_files()

    def _load2gui(self):
        """Load files, start preload and show in GUI."""
        self._init_progress_bar(0, 2)

        # TODO non-atomic
        # read files and start preload
        self.read_files()
        QTimer.singleShot(500, lambda: self.start_preload())

    def _load_dropped_dir(self, path: str):
        """Handle directory dropped onto the table.

        Parameters
        ----------
        path: str
            path to dropped directory
        """
        log.debug(f"Dropped dir: {path}")

        answer = self._question(f"Do you want to load files from: {path}? "
                                f"Previous changes will be discarded")

        if answer:
            self.work_dir = path
            self._load2gui()

    @exception(log)
    def _select_dir(self):
        """Select working directory, read found files and start preload."""
        with RememberDir(self) as rd:
            self.work_dir, load_ok = rd.get_dir()

        if load_ok:
            self._load2gui()

    def _init_progress_bar(self, minimum: int, maximum: int):
        """Resets main progresbar to 0 and sets range.

        Parameters
        ----------
        minimum: int
            minimal progressbar value
        maximum: int
            maximum progressbar value
        """
        GuiLoggger.progress = minimum
        self.progressBar.setRange(minimum, maximum)
        self.progressBar.setValue(minimum)

    @exception(log)
    def _wiki_search(self):
        """Start wikipedia search in background thread."""
        if not self._input_is_present(with_warn=True):
            return

        self._init_progress_bar(0, 16)

        log.info("starting wikipedia search")

        # TODO non-atomic
        self.reinit_parser()
        self._start_checkers()

        main_app = Thread(target=self._parser.run_wiki,
                          name="WikiSearch", daemon=True)
        main_app.start()

    @exception(log)
    def _lyrics_search(self):
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

        self._start_checkers()
        main_app = Thread(target=self._parser.run_lyrics,
                          name="LyricsSearch", daemon=True)
        main_app.start()
