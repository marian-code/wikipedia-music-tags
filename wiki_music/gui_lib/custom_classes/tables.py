"""Module providing custom Qt tables, their models and views."""

import logging
from collections import deque
from pathlib import Path
from typing import (
    TYPE_CHECKING, Any, Deque, List, Optional, Sequence, Tuple, Union)

from wiki_music.gui_lib.qt_importer import (QAbstractItemView, QColor,
                                            QPalette, QSortFilterProxyModel,
                                            QStandardItem, QStandardItemModel,
                                            QStyledItemDelegate, Qt,
                                            QTableView, QTableWidget, QWidget,
                                            Signal)

from .items import CustomQStandardItem, ImageItem

if TYPE_CHECKING:
    from wiki_music.gui_lib.qt_importer import (QDropEvent, QEnterEvent,
                                                QMoveEvent, QModelIndex,
                                                QStyleOptionViewItem)

__all__ = ["NumberSortProxy", "ImageTable", "TableItemModel",
           "CustomQTableView"]

logging.getLogger(__name__)

#: marks item curently marked by search index
CurrentRole = Qt.UserRole + 1
#: marks items found by table search
SelectedRole = Qt.UserRole + 2


class _HighlightDelegate(QStyledItemDelegate):
    """Delegate used for changing text color and highlighting behaviour.

    References
    ----------
    https://stackoverflow.com/questions/49986965/pyqt4-qtableview-cell-text-changes-color-on-row-selection
    https://doc.qt.io/qtforpython/PySide2/QtWidgets/QStyledItemDelegate.html
    """

    def __init__(self, parent: Optional["CustomQTableView"] = None) -> None:
        """Object initialization.

        cells - marked cells that have different content
        """
        QStyledItemDelegate.__init__(self, parent)
        self._parent = parent

    def initStyleOption(self, option: "QStyleOptionViewItem",
                        index: "QModelIndex"):

        super().initStyleOption(option, index)

        is_current = index.data(CurrentRole) or False
        is_selected = index.data(SelectedRole) or False

        if is_current:
            option.backgroundBrush = QColor(Qt.red)
            option.palette.setColor(QPalette.Normal, QPalette.Highlight,
                                    QColor(Qt.red))
        elif is_selected:
            option.backgroundBrush = option.palette.highlight()


