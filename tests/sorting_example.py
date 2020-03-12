from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from collections import deque
from random import randint
from typing import List, Union, Optional


class Splash(QWidget):

    def __init__(self):
        super().__init__()

        # create model
        self.model = TableItemModel(self)
        self.model.setHorizontalHeaderLabels(["column 1", "column 2"])

        # create sort proxy
        self.proxy = NumberSortModel()
        self.proxy.setSourceModel(self.model)

        # create view
        self.table = CustomQTableView(self)
        self.table.setGeometry(0, 0, 275, 575)
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)

        # create buttons
        button = QPushButton('Find cells containing 1', self)
        button.move(300, 70)
        button.clicked.connect(lambda: self.table.search_string("1", False, False, False, [0, 1]))

        # create buttons
        button = QPushButton('Find cells containing 1222', self)
        button.move(300, 160)
        button.clicked.connect(lambda: self.table.search_string("1222", False, False, False, [0, 1]))

        button = QPushButton('replace 1 with 2', self)
        button.move(300, 190)
        button.clicked.connect(lambda: self.table.replace_all("1", "A", True))

        button1 = QPushButton('next', self)
        button1.move(300, 100)
        button1.clicked.connect(self.table._search_next)

        button2 = QPushButton('previous', self)
        button2.move(300, 130)
        button2.clicked.connect(self.table._search_previous)

        # fill model
        for i in range(15):
            self.model.appendRow([QStandardItem(str(i)),
                                  QStandardItem(str(randint(1, 100)))])

        self.show()


# takes care of the coloring of results
class _HighlightDelegate(QStyledItemDelegate):

    def initStyleOption(self, option: "QStyleOptionViewItem",
                        index: QModelIndex):

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

    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)

        self.selected_indices: List[QModelIndex] = []
        self.current_index = None

        self.setItemDelegate(_HighlightDelegate(self))

    @property
    def _model(self):
        return self.model().sourceModel()

    def _reset(self):

        # restore to original state before search
        for index in self.selected_indices:
            self._model.setData(index, False, SelectedRole)

        if self.current_index is not None:
            self._model.setData(self.current_index, False, CurrentRole)

        self.current_index = None
        self.selected_indices = []

    def search_string(self, string: str, case_sensitive: bool,
                      support_re: bool, support_wildcard: bool,
                      col_indices: List[int]):

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

        if self.current_index is not None:
            self._model.setData(self.current_index, False, CurrentRole)
            self._sort_indices_by_view()
            pos = self.selected_indices.index(self.current_index)
            next_pos = (pos + direction) % len(self.selected_indices)
            self.current_index = self.selected_indices[next_pos]
            self._model.setData(self.current_index, True, CurrentRole)

    def _search_next(self):
        self._move_match_cursor(1)

    def _search_previous(self):
        self._move_match_cursor(-1)

    def _sort_indices_by_view(self):
        # column-wise sorting should be good, since we are searching column-wise
        self.selected_indices.sort(
            key=lambda index: self.model().mapFromSource(index).row()
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


# custom implementation to sort according to numbers not strings
class NumberSortModel(QSortFilterProxyModel):

    def lessThan(self, left_index: "QModelIndex",
                 right_index: "QModelIndex") -> bool:

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


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    ex = Splash()
    sys.exit(app.exec_())