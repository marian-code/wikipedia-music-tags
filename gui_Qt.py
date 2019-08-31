# pylint: disable=no-name-in-module
import package_setup

if __name__ == "__main__":
    from utilities.utils import clean_logs
    clean_logs()

import os
from abc import ABC, abstractmethod
import subprocess
import sys
import time
import webbrowser
import ctypes
from threading import Thread, current_thread
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QApplication,
                             QTableWidgetItem, QMessageBox, QAbstractItemView,
                             QInputDialog, QLabel, QVBoxLayout, QTableWidget,
                             QWidget, QDialog, QStatusBar, QHBoxLayout,
                             QSystemTrayIcon)
from PyQt5.QtGui import (QStandardItemModel, QStandardItem, QImage, QPixmap,
                         QIcon, QPainter)
from PyQt5.QtCore import (Qt, QSortFilterProxyModel, QTimer, pyqtProperty,
                          pyqtSlot)

from utilities.loggers import log_gui

log_gui.debug("started imports")

from wiki_music import parser
from wiki_music.external_libraries.google_images_download import google_images_download
from wiki_music.ui.gui_Qt_base import Ui_MainWindow
from wiki_music.ui.art_dialog_base import Ui_Dialog
from wiki_music.ui.cover_art_base import Ui_cover_art_search
from wiki_music.application import get_lyrics, get_wiki
from wiki_music.library import write_tags
from wiki_music.utilities.utils import list_files, we_are_frozen, module_path
from wiki_music.utilities.gui_utils import *  # pylint: disable=unused-wildcard-import
from utilities.sync import SharedVars
from utilities.wrappers import exception, synchronized

log_gui.debug("finished imports")


class NumberSortModel(QSortFilterProxyModel):

    def lessThan(self, left_index, right_index):

        left_var = left_index.data(Qt.EditRole)
        right_var = right_index.data(Qt.EditRole)

        try:
            return float(left_var) < float(right_var)
        except (ValueError, TypeError):
            pass

        try:
            return left_var < right_var
        except TypeError:  # in case of NoneType
            return True


class CustomQStandardItem(QStandardItem):
    """Overrides default methods so only the filename is "displayed"
    even though the object stores the full path
    """

    def data(self, role):
        if role != 0:
            return super(CustomQStandardItem, self).data(role)
        else:
            filtered = super(CustomQStandardItem, self).data(role)
            filtered = str(os.path.split(filtered)[1])
            return filtered

    def real_data(self, role):
        return super(CustomQStandardItem, self).data(role)

    def text(self):
        text_text = super(CustomQStandardItem, self).text()
        text_data = self.real_data(Qt.DisplayRole)

        if len(text_data) > len(text_text):
            return text_data
        else:
            return text_text


class ImageWidget(QWidget):
    def __init__(self, text, img, parent=None):
        QWidget.__init__(self, parent)

        self._text = text
        self._img = img

        self.setLayout(QVBoxLayout())
        self.lbPixmap = QLabel(self)
        self.lbText = QLabel(self)
        self.lbText.setAlignment(Qt.AlignCenter)

        self.layout().addWidget(self.lbPixmap)
        self.layout().addWidget(self.lbText)

        self.initUi()

    def initUi(self):
        image = QImage()
        image.loadFromData(self._img)
        self.lbPixmap.setPixmap(QPixmap(image).scaledToWidth(150))
        self.lbText.setText(self._text)

    @pyqtProperty(str)
    def img(self):
        return self._img

    @img.setter
    def total(self, value):
        if self._img == value:
            return
        self._img = value
        self.initUi()

    @pyqtProperty(str)
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if self._text == value:
            return
        self._text = value
        self.initUi()


