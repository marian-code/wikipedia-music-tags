## Module for variable synchronization between application and GUI

from threading import Barrier, Lock

## Class for synchronizing info between threads
#
# info_exchange class provides means to synchronize some
# variables between gui and application, it serves to pass
# the questions asked in application to to Tkinter frontend.

class info_exchange():

    def __init__(self):
        self.__set_default_values__()

        # mics
        self.write_json = False
        self.offline_debbug = False
        self.lock = Lock()
        self.barrier = Barrier(2)

    def re_init(self):
        self.__set_default_values__()

    def __set_default_values__(self):
        self.write_lyrics = None
        self.select_genre = None
        self.assign_artists = None
        self.write_tags = None
        self.wait = None
        self.switch = None
        self.done = False
        self.load = False

        # action description
        self.describe = ""

        # caught exceptions
        self._exception = None
        self._warning = None
        self.ask_exit = None

        # switches
        self.wait_exit = False
        self.terminate_app = False

    @property
    def exception(self):
        return self._exception

    @exception.setter
    def exception(self, string):
        if string is None:
            self._exception = string
        else:
            self._exception = str(string)

    @property
    def warning(self):
        return self._warning

    @warning.setter
    def warning(self, string):
        if string is None:
            self._warning = string
        else:
            self._warning = str(string)