class CustomQTableView(QTableView):
    """Table view implementing drag & drop actions.

    This is a custom widget for QtDesigner, its location must remain the same,
    otherwise UIC compiler will not find it at compile time. If it should be
    moved than QtableView widget promote settings must be changed accordingly.
    This class has to reimplement all three methods for drag & drop to work.

    Accepts only drops with paths to file or directory

    Attributes
    ----------
    FileDropped: Signal(Path)
        signal emited when folder is dropped to table
    _selected_rows_save: Optional[List[int]]
        save selected rows when search and replace is active

    References
    ----------
    https://stackoverflow.com/questions/19622014/how-do-i-use-promote-to-in-qt-designer-in-pyqt4
    https://www.learnpyqt.com/courses/qt-creator/embed-pyqtgraph-custom-widgets-qt-app/
    """

    FileDropped: Signal = Signal(str)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setAcceptDrops(True)

        self.selected_indices: List["QModelIndex"] = []
        self.current_index: Optional["QModelIndex"] = None

        self.setItemDelegate(_HighlightDelegate(self))

        self._selected_rows_save: List[int] = []

    def dragEnterEvent(self, event: "QEnterEvent"):
        """Handle start of a mouse drag, allow only data with file loactions.

        Parameters
        ----------
        event: QEnterEvent
            object containing info about occuring event
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: "QMoveEvent"):
        """Handle mouse drag movement, allow only data with file loactions.

        Parameters
        ----------
        event: QMoveEvent
            object containing info about occuring event
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: "QDropEvent"):
        """Handle data drop into the table.

        Only the first address is used, others are discarded.

        Parameters
        ----------
        event: QDropEvent
            object containing info about occuring event and dropped data
        """
        # take the first address and convert to local file
        path = Path(event.mimeData().urls()[0].toLocalFile())

        if path.is_dir():
            self.FileDropped.emit(str(path.resolve()))
        else:
            self.FileDropped.emit(str(path.parent.resolve()))

    def selected_rows(self, to_source: bool = True) -> List[int]:
        """Returns indices of selected table rows.

        Parameters
        ----------
        to_source: bool
            map proxy indices to source model

        Returns
        -------
        List[int]
            indices of selected rows
        """
        indices = self.selectionModel().selectedRows()
        if to_source:
            return [self._proxy.mapToSource(i).row() for i in indices]
        else:
            return [i.row() for i in indices]

    def set_search_visibility(self, tab_index: int):
        """Sets flags that tells if search tab is visible.

        Parameters
        ----------
        tab_index: int
            tab index
        """
        if tab_index > 1:
            raise NotImplementedError(f"Settings for tab {tab_index} have not "
                                      f"yet been implemented")

        if tab_index:
            self.setSelectionMode(QAbstractItemView.NoSelection)
            self._selected_rows_save = self.selected_rows(to_source=False)
            self.selectionModel().clearSelection()
            self._set(True)
        else:
            self.setSelectionMode(QAbstractItemView.SingleSelection)
            for i in self._selected_rows_save:
                self.selectRow(i)
            self._set(False)

    @property
    def _model(self) -> "TableItemModel":
        """Underlying table data model.

        :type: TableItemModel
        """
        # need to recurse two layers first is the NumberSortProxy proxy and the
        # second is the actual model: TableItemModel
        return self._proxy.sourceModel()

    @property
    def _proxy(self) -> "NumberSortProxy":
        """Underlying proxy model.

        :type: NumberSortProxy
        """
        return self.model()

    def _set(self, value: bool):
        """Set roles for found items to True or False.

        Parameters
        ----------
        value: bool
            all roles will be set to this value
        """
        for index in self.selected_indices:
            self._model.setData(index, value, SelectedRole)

        if self.current_index is not None:
            self._model.setData(self.current_index, value, CurrentRole)

    def _reset(self):
        """Restore to original non-highlight state before search."""
        self._set(False)

        self.current_index = None
        self.selected_indices = []

    def search_string(self, string: str, case_sensitive: bool,
                      support_re: bool, support_wildcard: bool,
                      col_indices: List[int]):
        """Search all table fields for string match.

        Parameters
        ----------
        string: str
            string to search for
        case_sensitive: bool
            if True search will be case sensitive
        support_re: bool
            support regular expressions
        support_wildcard: bool
            support widlcard operators
        col_indices: List[int]
            list of column indices where search will be performed

        References
        ----------
        https://doc-snapshots.qt.io/4.8/qt.html#MatchFlag-enum
        https://stackoverflow.com/questions/60639974/visual-position-of-item-in-qtableview/60642965?noredirect=1#comment107304241_60642965
        """
        # empty string would match all if it is recieved clear selection
        # and return
        if not string:
            self._reset()
            return

        # set the right flags for search
        flags = Qt.MatchContains
        if support_re:
            flags |= Qt.MatchRegExp
        if support_wildcard:
            flags |= Qt.MatchWildcard
        if case_sensitive:
            flags |= Qt.MatchCaseSensitive

        self._reset()

        self.selected_indices = self._model.match_all(string, col_indices,
                                                      Qt.DisplayRole, flags)

        self._sort_indices_by_view()

        if self.selected_indices:
            self.current_index = self.selected_indices[0]

        for index in self.selected_indices:
            self._model.setData(index, True, SelectedRole)

        if self.current_index is not None:
            self._model.setData(self.current_index, True, CurrentRole)

    def _move_match_cursor(self, direction: int):
        """Move search cursor to the next position.

        Parameters
        ----------
        direction: int
            direction of the move +1 = next, -1 = previous
        """
        if self.current_index is not None:
            self._model.setData(self.current_index, False, CurrentRole)
            self._sort_indices_by_view()
            pos = self.selected_indices.index(self.current_index)
            next_pos = (pos + direction) % len(self.selected_indices)
            self.current_index = self.selected_indices[next_pos]
            self._model.setData(self.current_index, True, CurrentRole)

    def search_previous(self):
        """Move search cursor to the previous position.

        See also
        --------
        :meth:`_move_match_cursor`
        """
        self._move_match_cursor(-1)

    def search_next(self):
        """Move search cursor to the next position.

        See also
        --------
        :meth:`_move_match_cursor`
        """
        self._move_match_cursor(1)

    def replace_one(self, search_str: str, replace_str: str):
        """Replaces one currently selected occurence.

        Parameters
        ----------
        search_str: str
            string to look for
        replace_str: str
            string to use as replacement

        See also
        --------
        :meth:`replace_all`
        """
        self.replace_all(search_str, replace_str, only_one=True)

    def _sort_indices_by_view(self):
        """Sort indeces by their position in table, top to bottom."""
        # column-wise sorting should be good,
        # since we are searching column-wise
        self.selected_indices.sort(
            key=lambda index: self._proxy.mapFromSource(index).row()
        )

    def replace_all(self, search_str: str, replace_str: str,
                    only_one: Optional[bool] = False):
        """Replaces one currently selected occurence.

        Parameters
        ----------
        search_str: str
            string to look for
        replace_str: str
            string to use as replacement
        only_one: bool
            replace only the first occurence
        """
        while self.selected_indices:

            # remove already replaced cells from stack
            index = self.selected_indices.pop(0)

            # cancel selected role
            self._model.setData(index, False, SelectedRole)

            # cancel old highlight
            self._model.setData(self.current_index, False, CurrentRole)

            if self.selected_indices:
                # move curernt index
                self.current_index = self.selected_indices[0]
                # move highlight cursor
                self._model.setData(self.current_index, True, CurrentRole)

            # get cell string
            text = self._model.item(index.row(), index.column()).text()
            # replace with desired text
            text = text.replace(search_str, replace_str)
            # set new value
            self._model.item(index.row(), index.column()).setText(text)

            # maintain the right sorting
            self._sort_indices_by_view()

            # if replace only one, break after the first iteration
            if only_one:
                break