class ImageTable(QTableWidget):
    def __init__(self, parent=None):
        QTableWidget.__init__(self, parent)

        self.max_columns = 4
        self.actualCol = -1
        self.setColumnCount(1)
        self.setRowCount(1)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        # self.cellClicked.connect(self.onCellClicked)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

    """
    @pyqtSlot(int, int)
    def onCellClicked(self, row, column):
        w = self.cellWidget(row, column)
        print(row, column)
    """

    def add_pic(self, label, picture):

        if self.actualCol < self.max_columns:
            self.actualCol += 1
            if self.rowCount() == 1:
                self.setColumnCount(self.columnCount() + 1)
        elif self.actualCol == self.max_columns:
            self.actualCol = 0
            self.setRowCount(self.rowCount() + 1)

        i = self.rowCount() - 1
        j = self.actualCol
        lb = ImageWidget(label, picture)
        self.setCellWidget(i, j, lb)

        self.resizeColumnsToContents()
        self.resizeRowsToContents()


# these method don't work alone, they must be inherited by Window class
class Gui2Parser:
    """ Methods for data transfer between  gui <--> parser object.
        This class is not stand-alone. It should be inherited and attributes in
        __init__ should be redefined.
    """

    def __init__(self):
        self.genre_entry = None
        self.year_entry = None
        self.album_entry = None
        self.band_entry = None
        self.table = None
        self.picture_visible = None
        self.picture_layout = None

    def __parser_to_gui__(self):

        self.genre_entry.setText(parser.selected_genre)
        self.year_entry.setText(parser.release_date)
        self.album_entry.setText(parser.album)
        self.band_entry.setText(parser.band)

        numbers = self.__spawn_rows_cols__(parser.numbers)
        tracks = self.__spawn_rows_cols__(parser.tracks)
        types = self.__spawn_rows_cols__(parser.types)
        disc_num = self.__spawn_rows_cols__(parser.disc_num)
        artists = self.__spawn_rows_cols__(parser.artists)
        lyrics = self.__spawn_rows_cols__(parser.lyrics)
        composers = self.__spawn_rows_cols__(parser.composers)
        files = self.__spawn_rows_cols__(parser.files)

        # on first display in gui there are no lyrics yet
        if not lyrics:
            for _ in numbers:
                lyrics.append("")

        # files must always be at the last place because it uses custom
        # QstandardItem - refer to __update_model__ function
        return [numbers, tracks, types, artists, composers, disc_num, lyrics,
                files]

    def __spawn_rows_cols__(self, data):

        temp = []
        for i in range(len(data)):
            temp.append("")
            if isinstance(data[i], str):
                temp[i] = data[i]
            elif isinstance(data[i], (int, float)):
                temp[i] = str(data[i])
            elif isinstance(data[i], type(None)):
                temp[i] = ""
            elif isinstance(data[i], list):
                temp[i] = ", ".join(sorted(data[i]))

        return temp

    def __gui_to_parser__(self):
        parser.selected_genre = self.genre_entry.text()
        parser.release_date = self.year_entry.text()
        parser.album = self.album_entry.text()
        parser.band = self.band_entry.text()

        # TODO non-atomic
        parser.numbers = self.__unspawn_rows_cols__(0)
        parser.tracks = self.__unspawn_rows_cols__(1)
        parser.types = self.__unspawn_rows_cols__(2, separate=True)
        parser.disc_num = self.__unspawn_rows_cols__(5)
        parser.artists = self.__unspawn_rows_cols__(3, separate=True)
        parser.lyrics = self.__unspawn_rows_cols__(6)
        parser.composers = self.__unspawn_rows_cols__(4, separate=True)
        parser.files = self.__unspawn_rows_cols__(7)

    def __unspawn_rows_cols__(self, col, separate=False):

        temp = []
        for row in range(self.table.rowCount()):
            temp.append(self.table.item(row, col).text())
            if "," in temp[row] and separate:
                temp[row] = [x.strip() for x in temp[row].split(",")]

        return temp

    def __display_image__(self, image=None):

        if parser.cover_art is not None:
            _img = parser.cover_art
        elif image is not None:
            _img = image
        else:
            return 0

        image = QImage()
        image.loadFromData(_img)

        # TODO not working if picture has been selected multiple times
        # only the first one is displayed
        self.lbl = QLabel(self)
        self.lbl.setPixmap(QPixmap(image))

        if not self.picture_visible:
            self.picture_layout.addWidget(self.lbl)
            self.picture_visible = True


