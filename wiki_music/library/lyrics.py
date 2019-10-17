"""
Get lyrics from:

Anime Lyrics, AZLyrics, Genius, Lyricsmode, \
Lyrical Nonsense, Musixmatch, darklyrics
"""

import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Union

import fuzzywuzzy.fuzz as fuzz  # lazy loaded

from wiki_music.constants import GREEN, NO_LYRIS, RESET
from wiki_music.external_libraries import lyricsfinder  # lazy loaded
from wiki_music.utilities import (SharedVars, ThreadPool, caseless_equal,
                                  exception, normalize, read_google_api_key,
                                  we_are_frozen)

if TYPE_CHECKING:
    from wiki_music.external_libraries.lyricsfinder import LyricsManager

log = logging.getLogger(__name__)
log.debug("lyrics imports done")

__all__ = ["save_lyrics"]


def save_lyrics(tracks: List[str], types: List[str], band: str, album: str,
                GUI: bool) -> List[str]:
    """This function does some preprocessing before it starts the lyricsfinder
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

    Returns
    -------
    List[str]
        list of track lyrics in same order as tracks list was passed in
    """

    GOOGLE_API_KEY = read_google_api_key(GUI)

    log.info("starting save lyrics")

    lyrics: List[str]
    tracks_dict: Dict[str, Dict[str, Union[str, list]]]
    raw_lyrics: List[Dict[str, Optional[str]]]

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
                if fuzz.token_set_ratio(tr, tr_k) > 90:
                    tracks_dict[tr_k]["track"].append(i)
                    break
            else:
                tracks_dict[tr] = {"track": [i]}

    log.info("Download lyrics")

    # manager must be initialized in main thread
    manager = lyricsfinder.LyricsManager()

    # adjust logging level for frozen app
    if we_are_frozen():
        name = "wiki_music.external_libraries.lyricsfinder.lyrics"
        logging.getLogger(name).setLevel("ERROR")

    # run search
    raw_lyrics = ThreadPool(target=_get_lyrics,
                            args=[(manager, band, album, t, GOOGLE_API_KEY)
                                  for t in tracks_dict.keys()]).run()

    log.info("Assign lyrics to tracks_dict")

    # report results
    for i, l in enumerate(raw_lyrics):
        if l["lyrics"]:
            print(GREEN + "Saved lyrics for:" + RESET,
                  f"{l['artist']} - {l['title']} " + GREEN +
                  f"({l['origin']['source_name']})")
            tracks_dict[l["title"]]["lyrics"] = l["lyrics"]
        else:
            print(GREEN + "Couldn't find lyrics for:" + RESET,
                  f"{l['artist']} - {l['title']}")
            tracks_dict[l["title"]]["lyrics"] = ""

    for track in tracks_dict.values():
        for t in track["track"]:
            lyrics[t] = track["lyrics"]

    return lyrics


@exception(log)
def _get_lyrics(manager: 'LyricsManager', artist: str, album: str, song: str,
                GOOGLE_API_KEY: str
                ) -> Dict[str, Optional[Union[str, Dict[str, str]]]]:
    """Function which calls lyricsfinder.LyricsManager.search_lyrics method
    to find and download lyrics for specified song.

    See also
    --------
    :meth:`wiki_music.external_libraries.lyricsfinder.LyricsManager`

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

    lyrics = next(
        manager.search_lyrics(song,
                              album,
                              artist,
                              google_api_key=GOOGLE_API_KEY), None)

    if not lyrics:
        log.info(f"Couldn't find lyrics for: {artist} - {song}")
        return {"lyrics": None, "artist": artist, "title": song}
    else:
        log.info(f"Saved lyrics for: {artist} - {song}")
        l = lyrics.to_dict()
        l["title"] = song
        l["lyrics"] = normalize(l["lyrics"].replace("\r",
                                                    "").replace("\n", "\r\n"))

        return l
