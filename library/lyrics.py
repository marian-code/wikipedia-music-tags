"""
Get lyrics from:

Anime Lyrics, AZLyrics, Genius, Lyricsmode, \
Lyrical Nonsense, Musixmatch, darklyrics
"""

from lazy_import import lazy_callable
from utilities.utils import we_are_frozen, get_google_api_key
from utilities.loggers import log_lyrics
from utilities.wrappers import exception

if not we_are_frozen():
    log_lyrics.propagate = False

Parallel = lazy_callable("joblib.Parallel")
delayed = lazy_callable("joblib.delayed")
Fore = lazy_callable("colorama.Fore")
fuzz = lazy_callable("fuzzywuzzy.fuzz")
colorama_init = lazy_callable("utilities.utils.colorama_init")
normalize = lazy_callable("utilities.utils.normalize")
LyricsManager = lazy_callable("external_libraries.lyricsfinder"
                              ".lyrics.LyricsManager")

GOOGLE_API_KEY = get_google_api_key()
colorama_init(autoreset=True)

log_lyrics.info("imports done")

__all__ = ["save_lyrics", "get_lyrics"]


def save_lyrics(parser):

    log_lyrics.info("starting save lyrics")

    parser.lyrics = []
    for i, typ in enumerate(parser.types):
        if typ == "Instrumental":
            parser.lyrics.append("Instrumental")
        elif typ == "Orchestral":
            parser.lyrics.append("Orchestral")
        else:
            parser.lyrics.append(None)

    log_lyrics.info("initialize duplicates")
    duplicates = [i for i, _ in enumerate(parser.lyrics)]

    for i, _ in enumerate(parser.lyrics):
        for j in range(i + 1, len(parser.lyrics)):
            if (fuzz.token_set_ratio(parser.tracks[i], parser.tracks[j]) >
                    90 and parser.lyrics[j] is None):
                duplicates[j] = i

    # run search
    lyrics_temp = Parallel(n_jobs=len(parser), prefer="threads")(
        delayed(get_lyrics)(parser.band, parser.album, t)
        for t in parser.tracks)

    # report results
    for i, l in enumerate(lyrics_temp):
        if l["lyrics"]:
            print(Fore.GREEN + "Saved lyrics for:" + Fore.RESET,
                  f"{l['artist']} - {l['title']} " +
                  Fore.GREEN + f"({l['origin']['source_name']})")
            lyrics_temp[i] = l["lyrics"]
        else:
            print(Fore.GREEN + "Couldn't find lyrics for:" +
                  Fore.RESET, f"{l['artist']} - {l['title']}")

    index = 0
    for i, dp in enumerate(duplicates):
        if i == dp:
            parser.lyrics[i] = lyrics_temp[index]
            index += 1

    for i, (pl, dp) in enumerate(zip(parser.lyrics, duplicates)):
        if pl is None:
            parser.lyrics[i] = parser.lyrics[dp]


@exception(log_lyrics)
def get_lyrics(artist: str, album: str, song: str) -> dict:

    log_lyrics.info("starting lyricsfinder ")

    l = LyricsManager()

    lyrics = next(l.search_lyrics(song, album, artist,
                                  google_api_key=GOOGLE_API_KEY), None)

    if lyrics is None:
        log_lyrics.info(f"Couldn't find lyrics for: {artist} - {song}")
        lyrics = {"lyrics": None, "artist": artist, "title": song}
    else:
        log_lyrics.info(f"Saved lyrics for: {artist} - {song}")
        lyrics = lyrics.to_dict()
        lyrics["lyrics"] = normalize(lyrics["lyrics"].replace("\r", "").replace("\n", "\r\n"))    

    return lyrics

if __name__ == "__main__":

    # testing
    from pprint import pprint
    pprint(get_lyrics("Swallow The Sun",
                      "When a Shadow is Forced Into the Light",
                      "When a Shadow Is Forced into the Light",
                      GOOGLE_API_KEY))
