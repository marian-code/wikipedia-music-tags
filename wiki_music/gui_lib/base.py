"""The base module for Qt frontend."""

import ctypes
import logging
from abc import abstractmethod

from wiki_music.constants import MAIN_WINDOW_UI
from wiki_music.gui_lib.qt_importer import (QAbstractItemView, QIcon,
                                            QMainWindow, QMessageBox,
                                            QStandardItemModel,
                                            QSystemTrayIcon, uic)
from wiki_music.utilities import MultiLog, abstract_warning, get_icon

log = logging.getLogger(__name__)
log.debug("base imports done")


# inherit base from QMainWindow and lyaout from Ui_MainWindow
class BaseGui(QMainWindow):
    """Base for all GUI classes, initializes UI from Qt Designer ui files.

    Then sets up needed variables. Connects buttons and input fields signals to
    methods. All GUI classes should subclass this class.

    Warnings
    --------
    This class is not ment to be instantiated, only inherited.

    Attributes
    ----------
    work_dir: str
        points to actuall selected directory with music files
    log: :class:`wiki_music.utilities.utils.MultiLog`
        class logger
    """

    def __init__(self) -> None:

        log.debug("init base")

        # call QMainWindow __init__ method
        super().__init__()

        # misc
        self.work_dir: str = ""
        self._log: MultiLog = MultiLog(log)

        # call Ui_MainWindow user interface setup method
        uic.loadUi(MAIN_WINDOW_UI, self)

        # initialize
        self._initUI()

        log.debug("init base done")

    def _initUI(self):
        """Load and set window tray icon and set application name."""
        self.setWindowTitle("Wiki Music")
        myappid = "WikiMusic"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        _icon = get_icon()
        self.setWindowIcon(QIcon(_icon))
        tray_icon = QSystemTrayIcon(QIcon(_icon))
        tray_icon.show()

    def _do_nothing(self):
        """Show warning about functionality not being implemented yet.

        Developement convenience function.
        """
        log.warning("Not implemented yet")
        QMessageBox(QMessageBox.Warning,
                    "Info", "Not implemented yet!").exec_()

    @abstractmethod
    def _display_image(self, image=None):
        """Will be reimpemented in :mod:`wiki_music.gui_lib.data_model`."""
        abstract_warning()
