# pylint: disable=no-name-in-module
import os
import sys
import time
import webbrowser
from subprocess import Popen
from threading import Thread, current_thread

import package_setup
from wiki_music.application import get_lyrics, get_wiki
from wiki_music.constants.paths import MP3_TAG
from wiki_music.gui import (BaseGui, CoverArtSearch, DataModel,
                            NumberSortModel, RememberDir)
from wiki_music.gui.qt_importer import (
    QAbstractItemView, QApplication, QFileDialog, QInputDialog, QMessageBox,
    QTimer)
from wiki_music.utilities import (SharedVars, clean_logs, exception, log_gui,
                                  synchronized, we_are_frozen)

if __name__ == "__main__":
    clean_logs()


class Checkers(BaseGui):
    """ This class is not stand-alone. It should be inherited and attributes in
        __init__ should be redefined.
    """

    def __init__(self):

        super().__init__()

        self.remember = None

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
                if not self.genres:
                    text, ok = QInputDialog.getText(self,
                                                    "Text Input Dialog",
                                                    "Input genre:")
                    if ok:
                        self.GENRE = text
                    else:
                        self.GENRE = "N/A"
                else:
                    item, ok = QInputDialog.getItem(self,
                                                    "Select input dialog",
                                                    "List of genres",
                                                    self.genres, 0,
                                                    False)
                    if ok:
                        self.GENRE = item
                    else:
                        self.GENRE = "N/A"

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

        if SharedVars.exception:
            msg = QMessageBox(QMessageBox.Critical, "Exception",
                              SharedVars.exception)
            msg.setDetailedText(open(r"logs/wiki_music_parser.log",
                                     "r").read())
            msg.exec_()
            SharedVars.exception = None

        if SharedVars.warning:
            QMessageBox(QMessageBox.Warning, "Warning",
                        SharedVars.warning).exec_()
            SharedVars.warning = None

        if SharedVars.ask_exit:
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

        if SharedVars.describe.strip() != "":
            if (self.remember == SharedVars.describe and
                "Done" not in SharedVars.describe):  # noqa E129
                SharedVars.describe += " ."
            self.statusbar.showMessage(SharedVars.describe)
        else:
            self.statusbar.showMessage("")


class Buttons(BaseGui):
    """ This class is not stand-alone. It should be inherited and attributes in
        __init__ should be redefined.
    """

    @exception(log_gui)
    def __open_dir__(self):

        if self.work_dir:
            print("Opening folder...")
            os.startfile(self.work_dir)
        else:
            QMessageBox(QMessageBox.Information, "Message",
                        "You must select directory first!").exec_()

    def __select_file__(self):
        _file = QFileDialog.getOpenFileName(self,
                                            "Select song file",
                                            self.work_dir,
                                            "Audio files (*.mp3 *.flac *.m4a)"
                                            ";;All files (*)")

        self.file_detail.setText(_file[0])

    @exception(log_gui)
    def __open_browser__(self):

        if self.url:
            webbrowser.open_new_tab(self.url)
        else:
            QMessageBox(QMessageBox.Information, "Message",
                        "You must run the search first!").exec_()

    @exception(log_gui)
    def __run_Mp3tag__(self):

        if self.work_dir:
            Popen([MP3_TAG, f"/fp:{self.work_dir}"])
        else:
            QMessageBox(QMessageBox.Information, "Message",
                        "You must select directory first!").exec_()

    def __entry_band__(self):
        self.ALBUMARTIST = self.band_entry_input.text()
        self.start_preload()

    def __entry_album__(self):
        self.ALBUM = self.album_entry_input.text()
        self.start_preload()

    def __select_json__(self):
        SharedVars.write_json = self.json_write_sw.isChecked()

    def __select_offline_debbug__(self):
        SharedVars.offline_debbug = self.offline_debbug_sw.isChecked()
        if SharedVars.offline_debbug:
            self.stop_preload()


class Window(DataModel, Checkers, Buttons, CoverArtSearch):

    def __init__(self):

        super().__init__()

        # set overlay functions
        self.__setup_overlay__()

        # start checkers
        self.__init_checkers__()
        self.__start_checkers__()

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

        # connect the album and band entry field to preload function
        self.band_entry_input.editingFinished.connect(self.__entry_band__)
        self.album_entry_input.editingFinished.connect(self.__entry_album__)

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

    # methods that bind to gui elements
    @exception(log_gui)
    def __save_all__(self, lyrics_only):

        # first stop any running preload, as it is not needed any more
        self.stop_preload()

        # TODO non-atomic
        if self.save_ready():
            QMessageBox(QMessageBox.Information, "Info",
                        "You must run the search first!").exec_()
        else:
            if self.work_dir == "":
                QMessageBox(QMessageBox.Information, "Info",
                            "You must specify directory with files!").exec_()
                return

            self._gui_to_parser()

            if not self.write_tags(lyrics_only=lyrics_only):
                msg = ("Cannot write tags because there are no "
                       "coresponding files")
                QMessageBox(QMessageBox.Information, "Info", msg)
                self.log.info(msg)

            # reload files from disc after save
            self.__init_parser__()
            self.read_files()
            self.__update_model__()

    @exception(log_gui)
    def __select_dir__(self):

        with RememberDir(self) as rd:
            self.work_dir = rd.get_dir()

        # TODO non-atomic
        # read files and start preload
        self.read_files()
        self.start_preload()

        self.__update_model__()

    def __check_input_is_present__(self):

        group = [self.ALBUMARTIST, self.ALBUM, self.work_dir]
        if all(group):
            return True
        else:
            alb, bnd, wkd, inp, com, _and = [""] * 6
            if not self.ALBUM:
                alb = " album"
            if not self.ALBUMARTIST:
                bnd = " band"
            if not self.work_dir:
                wkd = " select working directory"

            if any([alb, bnd]):
                inp = "input"
            if all([alb, bnd, wkd]):
                com = ","
            elif all([alb, bnd]):
                com = " and"
            if all([alb, wkd]) or all([wkd, bnd]):
                _and = " and"

            msg = f"You must {inp}{alb}{com}{bnd}{_and}{wkd}"

            message = QMessageBox()
            message.setIcon(QMessageBox.Information)
            message.setWindowTitle("Message")
            message.setText(msg)

    @exception(log_gui)
    def __run_search__(self, *args):

        if not self.__check_input_is_present__():
            return

        log_gui.info("starting wikipedia search")

        # TODO non-atomic
        self.__init_parser__()
        self.__start_checkers__()

        main_app = Thread(target=get_wiki, name="WikiSearch", args=(True,))
        main_app.daemon = True
        main_app.start()

    @exception(log_gui)
    def __run_lyrics_search__(self, *args):

        self.stop_preload()

        if not self.__check_input_is_present__():
            return

        log_gui.info("starting lyrics search")

        self.__start_checkers__()
        main_app = Thread(target=get_lyrics, name="LyricsSearch", args=(True,))
        main_app.start()

if __name__ == "__main__":

    current_thread().name = "GuiThread"
    app = QApplication(sys.argv)
    ui = Window()
    ui.show()
    sys.exit(app.exec_())
