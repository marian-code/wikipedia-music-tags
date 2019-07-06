"""Extractor for darklyrics.com."""

import logging
import re
from datetime import datetime

from lyricsfinder import Lyrics, NoLyrics
from lyricsfinder.extractor import LyricsExtractor
from lyricsfinder.utils import Request

log = logging.getLogger(__name__)


class Darklyrics(LyricsExtractor):
    """Class for extracting lyrics."""

    name = "Darklyrics"
    url = "http://www.darklyrics.com/"
    display_url = "darklyrics.com"

    @classmethod
    async def extract_lyrics(cls, request: Request) -> Lyrics:
        """Extract lyrics."""

        bs = await request.bs

        # get list of album tracks
        track_list = bs.find('div', class_='albumlyrics')
        if not track_list:
            raise NoLyrics
        track_list = track_list.text.split("\n")

        # remove empty entries from list
        track_list = list(filter(None, track_list))

        # convert to dict, delimiter is . or :
        for i in range(len(track_list)):
            track_list[i] = re.split("\.|:" ,track_list[i])

        # remove whitespaces
        d = {track[0]:track[1].strip() for track in track_list}
        
        # find release date
        for string in re.findall('\(.*?\)', d["album"]):
            string = re.sub(r"\(|\)", "", string)
            if string.isdigit():
                date_str = string
                break

        release_date = datetime.strptime(date_str, "%Y")

        # find the desired song
        for key, value in d.items():
            
            if request.song.lower() in value.lower():
                song_number = int(key)
                title = d[key]

        try:
            lyrics_div = bs.find('div', class_='lyrics')
            lyrics = lyrics_div.prettify().split('</h3>')  # split into separate lyrics
            lyric = cls.process_lyric(lyrics[song_number])
        except Exception as e:
            log.exception(e)

        return Lyrics(title, lyric, artist= request.artist.title(), release_date=release_date)

    @classmethod
    def process_lyric(cls, lyric):
        lyric = lyric[:lyric.find('<h3>')]  # remove tail
        # Set linebreaks
        lyric = lyric.replace('<br/>', '')
        # Remove italic
        lyric = lyric.replace('</i>', '')
        lyric = lyric.replace('<i>', '')
        # Remove trailing divs
        lyric = lyric.split('<div')[0]
        result = ''
        split_lyric = lyric.splitlines()
        for line_number in range(len(split_lyric) - 1):
            line = split_lyric[line_number].rstrip().strip()
            next_line = split_lyric[line_number + 1].rstrip()
            last_line = split_lyric[max(line_number - 1, 0)].rstrip()
            # Remove duplicate blank lines
            if line is not '' or (line is '' and next_line is '' and last_line is not ''):
                result = result + '\n' + line
        return result.strip()

