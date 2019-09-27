"""
Get lyrics from:

Anime Lyrics, AZLyrics, Genius, Lyricsmode, \
Lyrical Nonsense, Musixmatch, darklyrics
"""

from lazy_import import lazy_callable
from typing import Dict

from wiki_music.utilities import (exception, get_google_api_key, log_lyrics,
                                  normalize, we_are_frozen)
from wiki_music.constants.colors import GREEN, RESET

if not we_are_frozen():
    log_lyrics.propagate = False

Parallel = lazy_callable("joblib.Parallel")
delayed = lazy_callable("joblib.delayed")
fuzz = lazy_callable("fuzzywuzzy.fuzz")
LyricsManager = lazy_callable("external_libraries.lyricsfinder"
                              ".lyrics.LyricsManager")

GOOGLE_API_KEY = get_google_api_key()

log_lyrics.info("imports done")

__all__ = ["save_lyrics", "get_lyrics"]


def save_lyrics(parser):

    log_lyrics.info("starting save lyrics")

    parser.lyrics = []
    for i, tp in enumerate(parser.types):
        if tp == "Instrumental":
            parser.lyrics.append("Instrumental")
        elif tp == "Orchestral":
            parser.lyrics.append("Orchestral")
        else:
            parser.lyrics.append(None)

    log_lyrics.info("Initialize duplicates")

    tracks = dict()

    for i, (tr, lyr) in enumerate(zip(parser.tracks, parser.lyrics)):

        if lyr is None:
            for tr_k in tracks.keys():
                if fuzz.token_set_ratio(tr, tr_k) > 90:
                    tracks[tr_k]["track"].append(i)
                    break
            else:
                tracks[tr] = {"track": [i]}

    log_lyrics.info("Download lyrics")

    # run search
    lyrics = Parallel(n_jobs=len(parser), prefer="threads")(
        delayed(get_lyrics)(parser.band, parser.album, t)
        for t in tracks.keys())

    log_lyrics.info("Assign lyrics to tracks")

    # report results
    for i, l in enumerate(lyrics):
        if l["lyrics"]:
            print(GREEN + "Saved lyrics for:" + RESET,
                  f"{l['artist']} - {l['title']} " +
                  GREEN + f"({l['origin']['source_name']})")
            tracks[l["title"]]["lyrics"] = l["lyrics"]
        else:
            print(GREEN + "Couldn't find lyrics for:" +
                  RESET, f"{l['artist']} - {l['title']}")
            tracks[l["title"]]["lyrics"] = ""

    for track in tracks.values():
        for t in track["track"]:
            parser.lyrics[t] = track["lyrics"]


@exception(log_lyrics)
def get_lyrics(artist: str, album: str, song: str) -> Dict[str, str]:

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
        lyrics["title"] = song
        lyrics["lyrics"] = normalize(lyrics["lyrics"].replace("\r", "")
                                     .replace("\n", "\r\n"))

    return lyrics

