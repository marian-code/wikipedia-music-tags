"""Extractor for darklyrics.com."""

import logging
import re
from datetime import datetime

from ..extractor import LyricsExtractor
from ..models.lyrics import Lyrics

log = logging.getLogger(__name__)


class Darklyrics(LyricsExtractor):
    """Class for extracting lyrics."""

    name = "Darklyrics"
    url = "http://www.darklyrics.com/"
    display_url = "darklyrics.com"

    @classmethod
    def extract_lyrics(cls, url_data, song, artist):
        """Extract lyrics."""

        bs = url_data.bs

        # get list of album tracks
        track_list = bs.find('div', class_='albumlyrics')
        track_list = track_list.text.split("\n")

        # remove empty entries from list
        track_list = list(filter(None, track_list))

        # convert to dict, delimiter is . or :
        for i in range(len(track_list)):
            track_list[i] = re.split("\.|:" ,track_list[i])

        # remove whitespaces
        dict = {track[0]:track[1].strip() for track in track_list}
        
        # find release date
        for string in re.findall('\(.*?\)', dict["album"]):
            string = re.sub(r"\(|\)", "", string)
            if string.isdigit():
                date_str = string
                break

        release_date = datetime.strptime(date_str, "%Y")

        # find the desired song
        for key, value in dict.items():
            
            if song.lower() in value.lower():
                song_number = int(key)
                title = dict[key]

        try:
            lyrics_div = bs.find('div', class_='lyrics')
            lyrics = lyrics_div.prettify().split('</h3>')  # split into separate lyrics
            lyric = cls.process_lyric(cls, lyrics[song_number])
        except Exception as e:
            log.exception(e)

        return Lyrics(title, lyric, artist= artist.title(), release_date=release_date)

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

