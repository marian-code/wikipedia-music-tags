"""Helper GUI Qt dependent functions and classes."""

import logging

from typing import Tuple

from wiki_music.utilities import IniSettings, get_music_path
from wiki_music.gui_lib.qt_importer import QFileDialog

__all__ = ["RememberDir"]

logging.getLogger(__name__)


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
