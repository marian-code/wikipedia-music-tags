"""Hook for wiki_music."""

from PyInstaller.utils.hooks import collect_data_files
from wiki_music.constants import ROOT_DIR
import os

hiddenimports = [
    "wiki_music.version",
    # all the following are lazy loaded so pyinstaller cannot find them
    "wiki_music.library.tags_handler.tag_base",
    "wiki_music.library.tags_handler.mp3",
    "wiki_music.library.tags_handler.m4a",
    "wiki_music.library.tags_handler.flac",
    "wiki_music.external_libraries.lyricsfinder.extractors.animelyrics",
    "wiki_music.external_libraries.lyricsfinder.extractors.azlyrics",
    "wiki_music.external_libraries.lyricsfinder.extractors.darklyrics",
    "wiki_music.external_libraries.lyricsfinder.extractors.genius",
    "wiki_music.external_libraries.lyricsfinder.extractors.lyrical_nonsense",
    "wiki_music.external_libraries.lyricsfinder.extractors.lyricsmode",
    "wiki_music.external_libraries.lyricsfinder.extractors.musixmatch",
]

# collect the ui files
UI_PATH = os.path.join(ROOT_DIR, "ui")

datas = []
for f in os.scandir(UI_PATH):
    if f.is_file() and f.name.endswith(".ui"):
        datas.append((os.path.join(UI_PATH, f.name), "ui"))