class TableItemModel(QStandardItemModel):
    """Make table columns indexable by its names. Add easy column manipulation.

    Overrides the default impementation. adds `__getitem__`
    """

    def setColumn(self, column: Union[int, str], value_list: list):
        """Write python list to Qt table column.

        Parameters
        ----------
        column: Union[int, str]
            column integer index or header name
        value_list: list
            values to put in column
        """
        col = self._format_col(column)

        for row, value in enumerate(value_list):
            self.setItem(row, col, CustomQStandardItem(value))

    def set_python_item(self, row: int, column: int, item: Any):
        """Casts python type to Qt and passes its ownership table.

        Parameters
        ----------
        row: int
            row index
        column: int
            column index
        item: Any
            items to put into table
        """
        self.setItem(row, column, CustomQStandardItem(item))

    def getColumn(self, column: Union[int, str],
                  split: Optional[bool] = False) -> list:
        """Return whole table column as python list.

        Parameters
        ----------
        column: Union[int, str]
            column integer index or header name
        split: bool
            is strings in each column cell should be split on ',' to list

        Returns
        -------
        list
            list of column cell items
        """
        col = self._format_col(column)

        return [self.item(row, col).text(split=split)
                for row in range(self.rowCount())]

    def _format_col(self, column: Union[int, str]) -> int:
        """Convert column header name to index.

        Parameters
        ----------
        column: Union[int, str]
            column integer index or header name

        Returns
        -------
        int
            column index
        """
        if isinstance(column, int):
            return column
        else:
            return self.__getitem__(column)

    def __getitem__(self, name: str) -> int:
        """Column index from column header name.

        Parameters
        ----------
        name: str
            table column name

        Returns
        -------
        int
            column index

        Raises
        ------
        KeyError
            if the name does not exist in column headers
        """
        for column_int in range(self.columnCount()):
            if self.headerData(column_int, Qt.Horizontal) == name:
                return column_int

        raise KeyError(f"No column with name {name}")

    def match_all(self, string: str, columns: Sequence[Union[str, int]],
                  role: Qt.ItemDataRole, flags: Qt.MatchFlags
                  ) -> List["QModelIndex"]:
        """Matches all indices without restrictions in selected table columns.

        Parameters
        ----------
        string: str
            string to search for
        columns: List[Union[str, int]]
            column indeces or header names, can be mixed
        role: Qt.ItemDataRole
            model data role to search
        flags: Qt.MatchFlags
            Qt match flags

        Returns
        -------
        List[QModelIndex]
            matching model indices
        """
        match_indices: List["QModelIndex"] = list()

        for column in columns:

            # translate column header names to indices
            if isinstance(column, str):
                column = self.__getitem__(column)

            # always start search all cells in row
            index = self.index(0, column)

            # match
            match_indices.extend(self.match(index, role, string, -1, flags))

        return match_indices


