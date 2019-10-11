""" The base module for Qt frontend. """

import ctypes
from abc import abstractmethod

from wiki_music.constants import MAIN_WINDOW_UI
from wiki_music.gui_lib.qt_importer import (QAbstractItemView, QIcon,
                                            QMainWindow, QMessageBox,
                                            QStandardItemModel,
                                            QSystemTrayIcon, uic)
from wiki_music.utilities import MultiLog, abstract_warning, get_icon, log_gui

log_gui.debug("base imports done")


# inherit base from QMainWindow and lyaout from Ui_MainWindow
class BaseGui(QMainWindow):
    """ Base class for all GUI classes, initializes UI from Qt Designer
    generated files. then sets up needed variables. Connects buttons and input
    fields signals to methods. All GUI classes should subclass this class.

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

        log_gui.debug("init base")

        # call QMainWindow __init__ method
        super().__init__()
        # call Ui_MainWindow user interface setup method
        uic.loadUi(MAIN_WINDOW_UI, self)

        # initialize
        self.__initUI__()

        # misc
        self.work_dir: str = ""
        self.log: MultiLog = MultiLog(log_gui)

        log_gui.debug("init base done")

    def __initUI__(self):
        """ Has three responsibilities: load and set window and tray icon and
        Set application name.
        """

        self.setWindowTitle("Wiki Music")
        myappid = "WikiMusic"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        _icon = get_icon()
        self.setWindowIcon(QIcon(_icon))
        tray_icon = QSystemTrayIcon(QIcon(_icon))
        tray_icon.show()

    def _do_nothing(self):
        """ Developement convenience function, shows messagebox with a warning
        about functionality not being implemented yet.
        """

        log_gui.warning("Not implemented yet")
        QMessageBox(QMessageBox.Warning,
                    "Info", "Not implemented yet!").exec_()

    @abstractmethod
    def _display_image(self, image=None):
        """ Will be reimpemented in :mod:`wiki_music.gui_lib.data_model` module
        """
        abstract_warning()
