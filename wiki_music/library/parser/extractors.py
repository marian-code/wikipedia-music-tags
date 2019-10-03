import re  # lazy loaded
from typing import Any, List, Tuple

from wiki_music.utilities import (
    NoTracklistException, SharedVars, log_parser, normalize_caseless)

__all__ = ["DataExtractors"]


class DataExtractors:
    """ Extracts various table formats from wikipedia. """

    @classmethod
    def _from_table(cls, tables: list) -> List[List[List[str]]]:

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
                            if subcells is not None:
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
    def _from_list(cls, tables: Any) -> List[List[str]]:

        table = tables.find_next_sibling("ol")
        if table is None:
            table = tables.find_next_sibling("ul")

        try:
            rows = [ch for ch in table.children if ch.string != "\n"]
        except AttributeError as e:
            log_parser.warning(e)
            msg = ("No tracklist found!\n"
                   "It is probaly contained in some unknown format")
            SharedVars.warning(msg)
            raise NoTracklistException(msg)

        data: list = []
        for i, row in enumerate(rows):
            data.append([])

            try:
                number = re.search(r"\d+\.", row).group()
            except AttributeError:
                number = str(i + 1)
            else:
                rows[i] = row.replace(number, "")
            finally:
                number = re.sub(r"^0|\.", "", number.strip())
                data[-1].append(number)

            try:
                time = re.search(r"\d+\:\d+", row).group()
            except AttributeError:
                data[-1].append(row.strip())
            else:
                rows[i] = re.sub(r"\s*–?-?\s*" + time, "", row)
                rows[i] = row.replace(time, "")
                rows[i] = re.sub(r"\"", "", row)
                data[-1].append(row.strip())
                data[-1].append(time)

        return data

    @classmethod
    def get_track(cls, data: str) -> Tuple[list, list]:

        tracks: list = []
        subtracks: list = []

        # extract tracks and subtracks
        temp = data.split("\n")
        for j, tmp in enumerate(temp):
            if j > 0:
                # replace " with space, delete empty spaces,
                # remove numbering if there is any
                temp[j] = (tmp.replace("\"", "").strip().split(' ', 1)[1])
            else:
                temp[j] = tmp.replace("\"", "").strip()

            if "(" in tmp:
                start = tmp.find("(")
                end = tmp.find(")", start)
                # odstranenie zatvoriek s casom
                if tmp[start + 1:end].replace(":", "").isdigit():
                    temp[j] = cls.cut_out(tmp, start, end)
                # odstranenie bonus track
                if "bonus" in normalize_caseless(tmp[start + 1:end]):
                    temp[j] = cls.cut_out(tmp, start, end)

        tracks.append(temp[0].strip())
        subtracks.append(temp[1:len(temp)])

        return tracks, subtracks

    @classmethod
    def get_artist(cls, data: str) -> list:
        temp = re.split(",|&", data)
        return [tmp.replace(",", "").strip() for tmp in temp]

    @classmethod
    def cut_out(cls, string: str, start: int, end: int) ->str:
        return (string[:start] + string[end + 1:]).strip()