class DataModel:
    """ This class is not stand-alone. It should be inherited and attributes in
        __init__ should be redefined.
    """

    def __init__(self):
        self.table = None
        self.tableView = None
        self.number_detail = None
        self.title_detail = None
        self.artist_detail = None
        self.composer_detail = None
        self.lyrics_detail = None
        self.file_detail = None
        self.proxy = None

    @abstractmethod
    def __parser_to_gui__(self):
        abstract_warning()

    # methods for managing gui data model
    @exception(log_gui)
    def __update_model__(self):
        """
        gets called after conditonns check is done
        from within conditions check function
        """

        n_entries = len(parser)

        if n_entries > 0:

            log_gui.debug("parser to gui")
            # TODO non-atomic
            text_var = self.__parser_to_gui__()

            log_gui.debug("init entries")
            self.table.setRowCount(n_entries)
            for row in range(n_entries):
                for col, tv in enumerate(text_var):
                    # files column uses custom QStandardItem which shows
                    # only filename not the full path, files must be
                    # always last in text_var
                    if col == len(text_var) - 1:
                        item = CustomQStandardItem(tv[row])
                    else:
                        item = QStandardItem(tv[row])

                    self.table.setItem(row, col, item)

            self.tableView.update()
            for col, _ in enumerate(text_var):
                # resize all but the column with lyrics
                if col != len(text_var) - 2:
                    self.tableView.resizeColumnToContents(col)

            log_gui.debug("init entries done")
        else:
            QTimer.singleShot(100, self.__update_model__)

    @exception(log_gui)
    def __detail__(self, proxy_index):
        """
        Display detail of the row that is clicked
        """

        # proxy_index is QModelIndex proxyIndex Class type
        # it is index of data mapping as shown in gui
        # real indeces are different
        source_index = self.proxy.mapToSource(proxy_index)
        row = source_index.row()

        # maintain row highlight
        index = self.tableView.selectionModel().selectedRows()
        self.tableView.selectRow(index[0].row())

        entries = [
            self.number_detail,
            self.title_detail,
            None,
            self.artist_detail,
            self.composer_detail,
            None,
            self.lyrics_detail,
            self.file_detail
        ]

        log_gui.debug("connect detail function")

        for col, e in enumerate(entries):
            if e is not None:
                e.disconnect()
                e.setText(self.table.item(row, col).text())
                # col_inner = col is a hack to change the
                # scope of col otherwise lambda will refer
                # to actual value of col since it is in
                # outer scope
                # None is the default argument for text since QTextEdit
                # signal doesn´t retutn text
                e.textChanged.connect(lambda text=None, col_inner=col:
                                      self.__text_check__(row, col_inner,
                                                          text))

    def __text_check__(self, row, col, text):

        if text is None:
            item = QStandardItem(self.lyrics_detail.toPlainText())
        else:
            # because file has custom QStandardItem
            if isinstance(self.table.item(row, col), CustomQStandardItem):
                item = CustomQStandardItem(text)
            else:
                item = QStandardItem(text)

        self.table.setItem(row, col, item)


