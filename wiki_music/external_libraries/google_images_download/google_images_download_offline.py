import logging
import os
from typing import List, NoReturn, Tuple

from PIL import Image

from wiki_music.constants.paths import OFFLINE_DEBUG_IMAGES  # pylint: disable=import-error
from wiki_music.utilities.utils import list_files

log = logging.getLogger(__name__)

log.info("Loaded Offline google images download")

class googleimagesdownload:
    """ Offline version imitating google images download. Main puprose is
    offline testing.

    Attributes
    ----------
    thumbs: List[bytearray]
        list of dowloaded coverart thumbnails read in memory as bytearrays
    fullsize_url: List[str]
        list of urls pointing to fullsize pictures
    fullsize_dim: List[Tuple[float, Tuple[int, int]]]
        list of tuples containing size of image in Kb and dimensions
    count: int
        actual number of downloaded pictures
    finished: bool
        anounce finished downloading
    """

    def __init__(self) -> None:
        self.thumbs: List[bytearray] = []
        self.fullsize_url: List[str] = []
        self.fullsize_dim: List[Tuple[float, Tuple[int, int]]] = []
        self.count: int = 0
        self.finished: bool = False
        self._exit: bool = False

    def download(self, arguments: dict):
        """ Start reding images from files.

        Parameters
        ----------
        arguments: dict
            dictionary of arguments, essentialy it is not needed. It is
            included only to maintain simillarity with original version API
        """

        dim: Tuple[int, int]
        disk_size: float

        print(f"\nItem no.: 1 --> Item name = {arguments['keywords']}")
        print("Evaluating...")

        files: List[str] = list_files(OFFLINE_DEBUG_IMAGES, file_type="image",
                                      recurse=True)
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
        """ Stop downloading images. """

        self._exit = True

    def get_max(self) -> int:
        """ Returns maximum number of loadable images. Needed to set progresbar
        in GUI

        See also
        --------
        :func:`wiki_music.utilities.utils.list_files`
            to see list of suported files

        Returns
        -------
        int
            number of image files
        """
        return len(list_files(OFFLINE_DEBUG_IMAGES, file_type="image",
                              recurse=True))
