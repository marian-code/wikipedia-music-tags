import ctypes
from abc import abstractmethod

from wiki_music.gui_lib.qt_importer import (QAbstractItemView, QIcon,
                                            QMainWindow, QMessageBox,
                                            QStandardItemModel,
                                            QSystemTrayIcon)
from wiki_music.ui.gui_Qt_base import Ui_MainWindow
from wiki_music.utilities import MultiLog, abstract_warning, get_icon, log_gui

log_gui.debug("base imports done")

# inherit base from QMainWindow and lyaout from Ui_MainWindow
class BaseGui(QMainWindow, Ui_MainWindow):
    """ Base class for all GUI classes, initializes UI and needed variables.
        Connects buttons and input fields signals to methods.
    """

    def __init__(self) -> None:

        log_gui.debug("init base")

        # call QMainWindow __init__ method
        super().__init__()
        # call Ui_MainWindow user interface setup method
        super().setupUi(self)

        # initialize
        self.__initUI__()

        # misc
        self.work_dir: str = ""
        self.log: MultiLog = MultiLog(log_gui)

        log_gui.debug("init base done")

    def __initUI__(self):
        self.setWindowTitle("Wiki Music")
        myappid = "WikiMusic"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        _icon = get_icon()
        self.setWindowIcon(QIcon(_icon))
        tray_icon = QSystemTrayIcon(QIcon(_icon))
        tray_icon.show()

    def __do_nothing__(self):
        log_gui.warning("Not implemented yet")
        QMessageBox(QMessageBox.Warning,
                    "Info", "Not implemented yet!").exec_()

    @abstractmethod
    def __display_image__(self, image=None):
        abstract_warning()
