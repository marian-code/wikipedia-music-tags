"""Module with parser inpu-output methods."""

from itertools import product, filterfalse, combinations  # lazy loaded
import logging
import pickle  # lazy loaded
from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

import fuzzywuzzy.fuzz as fuzz  # lazy loaded
import fuzzywuzzy.process as process  # lazy loaded

from wiki_music.constants import (EXTENDED_TAGS, GREEN, LBLUE, LGREEN,
                                  OUTPUT_FOLDER, RESET, YELLOW)
from wiki_music.utilities import (ThreadPool, bracket, count_spaces,
                                  list_files, win_naming_convetion,
                                  write_roman, json_dump, lrange)

from ..lyrics import save_lyrics
from ..tags_io import read_tags, write_tags
from .base import ParserBase

log = logging.getLogger(__name__)

wnc = win_naming_convetion

if TYPE_CHECKING:
    from pathlib import Path
    from wikipedia import WikipediaPage
    from bs4 import BeautifulSoup

    Bs4Soup = Optional[BeautifulSoup]
    WikiPage = Optional[WikipediaPage]

    from typing_extensions import TypedDict

    SongDict = TypedDict("SongDict", {
        "ALBUM": str, "ALBUMARTIST": str, "ARTIST": List[str],
        "COMPOSER": List[str], "COVERART": bytes, "DATE": str,
        "DISCNUMBER": int, "GENRE": str, "LYRICS": str, "TITLE": str,
        "TRACKNUMBER": str, "TYPE": str, "FILE": str})
    SongList = List[SongDict]

__all__ = ["ParserInOut"]


