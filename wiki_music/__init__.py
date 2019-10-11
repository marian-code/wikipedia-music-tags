"""wiki_music root file: __init__ sets which modules are lazy imported on
on package level and pulls in constants: __version__ and GUI_RUNNING."""

from sys import argv
from lazy_import import lazy_module

try:
    from version import __version__
except ImportError:
    __version__ = "unknown"  #: specifies version of the package

if "gui" in argv[0].lower():
    GUI_RUNNING = True  #: tells if GUI or CLI frontend is running
else:
    GUI_RUNNING = False

# mark modules as lazy
# if we are subsequently importing submodule, it must be done as:
# import module.sub_module as sub_module
lazy_module("re")
lazy_module("io")
lazy_module("bs4")
lazy_module("yaml")
lazy_module("queue")
lazy_module("pickle")
lazy_module("urllib")
lazy_module("winreg")
lazy_module("mutagen")
lazy_module("requests")
lazy_module("argparse")
lazy_module("wikipedia")
lazy_module("webbrowser")
lazy_module("subprocess")
lazy_module("datefinder")
lazy_module("collections")
lazy_module("PIL.Image")
lazy_module("PIL.ImageFile")
lazy_module("fuzzywuzzy.fuzz")
lazy_module("fuzzywuzzy.process")
lazy_module("wiki_music.external_libraries.lyricsfinder")
lazy_module("wiki_music.external_libraries.google_images_download"
            ".google_images_download")
lazy_module("wiki_music.external_libraries.google_images_download"
            ".google_images_download_offline")
