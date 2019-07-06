# Module for variable synchronization between application and GUI

from threading import Barrier, Lock

# Class for synchronizing info between threads
#
# info_exchange class provides means to synchronize some
# variables between gui and application, it serves to pass
# the questions asked in application to to PyQt (Tkinter) frontend.

__all__ = ["SharedVars"]


class SharedVars:

    write_lyrics = None
    select_genre = None
    assign_artists = None
    write_tags = None
    wait = None
    switch = None
    done = False
    load = False

    # action description
    describe = ""

    # caught exceptions
    _exception = None
    _warning = None
    ask_exit = None

    # switches
    wait_exit = False
    terminate_app = False

    # threads
    parser_running = False

    # exceptions
    warning = None
    exception = None

    # mics
    write_json = False
    offline_debbug = False
    lock = Lock()
    barrier = Barrier(2)

    @classmethod
    def re_init(cls):

        cls.write_lyrics = None
        cls.select_genre = None
        cls.assign_artists = None
        cls.write_tags = None
        cls.wait = None
        cls.switch = None
        cls.done = False
        cls.load = False

        # action description
        cls.describe = ""

        # caught exceptions
        cls._exception = None
        cls._warning = None
        cls.ask_exit = None

        # switches
        cls.wait_exit = False
        cls.terminate_app = False

        # threads
        cls.preload = None
        cls.parser_running = False

        # exceptions
        cls.warning = None
        cls.exception = None
