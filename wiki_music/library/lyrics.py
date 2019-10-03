"""
Get lyrics from:

Anime Lyrics, AZLyrics, Genius, Lyricsmode, \
Lyrical Nonsense, Musixmatch, darklyrics
"""

import logging
from typing import Dict, Optional

import fuzzywuzzy.fuzz as fuzz  # lazy loaded

from wiki_music.constants.colors import GREEN, RESET
from wiki_music.external_libraries import lyricsfinder  # lazy loaded
from wiki_music.utilities import (ThreadPool, exception, get_google_api_key,
                                  log_lyrics, normalize, we_are_frozen)

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

    # manager must be initialized in main thread
    manager = lyricsfinder.LyricsManager()

    # adjust logging level for frozen app
    if we_are_frozen():
        name = "wiki_music.external_libraries.lyricsfinder.lyrics"
        logging.getLogger(name).setLevel("ERROR")

    # run search
    lyrics = ThreadPool(target=get_lyrics,
                        args=[(manager, parser.band, parser.album, t)
                               for t in tracks.keys()]).run()

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
def get_lyrics(manager, artist: str, album: str, song: str
              ) -> Dict[str, Optional[str]]:

    lyrics = next(manager.search_lyrics(song, album, artist,
                  google_api_key=GOOGLE_API_KEY), None)

    if not lyrics:
        log_lyrics.info(f"Couldn't find lyrics for: {artist} - {song}")
        return {"lyrics": None, "artist": artist, "title": song}
    else:
        log_lyrics.info(f"Saved lyrics for: {artist} - {song}")
        l = lyrics.to_dict()
        l["title"] = song
        l["lyrics"] = normalize(l["lyrics"].replace("\r", "").replace("\n", "\r\n"))

        return l
