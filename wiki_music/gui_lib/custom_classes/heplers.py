"""Helper GUI Qt dependent functions and classes."""

import logging
from typing import Tuple, Callable, TYPE_CHECKING, Optional, Any

from wiki_music.gui_lib.qt_importer import (QFileDialog, QProgressDialog, Qt,
                                            QTimer)
from wiki_music.utilities import (IniSettings, ThreadPoolProgress,
                                  get_music_path)

if TYPE_CHECKING:
    from wiki_music.gui_lib.qt_importer import QWidget
    from wiki_music.utilities import ThreadPool

__all__ = ["RememberDir", "ProgressBar"]

log = logging.getLogger(__name__)


class RememberDir:
    """Context manager for remembering last opened directory.

    Parameters
    ----------
    window_instance: object
        reference to the window in which the context was initialized to center
        the directory selection dialog

    Attributes
    ----------
    _start_dir: str
        remembered directory if it could be read from file
    """

    _start_dir: str

    def __init__(self, window_instance: object) -> None:

        # keep reference to main window for dialog centering
        self.window_instance = window_instance

    def get_dir(self) -> Tuple[str, bool]:
        """Shows a folder selection dialog with the last visited dir as root.

        After the user has selected directory it is remenbered, returned to
        user and upon context exit saved to file.

        Returns
        -------
        str
            string with directory name
        bool
            True if some directory was selected, False if dialog was canceled
        """
        self._start_dir = QFileDialog.getExistingDirectory(
            self.window_instance, "Open Folder", self._start_dir)

        return self._start_dir, bool(self._start_dir)

    def __enter__(self):
        """Load last visited directory from file.

        If the file could not be read, try to get music path on local PC
        """
        # load last opened dir
        self._start_dir = str(IniSettings.read("last_opened_dir",
                                               get_music_path().resolve()))

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """On context exit try to save opened directory to file."""
        if self._start_dir:
            IniSettings.write("last_opened_dir", self._start_dir)


class ProgressBar:
    """Class controling GUI progressbar and pooling threadpool for progress.

    Parameters
    ----------
    dialog_name: str
        name of the progressbar dialog
    minimum: int
        minimum progressbar value
    maximum: int
        maximum progressbar value
    parent: QWidget
        parent object reference for centering,
        this should be Qapplication instance
    run_me_later: Optional[Callable[..., Any]]
        callable that should be executed after treadpool is finished,
        it will be called with one keyword argument: collect=True
    thread_pool: Optional["ThreadPool"]
        reference to the underlying threadpool
    """

    def __init__(self, dialog_name: str, minimum: int, maximum: int,
                 parent: "QWidget",
                 run_me_later: Optional[Callable[..., Any]] = None,
                 thread_pool: Optional["ThreadPool"] = None) -> None:

        # setup timers
        self._setup_timer()

        # keep reference to threadpool and function to be continued
        self.threadpool = thread_pool
        self._run_me_later = run_me_later

        log.debug("create progressbar")

        # create progressbar
        self._progress_dialog = QProgressDialog(dialog_name, "", minimum,
                                                maximum, parent)
        self._progress_dialog.setMinimumDuration(0)
        self._progress_dialog.setWindowTitle(dialog_name)
        self._progress_dialog.setCancelButton(None)

        # start reading threadpool progress
        self._threadpool_check()

    def _setup_timer(self):

        self._timer = QTimer()
        self._timer.timeout.connect(self._threadpool_check)
        self._timer.setSingleShot(True)
        self._timer.setTimerType(Qt.PreciseTimer)

    def _threadpool_check(self):

        progress = ThreadPoolProgress.get_actual_nowait()

        if progress:
            self._progress_dialog.setValue(progress.actual)
            self._progress_dialog.setMaximum(progress.max)

            if progress.actual == progress.max or progress.finished:
                self._progress_dialog.cancel()
                if self._run_me_later:
                    self._run_me_later(collect=True)
                return

        self._timer.start(10)
