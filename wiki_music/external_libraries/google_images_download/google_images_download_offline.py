import logging
import os
from typing import List, NoReturn, Tuple

from PIL import Image

from wiki_music.constants.paths import ROOT_DIR  # pylint: disable=import-error

log = logging.getLogger(__name__)

log.info("Loaded Offline google images download")

class googleimagesdownload:

    def __init__(self) -> None:
        self.thumbs: List[bytearray] = []
        self.fullsize_url: List[str] = []
        self.fullsize_dim: List[Tuple[float, Tuple[int, int]]] = []
        self.count: int = 0
        self.finished: bool = False
        self._exit: bool = False

    def download(self, arguments: dict):

        dim: Tuple[int, int]
        disk_size: float

        print(f"\nItem no.: 1 --> Item name = {arguments['keywords']}")
        print("Evaluating...")

        files: List[str] = self.list_files()
        errorCount: int = 0

        for f in files:

            dim = Image.open(f).size
            disk_size = os.path.getsize(f)

            try:
                with open(f, "rb") as infile:
                    self.thumbs.append(bytearray(infile.read()))
                self.fullsize_dim.append((disk_size, dim))
                self.fullsize_url.append(f)
            except Exception as e:
                print(e)
                errorCount += 1
            else:
                self.count += 1
                print(f"Completed Image Thumbnail ====> {self.count}. {f}")

            if self._exit:
                print("Album art search exiting ...")

        print(f"\nErrors: {errorCount}\n")

        self.finished = True

    def close(self):
        self._exit = True

    def list_files(self) -> List[str]:

        folder: str = os.path.join(ROOT_DIR, "..", "tests", "offline_debug")

        return [os.path.join(folder, f.name) for f in os.scandir(folder)
                if f.is_file() and f.name.casefold().endswith(("jpg", "png"))]

    def get_max(self) -> int:
        return len(self.list_files())
