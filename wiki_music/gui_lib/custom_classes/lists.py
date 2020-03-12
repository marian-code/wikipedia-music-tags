"""Module providing custom Qt tables, their models and views."""

import logging
from typing import List, Optional

from wiki_music.gui_lib.qt_importer import (QStandardItem, QStandardItemModel,
                                            Qt)

logging.getLogger(__name__)

__all__ = ["CheckableListModel"]


class CheckableListModel(QStandardItemModel):
    """Builds list view with checkable items.

    References
    ----------
    https://stackoverflow.com/questions/846684/a-listview-of-checkboxes-in-pyqt
    """

    def add(self, item_name: str, checked: Optional[bool] = False):
        """Add one row to checkabel list.

        Paremeters
        ----------
        item_name: str
            name of the list item
        checked: Optional[bool]
            control if item will be in checked state upon insertion
        """
        item = QStandardItem(item_name)
        item.setCheckable(True)
        if checked:
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)

        self.appendRow(item)

    def get_checked_indices(self) -> List[int]:
        """Return list of indices of items that are checked.

        Returns
        -------
        List[int]
            list with checked indices
        """
        checked = list()
        for i in range(self.rowCount()):
            if bool(self.item(i, 0).checkState()):
                checked.append(i)

        return checked
