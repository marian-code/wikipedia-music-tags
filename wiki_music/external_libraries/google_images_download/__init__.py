"""Module handling cover art downloades from goole image search."""

from typing import Union, overload, TYPE_CHECKING
from typing_extensions import Literal

from . import google_images_download
from . import google_images_download_offline

if TYPE_CHECKING:
    Online = google_images_download.GoogleImagesDownload
    Offline = google_images_download_offline.GoogleImagesDownload

__all__ = ["GoogleImagesDownload"]


@overload
def GoogleImagesDownload(*, offline: Literal[True]) -> "Online": ...


@overload
def GoogleImagesDownload(*, offline: Literal[False]) -> "Offline": ...


@overload
def GoogleImagesDownload(*, offline: bool) -> Union["Online", "Offline"]: ...


def GoogleImagesDownload(*, offline: bool) -> Union["Online", "Offline"]:
    """Google images download factory.

    Parameters
    ----------
    offline: bool
        if true return offline version for ebugging

    Returns
    -------
    Union[Online, Offline]
        online or offline version with the same API
    """
    if offline:
        return google_images_download_offline.GoogleImagesDownload()
    else:
        return google_images_download.GoogleImagesDownload()
