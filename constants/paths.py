from wiki_music.package_setup import module_path
from os.path import join

__all__ = ["ROOT_DIR", "DIR_FILE", "MP3_TAG"]

ROOT_DIR = module_path()
DIR_FILE = join(ROOT_DIR, "data", "last_opened.txt")
MP3_TAG = r"C:\Program Files (x86)\Mp3tag\Mp3tag.exe"