class ParserInOut(ParserBase):
    """Encapsulates parser input and output methods.

    Class is inherited by
    :class:`wiki_music.library.parser.process_page.WikipediaParser`. Takes care
    of outputing and loading information.
    """

    _page: "WikiPage"
    _soup: "Bs4Soup"

    def __init__(self, protected_vars):

        super().__init__(protected_vars=protected_vars)

        self._debug_folder: "Path" = ""

    @abstractmethod
    def _info_tracks(self):
        raise NotImplementedError("Call to abstract method")

    @property
    def bracketed_types(self) -> List[str]:  # type: ignore
        """Takes `_bracketed_types` list, populates and returns it.

        See also
        --------
        :func:`wiki_music.utilities.parser_utils.bracket`
            function used to append brackets at the ends of strings in list

        :type: List[str]
        """
        if not self._bracketed_types:
            self._bracketed_types = bracket(self._types)

        return self._bracketed_types

    @property  # type: ignore
    def files(self) -> List[Path]:  # type: ignore
        """Gets list of music files in currently set working directory.

        :type: List[Path]

        See also
        --------
        :meth:`_reassign_files`

        """
        if len(self._files) < len(self._tracks) or not self._files:
            self._reassign_files()

        return self._files

    @files.setter
    def files(self, files: List[Path]):
        self._files = files

    @property
    def debug_folder(self) -> "Path":
        """Path to debugging folder.

        :type: str
        """
        if not self._debug_folder:
            _win_name = win_naming_convetion(self._album, dir_name=True)
            self._debug_folder = OUTPUT_FOLDER / _win_name
            self._debug_folder.mkdir(parents=True, exist_ok=True)

        return self._debug_folder

    def _reassign_files(self):
        """Search current working directory and assign files to tracks."""

        # TODO untested !!!!
        class FilesList(list):

            def get(self, key: str) -> Union[str, int]:
                """Always return the first element."""
                return self[0][key]

        class FifoList(list):

            def __init__(self, work_dir: Path) -> None:
                super().__init__()
                self.work_dir = work_dir

            def put(self, scored_files: List[Tuple[str, int]]):
                """Convert list of tuples to list of dicts and append."""
                self.append(FilesList([{"file": self.work_dir / s[0],
                                        "score": s[1]}
                                       for s in scored_files]))

        disk_files = list_files(self.work_dir)

        if not self._tracks:
            self.files = disk_files
            return

        # max() argument must have len >= 1
        max_length = len(max(self._tracks, key=len))

        files = []

        print(GREEN + "\nFound files:")
        for df in disk_files:
            print(df.resolve())
        print(GREEN + "\nAssigning files to tracks:")

        # TODO untested !!!!
        # new file assignment
        file_map = FifoList(self.work_dir)
        limit = int(len(disk_files) / 2)
        for tr, tp in zip(self._tracks, self._types):
            # for each track select best matching files
            file_map.put(process.extractBests(wnc(f"{tr} {tp}"),
                                              [f.name for f in disk_files],
                                              scorer=fuzz.token_set_ratio,
                                              limit=limit))

        # ! does not work deletes all matches fromn file map
        # if there are more tracks than files
        len_diff = len(disk_files) - len(self._tracks)
        if len_diff < 0:
            indices = [i for i in lrange(file_map)]
            print(indices)
            # sort indices based on first file score
            indices = [i for i, _ in sorted(zip(indices, file_map),
                                            key=lambda x: x[1].get("score"))]
            print(indices)
            # keep only number of best indices coresponding to number of
            # tracks
            indices = indices[:len_diff]
            print(indices)

            # keep the best matching files, reassign the rest to None
            for i in lrange(file_map):
                if i not in indices:
                    file_map[i] = {"file": None, "score": 0}

        print("-----------------------------------")
        print(file_map)

        # if lengths are equal but two tacks have same files
        for i, j in combinations(lrange(file_map), 2):

            # if None file is assigned skip iteration
            if not file_map[i].get("file") or not file_map[j].get("file"):
                continue

            # if files are equal, keep one with the higher score,
            # and reassign the one with lower score to next in its
            # respective list
            elif file_map[i].get("file") == file_map[j].get("file"):
                if file_map[i].get("score") > file_map[j].get("score"):
                    file_map[j].pop(0)
                elif file_map[i].get("score") < file_map[j].get("score"):
                    file_map[i].pop(0)
                else:
                    log.debug(f"i: {i}, j:{j}")
                    log.debug(wnc(f"{self._tracks[j]} {self._types[j]}"))
                    f = lambda x: f"{str(x['file']):100}:{x['score']:3}"
                    for f1, f2 in zip(file_map[i], file_map[j]):
                        print(f"{f(f1)} | {f(f2)}")
                    raise Exception(f"File mapping to tracks is "
                                    f"ambiguous! Cannot load files")

        # print out file assignments
        for tr, f in zip(self._tracks, file_map):

            if f.get("file"):
                print(LBLUE + tr + RESET,
                      "-" * (1 + max_length - len(tr)) + ">", f.get("file"))
                files.append(f.get("file"))
            else:
                print(YELLOW + tr + RESET, "." * (2 + max_length - len(tr)),
                      "Does not have a matching file!")
                files.append(None)

        self.files = files

    def basic_out(self):
        """Outputs files in three basic formats.

        1. pickled version of the downloaded wikipedia page
        2. nicely formated html version of the wikipedia page
        3. plain text version of the wikipedia page
        """
        # ensure directory for results storing exists
        self.debug_folder.mkdir(parents=True, exist_ok=True)

        # save page object for offline debbug
        fname = self.debug_folder / 'page.pkl'
        with fname.open('wb') as f:
            pickle.dump(self._page, f)

        # save formated html to file
        fname = self.debug_folder / 'page.html'
        fname.write_text(self._soup.prettify(), encoding='utf8')

        # save html converted to text
        fname = self.debug_folder / 'page.txt'
        fname.write_text(self._soup.get_text(), encoding='utf8')

    def disk_write(self):
        """Save tracklist and personnel to disk in plain text format."""
        # save tracklist to file
        for i, tracklist in enumerate(self.tracklist_2_str(to_file=True), 1):
            fname = self.debug_folder / f"tracklist_{i}.txt"
            fname.write_text(tracklist, encoding="utf-8")

        # save found personel to file
        fname = self.debug_folder / "personnel.txt"
        fname.write_text(self.personnel_2_str(), encoding="utf8")

    def tracklist_2_str(self, to_file=True) -> list:
        """Convert tracklist to string to print out or write to disk.

        Parameters
        ----------
        to_file: bool
            if False and the tracklist is to be printed to console, highlight
            headers to make tracklist more readable

        Returns
        -------
        str
            nicely formated string representation of tracklist
        """
        def _set_color():
            if to_file:
                return [""] * 3
            else:
                return GREEN, LGREEN, RESET

        # compute number of spaces, wrong mypy detection
        spaces, length = count_spaces(self._tracks, self.bracketed_types)

        G, LG, R = _set_color()

        # convert to string
        tracklists = []
        for j, (ds, hd) in enumerate(zip(self._disks, self._header)):
            s = ""
            s += f"{G}\n{j + 1}. Disk:{R} {ds}"
            if len(hd) >= 2:
                s += f" {LG}{hd[0]} {hd[1]}"
            if len(hd) >= 3:
                s += f"{' '*(length + len(hd[1]))}{hd[2]}"
            if len(hd) >= 4:
                s += f", {hd[3]}"
            s += f"{R}\n"

            for i in range(self._disk_sep[j], self._disk_sep[j + 1]):
                s += (f"{self._numbers[i]:>2}. {self._tracks[i]} "
                      f"{self.bracketed_types[i]}{spaces[i]} "
                      f"{', '.join(self._artists[i] + self._composers[i])}\n")

                for k, (sbtr, sbtp) in enumerate(
                        zip(self._subtracks[i], self._subtypes[i])):
                    s += (f"  {write_roman(k + 1)}. {sbtr} {sbtp}\n")

            tracklists.append(s)

        return tracklists

    def print_tracklist(self):
        """Prints tracklist to console.

        See also
        --------
        :func:`tracklist_2_str`
        """
        print("\n".join(self.tracklist_2_str(to_file=False)))

    def personnel_2_str(self):
        """Convert album personnel to string to print out or write to disk.

        Returns
        -------
        str
            nicely formated string representation of personnel
        """
        s = ""
        if not self._personnel:
            s += "---\n"

        for pers, app in filterfalse(lambda x: not bool(x[1]),
                                     zip(self._personnel, self._appearences)):

            s += pers + " - "
            temp = 1000

            for (k, a), j in product(enumerate(sorted(app)),
                                     lrange(self._disk_sep[:-1])):

                if (a >= self._disk_sep[j] and a < self._disk_sep[j + 1]):

                    if j != temp:
                        s += f"{self._disks[j]}: {self._numbers[a]}"
                        temp = j
                    else:
                        s += self._numbers[a]

                    if k != len(app) - 1:
                        s += ", "
                    break

                s += u'\n'
            else:
                s += pers + u'\n'

        return s

    def data_to_dict(self, indices: List[int]) -> "SongList":
        """Converts parser data to list of dictionaries.

        If json_dump is enabled list is written to file.

        Parameters
        ----------
        indices: List[int]
            indices of files to save

        See also
        --------
        :const:`wiki_music.constants.tags.EXTENDED_TAGS`
            list of tags that are written to each dictionary

        Returns
        -------
        List[Dict[str, Union[str, int, bytes, list]]]
            each dictionary in list represents tags of one song
        """
        dict_data: SongList = []
        for i, _ in enumerate(self._tracks):

            tags: "SongDict" = dict()

            if i not in indices:
                continue

            for t in EXTENDED_TAGS:
                attr = getattr(self, t)
                if isinstance(attr, list):
                    tags[t] = attr[i]
                else:
                    tags[t] = attr

            dict_data.append(tags)

        if self.write_json:
            json_dump(dict_data, self.work_dir)
            print("Saved json file")

        return dict_data

    def write_tags(self, indices: List[int]) -> bool:
        """Write tags to coresponding files. Writing is done in a parallel.

        Parameters
        ----------
        indices: List[int]
            indices of files to save

        See also
        --------
        :func:`wiki_music.library.tags_io.write_tags`
            function that handles tag writing
        :meth:`data_to_dict`
            this method prepares tags data in suitable format for writing
        :func:`wiki_music.utilities.parser_utils.ThreadPool`
            class that handles paralelism

        Returns
        -------
        bool
            If writing was successfull return true value
        """
        if not any(self.files):
            return False
        else:
            t = ThreadPool(target=write_tags,
                           args=[(d, ) for d in self.data_to_dict(indices)])
            if self.multi_threaded:
                t.run()
            else:
                t.run_serial()

            return True

    def save_lyrics(self, find: bool = True):
        """Calls lyricsfinder to search for and save lyrics for all tracks.

        Parameters
        ----------
        find: bool
            if False lyrics list is initialized only with empty strings

        See also
        --------
        :func:`wiki_music.library.lyrics.save_lyrics`
            function that handles lyrics finding and saving
        """
        if find:
            self._lyrics = save_lyrics(self._tracks, self._types, self._band,
                                       self._album, self._GUI,
                                       self.multi_threaded)
        else:
            self._lyrics = [""] * len(self)

    def read_files(self):
        """Read tags from files in working directory.

        See also
        --------
        :func:`wiki_music.library.tags_io.read_tags`
            function that thandles tag reading
        """
        # initialize variables
        self.reinit(protected_vars=False)

        t = ThreadPool(read_tags, [(f, ) for f in self.files])

        # read tags
        for tag in t.run(serial=not self.multi_threaded):

            for key, value in tag.items():

                # TODO need more elegant way to avoid this difference
                # between read tags and parser attributes
                if key == "COMMENT":
                    continue

                if isinstance(getattr(self, key), list):
                    getattr(self, key).append(value)
                else:
                    setattr(self, key, value)

        if self.files:
            # look for aditional artists in brackets behind track names and
            # complete artists names again with new info
            self._info_tracks()

            self._log.info("Files loaded sucesfully")
        else:
            self._album = ""
            self._band = ""
            self._selected_genre = ""
            self._release_date = ""

            self._log.info("No music files to Load")
