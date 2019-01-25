"""
Get lyrics from:

Anime Lyrics, AZLyrics, Genius, Lyricsmode, \
Lyrical Nonsense, Musixmatch, darklyrics
"""
import package_setup
import os
import lazy_import
import logging
from utils import module_path, we_are_frozen

# create formater
formatter = logging.Formatter("%(asctime)s - %(levelname)s \n\t - "
                              "pid = %(process)d \n\t - "
                              "proces name = %(processName)s \n\t - "
                              "module = %(module)s,"
                              "funcName = %(funcName)s \n\t - "
                              "%(message)s \n\t",
                              datefmt="%H:%M:%S")
# create logger
log = logging.getLogger(str(os.getpid()))
log.setLevel(logging.DEBUG)
# create file log
fh = logging.FileHandler(r"logs/wiki_music_lyrics_" +
                         str(os.getpid()) + ".log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)

if we_are_frozen() is False:
    log.propagate = False

log.info("starting imports")

from wiki_music import parser, exception
from utils import module_path

lyricsfinder = lazy_import.lazy_module("lyricsfinder")
re = lazy_import.lazy_module("re")
time = lazy_import.lazy_module("time")
Pool = lazy_import.lazy_callable("multiprocessing.Pool")
Fore = lazy_import.lazy_callable("colorama.Fore")
fuzz = lazy_import.lazy_callable("fuzzywuzzy.fuzz")
colorama_init = lazy_import.lazy_callable("utils.colorama_init")
normalize = lazy_import.lazy_callable("utils.normalize")

colorama_init()

log.info("imports done")

__all__ = ["save_lyrics", "get_lyrics"]


def save_lyrics():
    """
    Function is parallelized by use of multiprocessing.\n
    I have encountered strange problems with creating a\n
    shared Value or Array of strings. The problem is\n
    bypassed by using Manager().Value and putting those\n
    into list.
    """

    log.info("starting save lyrics")
    log.info("loading google api key")

    _file = os.path.join(module_path(), "files", "google_api_key.txt")
    try:
        f = open(_file, "r")
        google_api_key = f.read().strip()
    except Exception:
        raise Exception("You must input Google api key. Refer to repository "
                        "for instructions "
                        "https://github.com/marian-code/wikipedia-music-tags")
    else:
        log.info("Key loaded successfully")

    parser.lyrics = []
    for i, _ in enumerate(parser.tracks):
        if parser.types[i] == "Instrumental":
            parser.lyrics.append("Instrumental")
        elif parser.types[i] == "Orchestral":
            parser.lyrics.append("Orchestral")
        else:
            parser.lyrics.append(None)

    log.info("initialize duplicates")
    duplicates = [i for i in range(len(parser.lyrics))]

    for i, _ in enumerate(parser.lyrics):
        for j in range(i + 1, len(parser.lyrics)):
            if (fuzz.token_set_ratio(parser.tracks[i], parser.tracks[j]) >
                    90 and parser.lyrics[j] is None):
                duplicates[j] = i

    lyrics_temp = []

    if len(parser.tracks) > 1:

        t2 = time.time()
        arg = []
        # starmap takes list of tupples for argument
        for t in parser.tracks:
            arg.append((parser.band, parser.album, t, google_api_key))

        pool = Pool()
        lyrics_temp = pool.starmap(get_lyrics, arg)

        pool.close()
        pool.join()
        t3 = time.time()
        print("paralel part:", t3 - t2, "s")

    else:
        t2 = time.time()
        for i, tr in enumerate(parser.tracks):
            if i == duplicates[i]:
                lyrics_temp.append(get_lyrics(parser.band, parser.album,
                                              tr, google_api_key))

        t3 = time.time()
        print("serial part:", t3 - t2, "s")

    index = 0
    for i, _ in enumerate(parser.lyrics):
        if i == duplicates[i]:
            parser.lyrics[i] = lyrics_temp[index]
            index += 1

    for i, _ in enumerate(parser.lyrics):
        if parser.lyrics[i] is None:
            parser.lyrics[i] = parser.lyrics[duplicates[i]]


@exception(log)
def get_lyrics(artist: str, album: str, song: str, google_api_key) -> dict:

    log.info("starting lyricsfinder ")

    lyrics = next(lyricsfinder.search_lyrics(song, album, artist,
                                             google_api_key=google_api_key),
                  None)

    if not lyrics:
        return {
            "success": False,
            "error": "Couldn't find any lyrics for " + artist + " " + song
        }
    else:
        lyrics_data = lyrics.to_dict()
        lyrics_data["filename"] = lyrics.save_name
        lyrics_data["timestamp"] = time.time()
        
        print(Fore.GREEN + "Saved lyrics for: ",
              Fore.RESET, artist + " - " + song)
        log.info("Saved lyrics for " + "artist" + " - " + "song")

    log.info("lyrics to dict")

    lyrics = {
            "success": True,
            "title": lyrics_data["title"],
            "artist": lyrics_data["artist"],
            "release_date": lyrics_data["release_date"],
            # replace \n with \r\n if there is no \r in front of \n
            "lyrics": (normalize(lyrics_data["lyrics"]
                       .replace("\r", "").replace("\n", "\r\n"))),
            "origin": lyrics_data["origin"],
            "timestamp": lyrics_data["timestamp"]
        }

    log.info("done")

    return lyrics["lyrics"]

if __name__ == "__main__":

    # testing
    from pprint import pprint
    pprint(get_lyrics("arch enemy", "", "you will know my name"))
