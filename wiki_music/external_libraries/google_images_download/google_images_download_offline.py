"""Offline version of googleimages download for debugging."""

import logging
import queue
from typing import Dict, List, NoReturn, Tuple, TYPE_CHECKING, TypeVar

from PIL import Image

from wiki_music.constants.paths import OFFLINE_DEBUG_IMAGES
from wiki_music.utilities.utils import list_files

if TYPE_CHECKING:
    from pathlib import Path
    from typing_extensions import TypedDict

    RespDict = TypedDict("RespDict", {"thumb": bytes,
                                      "dim": Tuple[int, Tuple[int, int]],
                                      "url": "Path"})

log = logging.getLogger(__name__)

log.info("Loaded Offline google images download")


class GoogleImagesDownload:
    """Offline version imitating google images download API.

    Main puprose is offline testing.

    Attributes
    ----------
    stack: queue.Queue
        a FIFO stack that contains all the downloaded images, the limit is set
        to 5. Then the downloading is paused until items from the queue are
        consumed.
    max: int
        maximum number of file that are loadable from directory
    files: List[str]
        list of image file paths
    """

    def __init__(self) -> None:
        self.stack: "queue.Queue[RespDict]" = queue.Queue()
        self._exit: bool = False
        self._files: List["Path"] = []

    def download(self, arguments: dict):
        """Start reding images from files.

        Parameters
        ----------
        arguments: dict
            dictionary of arguments, essentialy it is not needed. It is
            included only to maintain simillarity with original version API
        """
        dim: Tuple[int, int]
        size: float
        thumb: bytes

        successCount: int = 0
        errorCount: int = 0

        print(f"\nItem no.: 1 --> Item name = {arguments['keywords']}")
        print("Evaluating...")

        for f in self.files:

            try:
                dim = Image.open(str(f)).size
                size = f.stat().st_size
                thumb = f.read_bytes()
            except Exception as e:
                print(e)
                errorCount += 1
            else:
                self.stack.put({"thumb": thumb, "dim": (size, dim), "url": f})
                successCount += 1
                print(f"Completed Image Thumbnail ====> {successCount}. {f}")
            finally:
                if self._exit:
                    print("Album art search exiting ...")
                    return

        print(f"\nErrors: {errorCount}\n")

    def close(self):
        """Stop downloading images."""
        self._exit = True

    @property
    def max(self) -> int:
        """Maximum number of loadable images.

        Needed to set progresbar in GUI. The value is cached for later use.

        See also
        --------
        :func:`wiki_music.utilities.utils.list_files`
            to see list of suported files

        :type: int
        """
        return len(self.files)

    @property
    def files(self) -> List["Path"]:
        """List of image files to load in direstory.

        See also
        --------
        :func:`wiki_music.utilities.utils.list_files`
            to see list of suported files
        :const:`wiki_music.constants.paths.OFFLINE_DEBUG_IMAGES`
            directory that is searched for images

        Returns
        -------
        List[str]
            list of paths to image files
        """
        if not self._files:
            self._files = list_files(OFFLINE_DEBUG_IMAGES, file_type="image",
                                     recurse=True)

        return self._files
