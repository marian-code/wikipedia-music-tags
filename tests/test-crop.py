import os
import sys

# append package parent directory to path
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..")))

from wiki_music.gui import SelectablePixmap
from wiki_music.gui.cover_art import PictureEdit
from wiki_music.gui.qt_importer import QApplication

if __name__ == '__main__':
    with open("input.jpg", "rb") as f:
        bytes_image = f.read()

    """
    myQApplication = QApplication(sys.argv)
    myQExampleLabel = SelectablePixmap(bytes_image)
    myQExampleLabel.show()
    sys.exit(myQApplication.exec_())
    """

    myQApplication = QApplication(sys.argv)
    myQExampleLabel = PictureEdit((100, 100), bytes_image)
    myQExampleLabel.show()
    sys.exit(myQApplication.exec_())