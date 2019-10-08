import re  # lazy loaded
from typing import List, Tuple, TYPE_CHECKING

from wiki_music.constants import TO_DELETE, ORDER_NUMBER, TIME
from wiki_music.utilities import (
    NoTracklistException, SharedVars, log_parser, normalize_caseless)

__all__ = ["DataExtractors"]

if TYPE_CHECKING:
    from bs4 import BeautifulSoup


class DataExtractors:
    """ Parse various table formats from wikipedia.
    
    Warnings
    --------
    This class is not ment to be instantiated, only inherited.
    """

    @classmethod
    def _from_table(cls, tables: List["BeautifulSoup"]
                   ) -> List[List[List[str]]]:
        """ Extract a classic wkikipedia html table composed of 'td' and 'th'
        html tags.

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

    @classmethod
    def _html2python_list(cls, table: "BeautifulSoup") -> List[str]:

        try:
            rows = [ch.get_text() for ch in table.find_all("li")
                    if ch.string != "\n"]
        except AttributeError:
            return []
        else:
            return rows

    @classmethod
    def _from_list(cls, table: "BeautifulSoup") -> List[List[str]]:
        """ Extract trackist formated as a html list with use of 'ol' and 'ul'
        tags.

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
            SharedVars.warning(msg)
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

    @classmethod
    def _get_track(cls, cell: str) -> Tuple[str, List[str]]:
        """ Extract track and subtracks names from table cell.

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

    @classmethod
    def _get_artist(cls, cell: str) -> List[str]:
        """ Splits list of artists in tracklist table cell separated by , or &

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

    @classmethod
    def _cut_out(cls, string: str, start: int, end: int) -> str:
        """ Given a string cuts out part specified by pointers.

        Parameters
        ----------
        string: str
            string containing substring to be removed
        start: int
            pointer to the begining of the substring to be removed
        end: int
            pointer to the end of the substring to be removed

        Returns
        -------
        str
            copy of passed in string with part between pointers removed
        """
        return (string[:start] + string[end + 1:]).strip()
