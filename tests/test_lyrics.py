import os
import sys

# append package parent directory to path
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

from library import save_lyrics
from utilities.loggers import log_lyrics

log_lyrics.propagate = True


class DummyParser:

    def __init__(self):

        self.tracks = ["The Crimson Crown",
                       "When a Shadow is Forced Into the Light",
                       "When a Shadow is Forced Into Light",
                       "Firelights"]
        self.types = ["", "", "", ""]
        self.lyrics = ["", "", "", ""]
        self.album = "When a Shadow is Forced Into the Light"
        self.band = "Swallow The Sun"

    def __len__(self):
        return len(self.tracks)

parser = DummyParser()

print("created parser")

save_lyrics(parser)

for l in parser.lyrics:
    print("---------------------------------------")
    print(l)