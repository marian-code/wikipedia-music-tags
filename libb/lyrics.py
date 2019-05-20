"""
Get lyrics from:

Anime Lyrics, AZLyrics, Genius, Lyricsmode, \
Lyrical Nonsense, Musixmatch, darklyrics
"""
import package_setup
from lazy_import import lazy_callable, lazy_module
from utils import we_are_frozen
from wiki_music import log_lyrics, parser, exception, google_api_key

if not we_are_frozen():
    log_lyrics.propagate = False

lyricsfinder = lazy_module("lyricsfinder")
Pool = lazy_callable("multiprocessing.Pool")
Fore = lazy_callable("colorama.Fore")
fuzz = lazy_callable("fuzzywuzzy.fuzz")
colorama_init = lazy_callable("utils.colorama_init")
normalize = lazy_callable("utils.normalize")

colorama_init()

log_lyrics.info("imports done")

__all__ = ["save_lyrics", "get_lyrics"]


def save_lyrics():

    log_lyrics.info("starting save lyrics")

    parser.lyrics = []
    for i, _ in enumerate(parser.tracks):
        if parser.types[i] == "Instrumental":
            parser.lyrics.append("Instrumental")
        elif parser.types[i] == "Orchestral":
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

    lyrics_temp = []

    if len(parser.tracks) > 1:

        arg = []
        # starmap takes list of tupples for argument
        for t in parser.tracks:
            arg.append((parser.band, parser.album, t, google_api_key))

        pool = Pool()
        lyrics_temp = pool.starmap(get_lyrics, arg)

        pool.close()
        pool.join()

    else:
        for i, (tr, dp) in enumerate(zip(parser.tracks, duplicates)):
            if i == dp:
                lyrics_temp.append(get_lyrics(parser.band, parser.album,
                                              tr, google_api_key))

    index = 0
    for i, dp in enumerate(duplicates):
        if i == dp:
            parser.lyrics[i] = lyrics_temp[index]
            index += 1

    for i, (pl, dp) in enumerate(zip(parser.lyrics, duplicates)):
        if pl is None:
            parser.lyrics[i] = parser.lyrics[dp]


@exception(log_lyrics)
def get_lyrics(artist: str, album: str, song: str, google_api_key) -> dict:

    log_lyrics.info("starting lyricsfinder ")

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

        print(Fore.GREEN + "Saved lyrics for: ",
              Fore.RESET, artist + " - " + song)
        log_lyrics.info("Saved lyrics for " + "artist" + " - " + "song")

    log_lyrics.info("lyrics to dict")

    lyrics = {
            "success": True,
            "title": lyrics_data["title"],
            "artist": lyrics_data["artist"],
            "release_date": lyrics_data["release_date"],
            # replace \n with \r\n if there is no \r in front of \n
            "lyrics": (normalize(lyrics_data["lyrics"]
                       .replace("\r", "").replace("\n", "\r\n"))),
            "origin": lyrics_data["origin"]
        }

    log_lyrics.info("done")

    return lyrics["lyrics"]

if __name__ == "__main__":

    # testing
    from pprint import pprint
    pprint(get_lyrics("arch enemy", "", "you will know my name",
                      "<google_api_key>"))
