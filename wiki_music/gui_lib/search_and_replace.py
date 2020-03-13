"""Module controling search and replace tab."""
import logging

from wiki_music.constants import GUI_HEADERS
from wiki_music.gui_lib import BaseGui, CheckableListModel
from wiki_music.gui_lib.qt_importer import QMessageBox, QPushButton, QIcon, QStyle

__all__ = ["Replacer"]

log = logging.getLogger(__name__)
log.debug("finished gui search & replace imports")


class Replacer(BaseGui):
    """Controls the search and replace tab in GUI.

    Warnings
    --------
    This class is not ment to be instantiated, only inherited.
    """

    def __init__(self) -> None:

        super().__init__()

        self.replace_tag_selector_model = CheckableListModel()
        self._fill_tags_list()

    def _fill_tags_list(self):
        """Create a checkable list with table column name headers."""
        for tag in GUI_HEADERS:
            self.replace_tag_selector_model.add(tag)

        self.replace_tag_selector_view.setModel(
            self.replace_tag_selector_model)

    def _setup_search_replace(self):
        """Connect to signals essential for search and replace tab."""
        # re-run search when search columns are reselected
        self.replace_tag_selector_model.itemChanged.connect(
            self._search_replace_run)

        # re-run search when options are checked
        self.search_support_re.stateChanged.connect(
            self._search_replace_run)
        self.search_support_wildcard.stateChanged.connect(
            self._search_replace_run)
        self.search_case_sensitive.stateChanged.connect(
            self._search_replace_run)

        # connect to control buttons
        self.search_next.clicked.connect(self.tableView.search_next)
        self.search_previous.clicked.connect(self.tableView.search_previous)
        self.replace_one.clicked.connect(
            lambda: self.tableView.replace_one(
                self.search_string_input.text(),
                self.replace_string_input.text()))
        self.replace_all.clicked.connect(
            lambda: self.tableView.replace_all(
                self.search_string_input.text(),
                self.replace_string_input.text()
            ))

        # search is run interacively as user is typing
        self.search_string_input.textChanged.connect(
            self._search_replace_run)

        # on tab change change selection and search highlight mode
        self.tool_tab.currentChanged.connect(
            self.tableView.set_search_visibility)

        # seems that filtering is done by rows
        # self.search_string_input.textChanged.connect(
        #     self.proxy.setFilterFixedString)

    def _search_replace_run(self, string: str):
        """Process search parameters and call table search method.

        Parameters
        ----------
        string: str
            string to search for
        """
        if (self.search_support_re.isChecked() and
            self.search_support_wildcard.isChecked()):

            msg = QMessageBox(QMessageBox.Warning, "Warning",
                              "Attempting to use regex and wildcards at once "
                              "may return unexpected results. "
                              "Do you want to proceed?",
                              QMessageBox.Yes | QMessageBox.No)

            if msg.exec_() == QMessageBox.No:
                return
            else:
                log.warning("Wildcard and regex used at once in search")

        self.tableView.search_string(
            self.search_string_input.text(),
            self.search_case_sensitive.isChecked(),
            self.search_support_re.isChecked(),
            self.search_support_wildcard.isChecked(),
            self.replace_tag_selector_model.get_checked_indices()
        )
