"""wiki_music GUI entry point."""

import logging
import sys
from threading import current_thread

from wiki_music.gui_lib.main_window import Window
from wiki_music.gui_lib.qt_importer import QApplication
from wiki_music.utilities import input_parser, set_log_handles


def main():
    """GUI entry point."""
    # setup logging levels and add file handles.
    debug = input_parser()[-1]
    if debug:
        set_log_handles(logging.DEBUG)
    else:
        set_log_handles(logging.INFO)

    current_thread().name = "GuiThread"
    app = QApplication(sys.argv)
    ui = Window(debug=debug)
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
