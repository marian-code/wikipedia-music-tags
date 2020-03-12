"""Module handling most of guis buttons."""

import logging
import os  # lazy loaded
import subprocess  # lazy loaded
import sys
import webbrowser  # lazy loaded
from typing import Optional

from wiki_music import __version__
from wiki_music.constants import LOG_DIR
from wiki_music.gui_lib import BaseGui
from wiki_music.gui_lib.qt_importer import QFileDialog, QMessageBox
from wiki_music.utilities import (NLTK, GoogleApiKey, GuiLoggger, IniSettings,
                                  Mp3tagNotFoundException, exception, warning)

__all__ = ["Buttons"]

log = logging.getLogger(__name__)
log.debug("finished gui buttons imports")


class Buttons(BaseGui):
    """Class for handling main window button interactions.

    Warnings
    --------
    This class is not ment to be instantiated, only inherited.
    """

    def _setup_menubar(self):

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

        # TODO menubar buttons that are not implemented
        self.actionNew.triggered.connect(self._do_nothing)
        self.actionExit.triggered.connect(self._do_nothing)
        self.actionSave.triggered.connect(self._do_nothing)

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

        MP3_TAG = IniSettings.read("Mp3tag_path", None)

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

                IniSettings.write("Mp3tag_path", MP3_TAG)
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

    def _select_json(self):
        """Connect to  checkbox."""
        self._parser.write_json = self.write_json_sw.isChecked()
        IniSettings.write("write_json", self._parser.write_json)

    def _select_multi(self):
        """Connect to  checkbox."""
        self._parser.multi_threaded = self.multi_threaded_sw.isChecked()
        IniSettings.write("multi_threaded", self._parser.multi_threaded)
        log.debug(f"multi threaded is set to: {self._parser.multi_threaded}")

    def _select_offline_debbug(self):
        """Connect to offline debug checkbox.

        Note
        ----
        Restarts the preload with right settings.
        """
        self.offline_debug = self.offline_debbug_sw.isChecked()
        IniSettings.write("offline_debug", self._parser.offline_debug)

        if self._input_is_present():
            self.start_preload()
