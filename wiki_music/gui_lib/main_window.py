"""Module containing Main GUI window class called by GUI entry point."""

import logging
import time  # lazy loaded
from threading import Thread
from typing import TYPE_CHECKING, List, Union

from wiki_music.gui_lib import (Buttons, Checkers, CoverArtSearch, DataModel,
                                RememberDir, Replacer)
from wiki_music.gui_lib.custom_classes import ProgressBar
from wiki_music.gui_lib.qt_importer import QMessageBox, QTimer
from wiki_music.utilities import (
    GuiLoggger, IniSettings, Progress, exception, lrange, warning)

log = logging.getLogger(__name__)
log.debug("finished gui imports")


class Window(DataModel, Checkers, Buttons, CoverArtSearch, Replacer):
    """Toplevel GUI class, main winndow with all its functionality."""

    def __init__(self, debug):

        log.debug("init superclass")
        super().__init__()

        # whether to show debugging options in gui
        self._DEBUG = debug

        log.debug("setup overlay")
        # set overlay functions
        self._setup_wikisearch()
        self._setup_table()
        self._setup_menubar()
        self._setup_statusbar()
        self._setup_search_replace()

        log.debug("start checkers")
        # start checkers
        self._init_checkers()
        self._start_checkers()

    def _setup_wikisearch(self):
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

        if not self._DEBUG:
            self.actionOffline_debug.setVisible(False)
            self.actionWrite_tags_to_JSON.setVisible(False)
            self.actionMulti_threaded.setVisible(False)
        else:
            # connect switches to functions
            self.actionOffline_debug.changed.connect(
                self._select_offline_debbug)
            self.actionWrite_tags_to_JSON.changed.connect(self._select_json)
            self.actionMulti_threaded.changed.connect(self._select_multi)

            # set states
            self.actionOffline_debug.setChecked(
                IniSettings.read("offline_debug", False, bool))
            self.actionWrite_tags_to_JSON.setChecked(
                IniSettings.read("write_json", False, bool))
            self.actionMulti_threaded.setChecked(
                IniSettings.read("multi_threaded", True, bool))

        # TODO test progressbar
        self.test_button.clicked.connect(self.test_progress)

    # TODO test progressbar
    def test_progress(self, collect=False):

        if not collect:
            from wiki_music.utilities import ThreadPool
            from time import sleep

            def fun(time):
                print(f"sleep {time}")
                sleep(time)

            log.debug("create threadpool")
            t = ThreadPool(target=fun, args=[(i, ) for i in range(5)])
            t.run()

            log.debug("create progressbar")
            self.prog = ProgressBar("Writing tags", 0, 5, self, self.test_progress, t)
        else:
            self.prog.threadpool.results()
            t.results()

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

            if selected:
                indices = self.tableView.selected_rows()
            else:
                indices = list(lrange(self._parser))

            # show save progress
            self.progressShow = ProgressBar("Writing tags", 0, len(indices), self)

            if not self.write_tags(indices):
                msg = ("Cannot write tags because there are no "
                       "coresponding files")
                QMessageBox(QMessageBox.Information, "Info", msg)
                self._log.info(msg)

            # reload files from disc after save
            self.reinit_parser()
            self.read_files()

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

    def _load2gui(self):
        """Load files, start preload and show in GUI."""
        self._init_progress_bar(0, 2)

        self.progressShow = ProgressBar("Loading files", 0, 1, self)

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
        self.progressShow = ProgressBar("Downloading lyrics", 0,
                                        self.number_of_tracks, self)

        log.info("starting lyrics search")

        self._start_checkers()
        main_app = Thread(target=self._parser.run_lyrics,
                          name="LyricsSearch", daemon=True)
        main_app.start()