class Checkers(DataModel):
    """ This class is not stand-alone. It should be inherited and attributes in
        __init__ should be redefined.
    """

    def __init__(self):
        self.statusbar = None
        self.input_work_dir = None

    @abstractmethod
    def exec_(self):
        abstract_warning()

    @abstractmethod
    def __display_image__(self):
        abstract_warning()

    def __init_checkers__(self):
        self.description_timer = QTimer()
        self.description_timer.timeout.connect(self.__description_checker__)
        self.description_timer.setSingleShot(True)

        self.exception_timer = QTimer()
        self.exception_timer.timeout.connect(self.__exception_check__)
        self.exception_timer.setSingleShot(True)

        self.conditions_timer = QTimer()
        self.conditions_timer.timeout.connect(self.__conditions_check__)
        self.conditions_timer.setSingleShot(True)

    def __start_checkers__(self):
        self.description_timer.start(200)
        self.exception_timer.start(500)
        self.conditions_timer.start(400)

    # periodically checking methods
    @exception(log_gui)
    def __conditions_check__(self):
        """
        checks for answers to questins the main app asks
        the sends them back to app
        """

        def msg_to_bool(out):
            if out == QMessageBox.Yes:
                return True
            else:
                return False

        if SharedVars.wait:

            if SharedVars.switch == "genres":

                log_gui.debug("initialize question window")
                # TODO non-atomic
                if not parser.genres:
                    text, ok = QInputDialog.getText(self,
                                                    "Text Input Dialog",
                                                    "Input genre:")
                    if ok:
                        parser.selected_genre = text
                    else:
                        parser.selected_genre = "N/A"
                else:
                    item, ok = QInputDialog.getItem(self,
                                                    "Select input dialog",
                                                    "List of genres",
                                                    parser.genres, 0,
                                                    False)
                    if ok:
                        parser.selected_genre = item
                    else:
                        parser.selected_genre = "N/A"

            if SharedVars.load:
                QTimer.singleShot(0, self.__update_model__)

            if SharedVars.switch == "comp":
                log_gui.debug("ask to copy composers")
                msg = QMessageBox(QMessageBox.Question, "Question",
                                  "Do you want to copy artists to composers?",
                                  QMessageBox.Yes | QMessageBox.No)

                SharedVars.assign_artists = msg_to_bool(msg.exec_())

            if SharedVars.switch == "lyrics":
                log_gui.debug("ask to find lyrics")
                msg = QMessageBox(QMessageBox.Question, "Question",
                                  "Do you want to find lyrics?",
                                  QMessageBox.Yes | QMessageBox.No)

                SharedVars.write_lyrics = msg_to_bool(msg.exec_())

            SharedVars.load = False
            SharedVars.switch = None
            SharedVars.wait = False

        if not SharedVars.done:
            self.conditions_timer.start(200)
        else:
            # announce that gui has reached the barrier
            log_gui.debug("gui reached barrier")
            SharedVars.barrier.wait()

            log_gui.debug("start __update_model__ function")
            QTimer.singleShot(0, self.__update_model__)
            self.__display_image__()

    def __exception_check__(self):
        if SharedVars.exception is not None:
            msg = QMessageBox(QMessageBox.Critical, "Exception",
                              SharedVars.exception)
            msg.setDetailedText(open(r"logs/wiki_music_parser.log",
                                     "r").read())
            msg.exec_()
            SharedVars.exception = None

        if SharedVars.warning is not None:
            QMessageBox(QMessageBox.Warning, "Warning",
                        SharedVars.warning).exec_()
            SharedVars.warning = None

        if SharedVars.ask_exit is not None:
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
                SharedVars.ask_exit = None

        self.exception_timer.start(500)

    # lock must be here because there are non atomic operations i.e. +=
    @exception(log_gui)
    @synchronized(SharedVars.lock)
    def __description_checker__(self):

        self.description_timer.start(400)

        if " . . ." in SharedVars.describe:
            SharedVars.describe = SharedVars.describe.replace(" . . .", "")

        self.remember = SharedVars.describe

        if SharedVars.describe != " " and SharedVars.describe != "":
            if (self.remember == SharedVars.describe and
                "Done" not in SharedVars.describe):  # noqa E129
                SharedVars.describe += " ."
            self.statusbar.showMessage(SharedVars.describe)
        else:
            self.statusbar.showMessage("")


