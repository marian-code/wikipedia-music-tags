"""Holds various html formats information extractors."""

import logging
import re  # lazy loaded
from typing import TYPE_CHECKING, List, Tuple, Optional

import fuzzywuzzy.fuzz as fuzz  # lazy loaded
import fuzzywuzzy.process as process  # lazy loaded

from wiki_music.constants import ORDER_NUMBER, TIME, TO_DELETE
from wiki_music.utilities import (NoTracklistException, normalize_caseless,
                                  warning)

log = logging.getLogger(__name__)

__all__ = ["DataExtractors"]

if TYPE_CHECKING:
    from bs4 import BeautifulSoup


class DataExtractors:
    """Parse various table formats from wikipedia.

    Warnings
    --------
    This class is not ment to be instantiated, only inherited.
    """

    @staticmethod
    def _from_table(tables: List["BeautifulSoup"]
                    ) -> List[List[List[str]]]:
        """Extract wkikipedia html table composed of 'td' and 'th' html tags.

        Parameters
        ----------
        tables: List[bs4.BeautifulSoup]
            each BeautifulSoup in list contains one htlm table

        Returns
        -------
        List[List[List[str]]]
            each emement in list is one parsed table, each table is a 2D array
            of strings representing rows and columns
        """
        data_collect = []
        for table in tables:

            # preinit list of lists
            rows = table.findAll("tr")
            row_lengths = [len(r.findAll(['th', 'td'])) for r in rows]
            ncols = max(row_lengths)
            nrows = len(rows)
            data = []

            for _ in rows:
                rowD = []
                for _ in range(ncols):
                    rowD.append('')
                data.append(rowD)

            # process html
            for i, row in enumerate(rows):
                cells = row.findAll(["td", "th"])

                for j, cell in enumerate(cells):
                    # lots of cells span cols and rows so lets deal with that
                    # row can probably span other subrows when there are
                    # subracks
                    cspan = int(cell.get('colspan', 1))
                    rspan = int(cell.get('rowspan', 1))

                    for k in range(rspan):
                        for l in range(cspan):
                            # sometimes cell is devided to subsells, so lets
                            # deal with this first
                            subcells = cell.find("div",
                                                 class_=re.compile("^hlist"))
                            if subcells:
                                c = ", ".join([s.text for s in
                                               subcells.findAll("li")])
                            else:
                                c = cell.text
                            data[i + k][j + l] += c

            for i in range(nrows):
                data[i] = list(filter(None, data[i]))
            data = list(filter(None, data))
            data_collect.append(data)

        return data_collect

    @staticmethod
    def _html2python_list(table: "BeautifulSoup") -> List[str]:
        """Converst html list to python list.

        Html list can be ordered <ol> or unordered <ul> its elements should be
        separated by <li> tags.

        Parameters
        ----------
        table: BeautifulSoup
            html object parsed by bs4

        Returns
        -------
        list
            each element represents on row in html list
        """
        try:
            rows = [ch.get_text() for ch in table.find_all("li")
                    if ch.string != "\n"]
        except AttributeError:
            return []
        else:
            return rows

    @classmethod
    @warning(log)
    def _from_list(cls, table: "BeautifulSoup") -> List[List[List[str]]]:
        """Extract trackist formated as a html list with 'ol' and 'ul' tags.

        See also
        --------
        :meth:`_html2python_list`

        Parameters
        ----------
        table: BeautifulSoup
            html list containing the tracklist

        Returns
        -------
        List[List[str]]
            2D array representing table with rows and columns
        """
        rows = cls._html2python_list(table)

        if not rows:
            msg = ("No tracklist found!\n"
                   "It is probaly contained in some unknown format")
            raise NoTracklistException(msg)
        else:

            data: list = []
            for i, row in enumerate(rows):
                data.append([])

                try:
                    number = re.search(r"\d+\.", row).group()  # type: ignore
                except AttributeError:
                    number = str(i + 1)
                else:
                    rows[i] = row.replace(number, "")
                finally:
                    number = re.sub(r"^0|\.", "", number.strip())
                    data[-1].append(number)

                try:
                    time = re.search(TIME, row).group()  # type: ignore
                except AttributeError:
                    data[-1].append(row.strip())
                else:
                    rows[i] = re.sub(r"\s*–?-?\s*" + time, "", row)
                    rows[i] = row.replace(time, "")
                    rows[i] = re.sub(r"\"", "", row)
                    data[-1].append(row.strip())
                    data[-1].append(time)

            return [data]

    @staticmethod
    def _get_track(cell: str) -> Tuple[str, List[str]]:
        """Extract track and subtracks names from table cell.

        Parameters
        ----------
        cell: str
            table cell contining track and posiblly subtrack names

        Returns
        -------
        tuple
            first element is track name and second is a list of subtracks
        """
        # extract tracks and subtracks
        tracks = cell.split("\n")
        for j, t in enumerate(tracks):
            # delete " and strip whitespaces from ends
            t = t.replace("\"", "").strip()

            if j > 0:  # for subtracks
                # delete empty spaces, remove numbering if there is any
                t = re.sub(ORDER_NUMBER, "", t)

            # odstranenie zatvoriek s casom
            t = re.sub(TIME, "", t)
            # remove bonus in bracket behinf track name
            # TODO use TO_DELETE list from constats here
            tracks[j] = re.sub(TO_DELETE, "", t)

        return tracks[0], tracks[1:len(tracks)]

    @staticmethod
    def _get_artist(cell: str) -> List[str]:
        """Splits list of artists in tracklist table cell separated by , or &.

        Parameters
        ----------
        cell: str
            string containing artists separated by delimites

        Returns
        -------
        List[str]
            list of artists
        """
        return [c.replace(",", "").strip() for c in re.split(",|&", cell)]

    @staticmethod
    def _fuzzy_extract(string: str, choices: List[str],
                       limit: Optional[int] = None) -> List[str]:
        """Fuzzy extract names, track types .. from brackets behind track name.

        Parameters
        ----------
        string: str
            string to match
        choices: List[str]
            list of possible choisec for string to match
        limit: int
            max number of extracted choices

        Returns
        -------
        List[str]
            list of extracted choices
        """
        if limit is None:
            limit = len(choices)

        return [b[0] for b in process.extractBests(string, choices,
                                                   scorer=fuzz.token_set_ratio,
                                                   score_cutoff=90,
                                                   limit=limit)]
