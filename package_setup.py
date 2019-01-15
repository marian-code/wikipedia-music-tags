import os
import sys


def we_are_frozen():
    # All of the modules are built-in to the interpreter, e.g., by py2exe
    return hasattr(sys, "frozen")


def module_path():
    # encoding = sys.getfilesystemencoding()
    if we_are_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)

sys.path.append(os.path.join(module_path(), ".."))

if we_are_frozen() is True:
    from multiprocessing import freeze_support
    freeze_support()

if we_are_frozen() is True:
    f = open(os.devnull, 'w')
    sys.stdout = f
    sys.stderr = f
