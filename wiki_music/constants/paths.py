from wiki_music.package_setup import module_path
from os.path import join

__all__ = ["ROOT_DIR", "DIR_FILE", "MP3_TAG", "LOG_DIR"]

ROOT_DIR: str = module_path()
DIR_FILE: str = join(ROOT_DIR, "data", "last_opened.txt")
LOG_DIR: str = join(ROOT_DIR, "logs")
MP3_TAG: str = r"C:\Program Files (x86)\Mp3tag\Mp3tag.exe"
