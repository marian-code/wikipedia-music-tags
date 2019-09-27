from . import package_setup
from sys import argv

if "gui" in argv[0].lower():
    GUI_RUNNING = True
else:
    GUI_RUNNING = False