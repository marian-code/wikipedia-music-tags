"""Periodically checking methods that process parser interaction."""

import logging
import sys
from typing import Optional

from wiki_music.constants import LOG_DIR
from wiki_music.gui_lib import BaseGui
from wiki_music.gui_lib.qt_importer import (QFileDialog, QInputDialog,
                                            QMessageBox, QProgressBar,
                                            QProgressDialog, Qt, QTimer)
from wiki_music.utilities import (Action, Control, Progress,
                                  ThreadPoolProgress, exception, warning)

__all__ = ["Checkers"]

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

    def _setup_statusbar(self):

        # add starusbar to progress bar
        self.progressBar = QProgressBar()
        self.progressBar.setTextVisible(True)
        self.progressBar.setAlignment(Qt.AlignCenter)
        self.progressBar.setFormat("")

        self.statusbar.addPermanentWidget(self.progressBar)

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
