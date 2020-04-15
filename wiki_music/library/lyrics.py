r"""Get lyrics from.

Anime Lyrics, AZLyrics, Genius, Lyricsmode, \
Lyrical Nonsense, Musixmatch, darklyrics
"""

import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Union

import rapidfuzz.fuzz as fuzz  # lazy loaded

from wiki_music.constants import GREEN, NO_LYRIS, RESET
from wiki_music.external_libraries import lyricsfinder  # lazy loaded
from wiki_music.utilities import (GoogleApiKey, ThreadPool, caseless_equal,
                                  exception, normalize)

if TYPE_CHECKING:
    from wiki_music.external_libraries.lyricsfinder import LyricsManager
    from typing_extensions import TypedDict

    LyrData = TypedDict("LyrData", {"track": List[int], "lyrics": str})
    LyrDict = Dict[str, LyrData]
    from wiki_music.external_libraries.lyricsfinder.models.lyrics import (
        LyricsDict)


log = logging.getLogger(__name__)
log.debug("lyrics imports done")

__all__ = ["save_lyrics"]


def save_lyrics(tracks: List[str], types: List[str], band: str, album: str,
                GUI: bool, multi_threaded: bool) -> List[str]:
    """Searches and downloads lyrics for each track.

    Does some preprocessing before it starts the lyricsfinder
    module and downloads the lyrics. In preproces, tracks which will have same
    lyrics are identified so the same lyrics are not downloaded twice. The
    lyrics are then downloaded asynchronously each in separate thread for
    speed.

    See also
    --------
    :mod:`wiki_music.external_libraries.lyricsfinder`
         module used to download lyrics
    :class:`wiki_music.utilities.parser_utils.ThreadPool`
        async download

    Parameters
    ----------
    tracks: List[str]
        list of album tracks
    types: List[str]
        list of album types, to infer which tracks have same lyrics, e.g.
        <track> and <track (acoustic)> are considered to have same lyrics.
        Instrumental and Orchestral types are set to no lyrics
    band: str
        album artist name
    album: str
        album name
    GUI: bool
        whether app is running in GUI mode
    multi_threaded: bool
        whether to download lyrics in parallel of in orderely fasion

    Returns
    -------
    List[str]
        list of track lyrics in same order as tracks list was passed in
    """
    log.info("starting save lyrics")

    GOOGLE_API_KEY = GoogleApiKey.value(GUI)

    lyrics: List[str]
    tracks_dict: "LyrDict"
    raw_lyrics: List["LyricsDict"]

    lyrics = []
    for i, tp in enumerate(types):
        for nl in NO_LYRIS:
            if caseless_equal(nl, tp):
                lyrics.append(nl)
                break
        else:
            lyrics.append("")

    log.info("Initialize duplicates")

    tracks_dict = dict()

    for i, (tr, lyr) in enumerate(zip(tracks, lyrics)):

        if not lyr:
            for tr_k in tracks_dict.keys():
                if fuzz.token_set_ratio(tr, tr_k, score_cutoff=90):
                    tracks_dict[tr_k]["track"].append(i)
                    break
            else:
                tracks_dict[tr] = {"track": [i], "lyrics": ""}

    log.info("Download lyrics")

    # manager must be initialized in main thread
    manager = lyricsfinder.LyricsManager()

    # run search
    t = ThreadPool(target=_get_lyrics,
                   args=[(manager, band, album, t, GOOGLE_API_KEY)
                         for t in tracks_dict.keys()])
    if multi_threaded:
        raw_lyrics = t.run()
    else:
        raw_lyrics = t.run_serial()

    log.info("Assign lyrics to tracks_dict")

    # report results
    for i, l in enumerate(raw_lyrics):
        if l["lyrics"]:
            print(GREEN + "Saved lyrics for:" + RESET,
                  f"{l['artist']} - {l['title']} " + GREEN +
                  f"({l['origin']['source_name']})")
        else:
            print(GREEN + "Couldn't find lyrics for:" + RESET,
                  f"{l['artist']} - {l['title']}")

        tracks_dict[l["title"]]["lyrics"] = l["lyrics"]

    for track in tracks_dict.values():
        for t in track["track"]:
            lyrics[t] = track["lyrics"]

    return lyrics


@exception(log)
def _get_lyrics(manager: 'LyricsManager', artist: str, album: str, song: str,
                GOOGLE_API_KEY: str
                ) -> "LyricsDict":
    """Find and download lyrics for specified song.

    See also
    --------
    :meth:`wiki_music.external_libraries.lyricsfinder.LyricsManager`
        low level lyricsfinding implementation

    Parameters
    ----------
    manager: lyricsfinder.LyricsManager
        instance of LyricsManager which encapsulates the lyrics finding and
        downloading methods
    artist: str
        artist name
    album: str
        album name
    song: str
        song name

    Returns
    -------
    dict
        dictionary with lyrics and information where it was downloaded from
    """
    lyrics = next(manager.search_lyrics(song, album, artist,
                                        google_api_key=GOOGLE_API_KEY), None)

    if not lyrics:
        log.info(f"Couldn't find lyrics for: {artist} - {song}")
        return {"lyrics": "", "artist": artist, "title": song,
                "release_date": None, "origin": {"source_name": "",
                                                 "query": "", "url": "",
                                                 "source_url": ""}}
    else:
        log.info(f"Saved lyrics for: {artist} - {song}")
        response = lyrics.to_dict()
        response["title"] = song
        return response
