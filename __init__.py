from . import package_setup
import os
from sys import argv

if "gui" in argv[0].lower():
    GUI_RUNNING = True
else:
    GUI_RUNNING = False

from .library import WikipediaParser  # noqa E402
parser = WikipediaParser()
