""" wiki_music GUI entry point. """

import sys
from threading import  current_thread

try:
    import package_setup
except ImportError:
    pass  # not needed for the frozen app

from wiki_music.gui_lib.main_window import Window
from wiki_music.gui_lib.qt_importer import QApplication


if __name__ == "__main__":

    current_thread().name = "GuiThread"
    app = QApplication(sys.argv)
    ui = Window()
    ui.show()
    sys.exit(app.exec_())
