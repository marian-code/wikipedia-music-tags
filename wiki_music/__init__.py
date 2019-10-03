from sys import argv
from lazy_import import lazy_module

if "gui" in argv[0].lower():
    GUI_RUNNING = True
else:
    GUI_RUNNING = False

# mark modules as lazy
# if we are subsequently importing submodule, it must be done as:
# import module.sub_module as sub_module 
lazy_module("re")
lazy_module("io")
lazy_module("PIL")
lazy_module("bs4")
lazy_module("yaml")
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
lazy_module("win32clipboard")
lazy_module("fuzzywuzzy.fuzz")
lazy_module("fuzzywuzzy.process")
lazy_module("wiki_music.external_libraries.lyricsfinder")
lazy_module("wiki_music.external_libraries.google_images_download.google_images_download")
lazy_module("wiki_music.external_libraries.google_images_download.google_images_download_offline")