class ImageTable(QTableWidget):
    """Table with cells holding Images with short text in cells.

    Parameters
    ----------
    parent: QWidget
        reterence to parent widget for centering

    Attribures
    ----------
    self.MAX_COLUMNS: int
        constant saying how many columns should the table have
    self.actualCol: int
        holds the position of actual column

    See also
    --------
    :class:ImageItem
        each cell holds one of these widgets
    """

    MAX_COLUMNS: int
    actualCol: int

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        QTableWidget.__init__(self, parent)

        self.MAX_COLUMNS: int = 4
        self.actualCol: int = -1
        self.setColumnCount(1)
        self.setRowCount(1)
        self.resizeToContents()
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

    def add_pic(self, label: str, picture: bytes):
        """Add one picture to table.

        Pictures are added in row until the row has `ImageTable.MAX_COLUMNS`
        pictures then we switch to the next row.

        Parameters
        ----------
        label: str
            short text to display under picture
        picture: bytes
            picture to display

        Raises
        ------
        ValueError
            when method trie to add picture in column with
            `index` > `ImageTable.MAX_COLUMNS`
        """
        if self.actualCol < self.MAX_COLUMNS:
            self.actualCol += 1
            if self.rowCount() == 1:
                self.setColumnCount(self.columnCount() + 1)
        elif self.actualCol == self.MAX_COLUMNS:
            self.actualCol = 0
            self.setRowCount(self.rowCount() + 1)
        else:
            raise ValueError("Exception in adding picture to table. Actual"
                             " column exceeded value of max columns")

        self.setCellWidget(*self.ij, ImageItem(label, picture))
        self.resizeToContents()

    @property
    def ij(self) -> Tuple[int, int]:
        """Actual free cell where next picture should be added.

        :type: Tuple[int, int]
        """
        return self.rowCount() - 1, self.actualCol

    def resizeToContents(self):
        """Resizes table rows and columns to fit largest cell contents."""
        self.resizeColumnsToContents()
        self.resizeRowsToContents()


class NumberSortProxy(QSortFilterProxyModel):
    """Custom table proxy model which can sort numbers not only strings."""

    def lessThan(self, left_index: "QModelIndex",
                 right_index: "QModelIndex") -> bool:
        """Reimplemented comparator method to handle numbers correctly.

        Parameters
        ----------
        left_index: QModelIndex
            index of the left compared element
        right_index: QModelIndex
            index of the right compared element
        """
        left_var: str = left_index.data(Qt.EditRole)
        right_var: str = right_index.data(Qt.EditRole)

        try:
            return float(left_var) < float(right_var)
        except (ValueError, TypeError):
            pass

        try:
            return left_var < right_var
        except TypeError:  # in case of NoneType
            return True
