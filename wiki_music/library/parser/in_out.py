import os
import pickle  # lazy loaded
from abc import abstractmethod
from typing import Any, List

from wiki_music.constants.colors import GREEN, LBLUE, LGREEN, LYELLOW, RESET
from wiki_music.constants.tags import EXTENDED_TAGS
from wiki_music.utilities import (SharedVars, ThreadPool, bracket,
                                  count_spaces, list_files, log_parser,
                                  normalize_caseless, win_naming_convetion,
                                  write_roman, yaml_dump)

from ..ID3_tags import read_tags, write_tags
from ..lyrics import save_lyrics
from .base import ParserBase

wnc = win_naming_convetion
nc = normalize_caseless

log_parser.debug("in_out imports done")

__all__ = ["ParserInOut"]


class ParserInOut(ParserBase):
    formated_html: Any
    info_box_html: Any
    page: Any
    soup: Any

    def __init__(self, protected_vars):

        super().__init__(protected_vars=protected_vars)

        self._debug_folder: str = ""

    @abstractmethod
    def info_tracks(self):
        raise NotImplementedError("Call to abstract method")

    @property
    def bracketed_types(self) -> List[str]:  # type: ignore
        if not self._bracketed_types:
            self._bracketed_types = bracket(self.types)
            return self._bracketed_types
        else:
            return self._bracketed_types

    @property  # type: ignore
    def files(self) -> List[str]:  # type: ignore
        if len(self._files) < len(self.tracks):
            self.reassign_files()

        return self._files

    @files.setter
    def files(self, files: List[str]):
        self._files = files

    @property
    def debug_folder(self):
        if not self._debug_folder:
            _win_name = win_naming_convetion(self.album, dir_name=True)
            self._debug_folder = os.path.join("output", _win_name)

        return self._debug_folder

    def list_files(self):
        self.files = list_files(self.work_dir)

    def reassign_files(self):

        wnc = win_naming_convetion
        max_length = len(max(self.tracks, key=len))

        # write data to ID3 tags
        disk_files = list_files(self.work_dir)
        files = []

        print(GREEN + "\nFound files:")
        print(*disk_files, sep="\n")
        print(GREEN + "\nAssigning files to tracks:")

        for i, tr in enumerate(self.tracks):
            self.tracks[i] = tr.strip()

            for path in disk_files:
                f = os.path.split(path)[1]
                if (nc(wnc(tr)) in nc(f) and nc(self.types[i]) in nc(f)):  # noqa E129

                    print(LYELLOW + tr + RESET,
                          "-" * (1 + max_length - len(tr)) + ">", path)
                    files.append(path)
                    break
            else:
                print(LBLUE + tr + RESET, "." * (2 + max_length - len(tr)),
                      "Does not have a matching file!")

                files.append(None)

        self.files = files

    def basic_out(self):

        os.makedirs(self.debug_folder, exist_ok=True)

        # save page object for offline debbug
        fname = os.path.join(self.debug_folder, 'page.pkl')
        if not os.path.isfile(fname):
            with open(fname, 'wb') as f:
                pickle.dump(self.page, f, pickle.HIGHEST_PROTOCOL)

        # save formated html to file
        fname = os.path.join(self.debug_folder, 'page.html')
        if not os.path.isfile(fname):
            with open(fname, 'w', encoding='utf8') as f:
                f.write(self.soup.prettify())

        # save html converted to text
        fname = os.path.join(self.debug_folder, 'page.txt')
        if not os.path.isfile(fname):
            with open(fname, 'w', encoding='utf8') as f:
                f.write(self.formated_html)

    def disk_write(self):

        for i, tracklist in enumerate(self.tracklist_2_str(to_file=True), 1):
            fname = os.path.join(self.debug_folder, f"tracklist_{i}.txt")
            with open(fname, "w", encoding="utf-8") as f:
                f.write(tracklist)

        # save found personel to file
        with open(os.path.join(self.debug_folder, "personnel.txt"),
                  "w", encoding="utf8") as f:

            f.write(self.personnel_2_str())

    def tracklist_2_str(self, to_file=True) -> list:

        def _set_color():
            if to_file:
                return [""] * 3
            else:
                return GREEN, LGREEN, RESET

        # compute number of spaces
        spaces, length = count_spaces(self.tracks, self.bracketed_types)

        G, LG, R = _set_color()

        # convert to string
        tracklists = []
        for j, (ds, hd) in enumerate(zip(self.disks, self.header)):
            s = ""
            s += f"{G}\n{j + 1}. Disk:{R} {ds}"
            if len(hd) >= 2:
                s += f" {LG}{hd[0]} {hd[1]}"
            if len(hd) >= 3:
                s += f"{' '*(length + len(hd[1]))}{hd[2]}"
            if len(hd) >= 4:
                s += f", {hd[3]}"
            s += f"{R}\n"

            for i in range(self.disk_sep[j], self.disk_sep[j + 1]):
                s += (f"{self.numbers[i]:>2}. {self.tracks[i]} "
                      f"{self.bracketed_types[i]}{spaces[i]} "
                      f"{', '.join(self.artists[i] + self.composers[i])}\n")

                for k, (sbtr, sbtp) in enumerate(zip(self.subtracks[i],
                                                     self.sub_types[i])):
                    s += (f"  {write_roman(k + 1)}. {sbtr} {sbtp}\n")

            tracklists.append(s)

        return tracklists

    def print_tracklist(self):
        print("\n".join(self.tracklist_2_str(to_file=False)))

    def personnel_2_str(self):

        s = ""
        if not self.personnel:
            s += "---\n"

        for pers, app in zip(self.personnel, self.appearences):

            if app:
                s += pers + " - "
                temp = 50

                for k, a in enumerate(app):
                    for j, _ in enumerate(self.disk_sep[:-1]):

                        if (a > self.disk_sep[j] and
                            a < self.disk_sep[j + 1]):  # noqa E129

                            if j != temp:
                                s += f"{self.disks[j]}: {self.numbers[a]}"
                                temp = j
                            else:
                                s += self.numbers[a]

                            if k != len(app) - 1:
                                s += ", "
                            break
                    else:
                        continue

                s += u'\n'
            else:
                s += pers + u'\n'

        return s

    def data_to_dict(self) -> List[dict]:

        dict_data = []
        for i, _ in enumerate(self.tracks):

            tags = dict()

            for t in EXTENDED_TAGS:
                attr = getattr(self, t)
                if isinstance(attr, list):
                    tags[t] = attr[i]
                else:
                    tags[t] = attr

            dict_data.append(tags)

        if SharedVars.write_json:
            yaml_dump(dict_data, self.work_dir)
            print("Saved YAML file")

        return dict_data

    def write_tags(self, lyrics_only: bool=False) -> bool:

        if not any(self.files):
            return False
        else:
            # for data in self.data_to_dict():
            #     write_tags(data, lyrics_only=lyrics_only)

            ThreadPool(target=write_tags,
                       args=[(data, lyrics_only)
                              for data in self.data_to_dict()])

            """
            Parallel(n_jobs=len(self), prefer="threads")(
                delayed(write_tags)(data, lyrics_only=lyrics_only)
                for data in self.data_to_dict())
            """

            return True

    def save_lyrics(self):
        if SharedVars.write_lyrics:
            save_lyrics(self)
        else:
            self.lyrics = [""] * len(self)

    def read_files(self):

        # initialize variables
        self.__init__(protected_vars=False)

        self.list_files()

        for fl in self.files:

            for key, value in read_tags(fl).items():

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
            self.info_tracks()

            self.log.info("Files loaded sucesfully")
        else:
            self.album = ""
            self.band = ""
            self.selected_genre = ""
            self.release_date = ""

            self.log.info("No music files to Load")
