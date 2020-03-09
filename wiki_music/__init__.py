"""Root file of wiki_music.

Sets which modules are lazy imported on package level and reads
package __version__
"""

import logging
from sys import argv

from lazy_import import lazy_module

#: specifies version of the package
logging.getLogger(__name__)

__version__: str

try:
    from version import __version__
except ImportError:
    __version__ = "unknown"

# mark modules as lazy
# if we are subsequently importing submodule, it must be done as:
# import module.sub_module as sub_module
lazy_module("re")
lazy_module("os")
lazy_module("io")
lazy_module("bs4")
lazy_module("json")
lazy_module("queue")
lazy_module("ctypes")
lazy_module("pickle")
lazy_module("urllib")
lazy_module("winreg")
lazy_module("mutagen")
lazy_module("operator")
lazy_module("requests")
lazy_module("argparse")
lazy_module("itertools")
lazy_module("wikipedia")
lazy_module("webbrowser")
lazy_module("subprocess")
lazy_module("datefinder")
lazy_module("collections")
lazy_module("configparser")
lazy_module("PIL.Image")
lazy_module("PIL.ImageFile")
lazy_module("fuzzywuzzy.fuzz")
lazy_module("fuzzywuzzy.process")
lazy_module("wiki_music.external_libraries.lyricsfinder")
lazy_module("wiki_music.external_libraries.google_images_download"
            ".google_images_download")
lazy_module("wiki_music.external_libraries.google_images_download"
            ".google_images_download_offline")
