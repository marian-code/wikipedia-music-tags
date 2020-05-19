import logging
import sys
from copy import deepcopy
from pathlib import Path
from random import seed, shuffle
from unittest import TestCase, main, mock

from wiki_music.library.parser import in_out

logging.basicConfig(stream=sys.stderr)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

seed(1)


class TestFileAssignment(TestCase):

    def setUp(self):

        self.tests_path = Path("file_assignment")
        self.parser = in_out.ParserInOut(protected_vars=True)
        self.file_sets = dict()
        for tp in self.tests_path.rglob("*"):
            if tp.is_dir():
                self.file_sets[tp] = [d for d in tp.rglob("*") if d.is_dir()]

        self.mock_this = "wiki_music.library.parser.in_out.list_files"

    def test_simple_assign(self):
        for band, albums in self.file_sets.items():
            for album in albums:

                wd = Path(self.tests_path) / band.name / album.name
                check_file = (wd / "mapping.txt").read_text().splitlines()

                tracks = [c.split("::")[0] for c in check_file]
                files = [wd / c.split("::")[1] for c in check_file]

                log.debug(tracks)
                log.debug(files)

                shuffle_files = deepcopy(files)
                shuffle(shuffle_files)

                with mock.patch(self.mock_this, return_value=shuffle_files):

                    self.parser.work_dir = wd
                    self.parser._tracks = tracks
                    self.parser._types = [""] * len(tracks)

                    self.assertSequenceEqual(files, self.parser.files,
                                             f"test failed for:"
                                             f" {band.name} - {album.name}")
                
    # tap into list_files function in utils and change its behaviour
    def test_more_files(self):
        for band, albums in self.file_sets.items():
            for album in albums:

                wd = Path(self.tests_path) / band.name / album.name
                check_file = (wd / "mapping.txt").read_text().splitlines()

                tracks = [c.split("::")[0] for c in check_file]
                files = [wd / c.split("::")[1] for c in check_file]

                log.debug("test more files")
                log.debug(tracks)
                log.debug(files)

                shuffle_files = deepcopy(files)
                shuffle_files.extend(shuffle_files)
                shuffle(shuffle_files)

                with mock.patch(self.mock_this, return_value=shuffle_files):

                    self.parser.work_dir = wd
                    self.parser._tracks = tracks
                    self.parser._types = [""] * len(tracks)

                    self.assertSequenceEqual(files, self.parser.files,
                                             f"test failed for:"
                                             f" {band.name} - {album.name}")

    def test_less_files(self):
        for band, albums in self.file_sets.items():
            for album in albums:

                wd = Path(self.tests_path) / band.name / album.name
                check_file = (wd / "mapping.txt").read_text().splitlines()

                tracks = [c.split("::")[0] for c in check_file]
                files = [wd / c.split("::")[1] for c in check_file]
                shuffle(files)

                log.debug("test less files")
                log.debug(tracks)
                log.debug(files)

                half = int(len(files) / 2)

                shuffle_files = deepcopy(files)
                shuffle_files = shuffle_files[:half]
                shuffle(shuffle_files)

                with mock.patch(self.mock_this, return_value=files):

                    self.parser.work_dir = wd
                    self.parser._tracks = tracks
                    self.parser._types = [""] * len(tracks)

                    files = files + [None] * half
                    self.assertSequenceEqual(files, self.parser.files,
                                             f"test failed for:"
                                             f" {band.name} - {album.name}")

if __name__ == '__main__':
    main()