class Buttons:
    """ This class is not stand-alone. It should be inherited and attributes in
        __init__ should be redefined.
    """

    def __init__(self):
        self.file_detail = None
        self.json_write_sw = None
        self.offline_debbug_sw = None
        self.input_work_dir = None

    @exception(log_gui)
    def __open_dir__(self):

        if not self.input_work_dir:
            QMessageBox(QMessageBox.Information, "Message",
                        "You must select directory first!").exec_()

        else:
            print("Opening folder...")
            os.startfile(self.input_work_dir)
            """
            if sys.platform == "linux" or sys.platform == "linux2":
                subprocess.check_call(['xdg-open',
                                        self.input_work_dir.get()])
            elif sys.platform == "win32":
                #subprocess.Popen('explorer "self.input_work_dir.get()"')
            """

    def __select_file__(self):
        _file = QFileDialog.getOpenFileName(self,
                                            "Select song file",
                                            self.input_work_dir,
                                            "Audio files (*.mp3 *.flac *.m4a)"
                                            ";;All files (*)")

        self.file_detail.setText(_file[0])

    @exception(log_gui)
    def __open_browser__(self):

        if parser.url is not None:
            webbrowser.open_new_tab(parser.url)
        else:
            QMessageBox(QMessageBox.Information, "Message",
                        "You must run the search first!").exec_()

    @exception(log_gui)
    def __run_Mp3tag__(self):

        if not self.input_work_dir:
            QMessageBox(QMessageBox.Information, "Message",
                        "You must select directory first!").exec_()
        else:
            subprocess.Popen([r"C:\Program Files (x86)\Mp3tag\Mp3tag.exe",
                              r'/fp:' + self.input_work_dir])

    def __entry_band__(self, text):
        parser.band = text

    def __entry_album__(self, text):
        parser.album = text

    def __select_json__(self):
        SharedVars.write_json = self.json_write_sw.isChecked()

    def __select_offline_debbug__(self):
        SharedVars.offline_debbug = self.offline_debbug_sw.isChecked()
        if SharedVars.offline_debbug:
            parser.preload.stop()

    def __do_nothing__(self):
        log_gui.warning("Not implemented yet")
        QMessageBox(QMessageBox.Warning,
                    "Info", "Not implemented yet!").exec_()


