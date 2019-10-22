import sys
import setup_tests

print("\n".join(sys.path))


from wiki_music.gui_lib import SelectablePixmap
from wiki_music.gui_lib.cover_art import PictureEdit
from wiki_music.gui_lib.qt_importer import QApplication

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
