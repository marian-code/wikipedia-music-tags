"""wiki_music submodule which provides all the GUI functionallity built with
support of all major python Qt bindings.
"""

import logging

# be sure to preserve import order! custom classes must be imported first!
# otherwise other imports will fail.
from .custom_classes import (
    CustomQStandardItem, TableItemModel, ImageTable, ImageWidget,
    NumberSortModel, RememberDir, ResizablePixmap, ResizableRubberBand,
    SelectablePixmap, CustomQTableView, CheckableListModel)
from .base import BaseGui
from .data_model import DataModel
from .cover_art import CoverArtSearch

__all__ = ["CustomQStandardItem", "TableItemModel", "ImageTable",
           "ImageWidget", "NumberSortModel", "RememberDir", "ResizablePixmap",
           "ResizableRubberBand", "SelectablePixmap", "BaseGui",
           "CoverArtSearch", "DataModel", "CustomQTableView",
           "CheckableListModel"]

logging.getLogger(__name__)