# inherit base from QMainWindow and lyaout from Ui_MainWindow
class Window(QMainWindow, Ui_MainWindow, Gui2Parser, Checkers, Buttons):

    def __init__(self):
        # call QMainWindow __init__ method
        super(Window, self).__init__()
        # call Ui_MainWindow user interface setup method
        super(Window, self).setupUi(self)

        # initialize
        self.__initUI__()

        # misc
        self.input_work_dir = ""
        self.input_album = ""
        self.input_band = ""
        self.write_json = False
        self.offline_debbug = False
        self.picture_visible = False

        # tag related variables
        self.files_prewiew = []

        # init checker
        self.remember = None
        self.__init_checkers__()
        self.__start_checkers__()

        # * PyQt5 Native
        # set overlay functions
        self.__setup_overlay__()

    # setup methods
    def __setup_overlay__(self):

        # map buttons to functions
        # must use lambda otherwise wrapper doesnt work correctly
        self.browse_button.clicked.connect(lambda: self.__select_dir__())
        self.wiki_search_button.clicked.connect(lambda: self.__run_search__())
        self.coverArt.clicked.connect(lambda: self.__cover_art_search__())
        self.lyrics_button.clicked.connect(
            lambda: self.__run_lyrics_search__())
        self.toolButton.clicked.connect(lambda: self.__select_file__())
        self.band_entry_input.textChanged.connect(self.__entry_band__)
        self.album_entry_input.textChanged.connect(self.__entry_album__)

        # connect the album and band entry field to preload function
        self.band_entry.textChanged.connect(lambda: self.__preload__())
        self.album_entry.textChanged.connect(lambda: self.__preload__())

        # create table to hold the data
        self.table = QStandardItemModel()
        self.__table_headers__()

        # create table-proxy mapping for sorting
        self.proxy = NumberSortModel()
        self.proxy.setSourceModel(self.table)
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
        self.tableView.clicked.connect(self.__detail__)

        # connect menubar actions to functions
        # must use lambda otherwise wrapper doesnt work correctly
        self.actionDirectory.triggered.connect(lambda: self.__open_dir__())
        self.actionWikipedia.triggered.connect(lambda: self.__open_browser__())
        self.actionMp3_Tag.triggered.connect(lambda: self.__run_Mp3tag__())

        # connect menubar actions to functions
        self.actionAll_Tags.triggered.connect(lambda: self.__save_all__(False))
        self.actionOnly_Lyrics.triggered.connect(
            lambda: self.__save_all__(True))

        # menubar buttons taht are not implemented
        self.actionNew.triggered.connect(self.__do_nothing__)
        self.actionOpen.triggered.connect(self.__do_nothing__)
        self.actionExit.triggered.connect(self.__do_nothing__)
        self.actionSave.triggered.connect(self.__do_nothing__)

        self.actionHelp_Index.triggered.connect(self.__do_nothing__)
        self.actionAbout.triggered.connect(self.__do_nothing__)
        self.actionGit.triggered.connect(self.__do_nothing__)

        if we_are_frozen():
            # show switches only if not frozen
            self.offline_debbug_sw.hide()
            self.json_write_sw.hide()
        else:
            # connect switches to functions
            self.offline_debbug_sw.stateChanged.connect(
                self.__select_offline_debbug__)
            self.json_write_sw.stateChanged.connect(self.__select_json__)

    def __initUI__(self):
        self.setWindowTitle("Wiki Music")
        myappid = "WikiMusic"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        _icon = os.path.join(module_path(), "files", "icon.ico")
        if not os.path.isfile(_icon):
            raise FileNotFoundError(f"There is no icon file in: {_icon}")
        self.setWindowIcon(QIcon(_icon))
        tray_icon = QSystemTrayIcon(QIcon(_icon))
        tray_icon.show()

    def __table_headers__(self):
        _headers = ["Number:", "Name:", "Type:", "Artists:", "Composers:",
                    "Discnumber:", "Lyrics:", "File:"]
        self.table.setHorizontalHeaderLabels(_headers)

    def __init_parser__(self):
        # TODO non-atomic
        parser.__init__(protected_vars=False)
        parser.work_dir = self.input_work_dir
        SharedVars.re_init()

    # methods that bind to gui elements
    @exception(log_gui)
    def __save_all__(self, lyrics_only):

        # first stop any running preload, as it is not needed any more
        parser.preload.stop()

        # TODO non-atomic
        if not parser.numbers:
            QMessageBox(QMessageBox.Information, "Info",
                        "You must run the search first!").exec_()
        else:
            if self.input_work_dir == "":
                QMessageBox(QMessageBox.Information, "Info",
                            "You must specify directory with files!").exec_()
                return None

            self.__gui_to_parser__()
            dict_data, writable = parser.data_to_dict()

            if writable:
                for data in dict_data:
                    write_tags(data, lyrics_only=lyrics_only)
            else:
                QMessageBox(QMessageBox.Information, "Info",
                            "Cannot write tags because there are no "
                            "coresponding files")

            # reload files from disc after save
            self.__init_parser__()
            parser.read_files()
            self.__update_model__()

    @exception(log_gui)
    def __select_dir__(self):

        dir_file = os.path.join(os.getcwd(), "data", "last_opened.txt")

        # load last opened dir
        try:
            f = open(dir_file, "r")
        except FileNotFoundError:
            start_dir = get_music_path()
        else:
            start_dir = f.readline().strip()

        # select dir
        self.input_work_dir = QFileDialog.getExistingDirectory(self,
                                                               "Open Folder",
                                                               start_dir)

        # record last opened dir
        with open(dir_file, "w") as f:
            f.write(self.input_work_dir)

        parser.work_dir = self.input_work_dir

        # TODO non-atomic
        parser.read_files()

        self.input_album = parser.album
        self.input_band = parser.band

        self.band_entry_input.setText(self.input_band)
        self.album_entry_input.setText(self.input_album)
        self.__preload__(first=True)

        self.display_dir.setText(self.input_work_dir)
        self.band_entry.setText(self.input_band)
        self.album_entry.setText(self.input_album)

        self.__update_model__()

    def __preload__(self, first=False):
        album = self.album_entry_input.text()
        band = self.band_entry_input.text()

        # if no changes occured and this is not the first call,
        # return imediately
        if not first:
            if self.input_album == album and self.input_band == band:
                return

        self.input_album = album
        self.input_band = band

        # offline debug must be dissabled
        if not SharedVars.offline_debbug:
            # band and album entry must be non-empty strings
            if self.input_band and self.input_album:
                parser.preload.stop()
                parser.preload.start()

    def __check_input_is_present__(self):

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Message")

        if self.input_band == "":
            msg.setText("You must input artist!")
            msg.exec_()
            return False
        elif self.input_album == "":
            msg.setText("You must input album!")
            msg.exec_()
            return False
        elif self.input_work_dir in ("", None):
            msg.setText("You must select working directory!")
            msg.exec_()
            return False
        else:
            return True

    @exception(log_gui)
    def __run_search__(self, *args):

        self.input_band = self.band_entry_input.text()
        self.input_album = self.album_entry_input.text()

        if not self.__check_input_is_present__():
            return

        log_gui.info("starting wikipedia search")

        # TODO non-atomic
        self.__init_parser__()
        parser.files = list_files(parser.work_dir)

        self.__start_checkers__()

        main_app = Thread(target=get_wiki, name="WikiSearch", args=(True,))
        main_app.daemon = True
        main_app.start()

    @exception(log_gui)
    def __run_lyrics_search__(self, *args):

        parser.preload.stop()

        self.input_band = self.band_entry_input.text()
        self.input_album = self.album_entry_input.text()

        if not self.__check_input_is_present__():
            return

        log_gui.info("starting lyrics search")

        self.__start_checkers__()
        main_app = Thread(target=get_lyrics, name="LyricsSearch", args=(True,))
        main_app.start()

        log_gui.debug("lyrics search started")

    @exception(log_gui)
    def __cover_art_search__(self):

        def _async_search():

            new_count = self.imd.count
            if new_count > self.old_count:
                for i in range(self.old_count, new_count):
                    s = self.imd.fullsize_dim[i]
                    t = self.imd.thumbs[i]
                    try:
                        dim = "{}x{}\n{:.2f}Kb".format(s[1][0], s[1][1],
                                                       s[0] / 1024)
                    except TypeError:
                        break
                    """
                    if t is None:
                        with open("files/Na.jpg", "rb") as imageFile:
                            t = bytearray(imageFile.read())
                        break
                    """
                    self.image_table.add_pic(dim, t)
                    # TODO not working
                    image_table_w.progressBar.setValue(new_count / 20)

                self.old_count = new_count

            if not self.cover_art_search.isVisible():
                self.imd.exit = True
            else:
                QTimer.singleShot(100, _async_search)

        if parser.band is None or parser.album is None:
            QMessageBox(QMessageBox.Information, "Message",
                        "You must input Artist and Album first").exec_()
            return 0

        self.imd = google_images_download.googleimagesdownload()
        self.old_count = self.imd.count

        query = "{} {}".format(parser.band, parser.album)
        arguments = {
            "keywords": query,
            "limit": 20,
            "size": "large",
            "no_download": True,
            "no_download_thumbs": True,
            "thumbnail": True
        }

        # init thread that preforms the search
        self.image_search_thread = Thread(target=self.imd.download,
                                          args=(arguments, ),
                                          name="ImageSearch")
        self.image_search_thread.daemon = True
        self.image_search_thread.start()

        # init base dialog class
        self.cover_art_search = QDialog()
        self.cover_art_search.setWindowTitle("Wiki Music - Cover Art search")
        self.cover_art_search.setWindowIcon(QIcon(os.path.join(module_path(),
                                                               "files",
                                                               "icon.ico")))

        # int table for showing images
        self.image_table = ImageTable()
        self.image_table.cellClicked.connect(self.__select_picture__)

        # setup dialog layout and connect to button signals
        image_table_w = Ui_cover_art_search()
        image_table_w.setupUi(self.cover_art_search)
        image_table_w.verticalLayout.insertWidget(0, self.image_table)
        image_table_w.query.setText(query)
        image_table_w.load_button.clicked.connect(self.__do_nothing__)
        image_table_w.search_button.clicked.connect(self.__do_nothing__)
        image_table_w.browser_button.clicked.connect(self.__do_nothing__)
        image_table_w.cancel_button.clicked.connect(self.__do_nothing__)
        image_table_w.progressBar.setValue(0)

        self.cover_art_search.show()

        QTimer.singleShot(0, _async_search)

        SharedVars.describe = "Searching for Cover Art"

    @exception(log_gui)
    def __select_picture__(self, row, col):

        def _set_clipboard():
            nonlocal clipboard
            clipboard = self.image_dialog.ca_clipboard.isChecked()

        def _set_file():
            nonlocal _file
            _file = self.image_dialog.ca_file.isChecked()

        def _dialog_cancel():
            nonlocal cancel
            cancel = True

        # TODO when not nice round numbers - fails because of recursion
        # TODO these two methods keep calling each other
        # TODO make some function that corrects this
        @exception(log_gui)
        def _aspect_ratio_connect_X(dim_Y):
            value = int(original_ratio * dim_Y)
            self.image_dialog.size_spinbox_X.setValue(value)

        @exception(log_gui)
        def _aspect_ratio_connect_Y(dim_X):
            value = int((1 / original_ratio) * dim_X)
            self.image_dialog.size_spinbox_Y.setValue(value)

        size = None
        clipboard = True
        _file = None
        cancel = False

        # position of clicked picture in list
        index = (self.image_table.max_columns + 1) * row + col
        log_gui.info("clicked: {}".format(self.imd.fullsize_url[index]))

        # 0-th position is size in b, and 1-st position is tuple of dimensions
        dim = self.imd.fullsize_dim[index][1]
        try:
            dim_X, dim_Y = dim
        except TypeError:
            log_gui("exception index: {}".format(index))
            raise Exception("File cannot be accessed")

        original_ratio = dim_X / dim_Y

        # create dialog to get desired resize, save to disk
        # and copy to clipboard decision
        dialog_window = QDialog()
        dialog_window.setWindowTitle("Select options")
        self.image_dialog = Ui_Dialog()
        self.image_dialog.setupUi(dialog_window)

        # set values
        self.image_dialog.size_spinbox_X.setValue(dim_X)
        self.image_dialog.size_spinbox_Y.setValue(dim_Y)

        # TODO set file size in dialog
        # connect to dialog window button events
        self.image_dialog.ca_clipboard.stateChanged.connect(_set_clipboard)
        self.image_dialog.ca_file.stateChanged.connect(_set_file)
        self.image_dialog.buttonBox.rejected.connect(_dialog_cancel)
        self.image_dialog.size_spinbox_X.valueChanged.connect(
            _aspect_ratio_connect_Y)
        self.image_dialog.size_spinbox_Y.valueChanged.connect(
            _aspect_ratio_connect_X)
        dialog_window.rejected.connect(_dialog_cancel)

        dialog_window.exec_()

        if cancel:
            return 0

        self.cover_art_search.close()
        self.imd.exit = True
        self.__display_image__(self.imd.thumbs[index])

        size_X = self.image_dialog.size_spinbox_X.value()
        size_Y = self.image_dialog.size_spinbox_Y.value()

        size = (size_X, size_Y)
        if dim == size:
            size = None

        if _file:
            _file = os.path.join(self.input_work_dir, "Folder.jpg")

        SharedVars.describe = "Downloading full size cover art"
        log_gui.info("Downloading full size cover art from: "
                     "{}".format(self.imd.fullsize_url[index]))

        result = image_handle(self.imd.fullsize_url[index], size=size,
                              clipboad=clipboard, path=_file, log=log_gui)

        if result is not True:
            SharedVars.exception = ("Error in processing Cover Art "
                                    "{}".format(result))
            log_gui.exception(result)
            return 0

        if size is not None:
            SharedVars.describe = "Cover art resized to: {}x{}".format(*size)
            log_gui.info("Cover art resized to: {}x{}".format(*size))
        if clipboard:
            SharedVars.describe = "Cover art copied to clipboard"
            log_gui.info("Cover art copied to clipboard")
        if _file is not None:
            SharedVars.describe = "Cover art saved to file"
            log_gui.info("Cover art saved to file")


if __name__ == "__main__":
    current_thread().name = "GuiThread"
    app = QApplication(sys.argv)
    ui = Window()
    ui.show()
    sys.exit(app.exec_())
