"""Extractor for darklyrics.com."""

import logging
import re
from datetime import datetime

from ..extractor import LyricsExtractor
from ..models.lyrics import Lyrics
from ..models import exceptions

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

        if not track_list:
            raise exceptions.NoLyrics

        # get table header
        header = track_list.find("h2").text

        # get tracklist
        track_list = track_list.find_all("a", href=re.compile(r"#"))
        track_list = [t.text for t in track_list]

        # convert to dict, delimiter is . or :
        for i, t in enumerate(track_list):
            track_list[i] = re.split(r"\.|:", t)

        # remove whitespaces
        track_list = {t[0]: t[1].strip() for t in track_list}

        # find release date
        for string in re.findall(r'\(.*?\)', header):
            string = re.sub(r"\(|\)", "", string)
            if string.isdigit():
                date_str = string
                break
        else:
            date_str = "9999"

        release_date = datetime.strptime(date_str, "%Y")

        # find the desired song
        for key, value in track_list.items():

            if song.lower() in value.lower():
                song_number = int(key)
                title = track_list[key]

        try:
            lyrics_div = bs.find('div', class_='lyrics')
            # split into separate lyrics
            lyrics = lyrics_div.prettify().split('</h3>')
            lyric = cls.process_lyric(lyrics[song_number])
        except Exception as e:
            log.exception(e)

        if not lyric.strip():
            raise exceptions.NoLyrics

        return Lyrics(title, lyric, artist=artist.title(),
                      release_date=release_date)

    @classmethod
    def process_lyric(cls, lyric):
        """Process and format lyrics."""
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
            if line is not '' or (line is '' and next_line is '' and
                                  last_line is not ''):
                result = result + '\n' + line
        return result.strip()
