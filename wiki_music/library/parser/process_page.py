"""This module containns the whole parser with all the inherited subclasses.
Class :class:`WikipediaParser` has complete functionallity but its methods need
to be called in the correst order to give sensible results.
"""

import logging
import re  # lazy loaded
from os import path
from threading import Thread
from typing import List, Tuple

import datefinder  # lazy loaded
import fuzzywuzzy.fuzz as fuzz  # lazy loaded
import fuzzywuzzy.process as process  # lazy loaded

from wiki_music.constants import FILES_DIR
from wiki_music.constants.parser_const import *
from wiki_music.utilities import (NLTK, SharedVars, caseless_contains,
                                  complete_N_dim, delete_N_dim, flatten_set,
                                  for_all_methods, get_image, normalize,
                                  normalize_caseless, replace_N_dim,
                                  time_methods, warning)
from wiki_music.utilities.exceptions import *

from .base import ParserBase
from .extractors import DataExtractors
from .in_out import ParserInOut
from .preload import WikiCooker

nc = normalize_caseless
log = logging.getLogger(__name__)

NLTK.run_import(log)  # imports nltk in separate thread

log.debug("parser imports done")

__all__ = ["WikipediaParser"]


@for_all_methods(time_methods)
class WikipediaParser(DataExtractors, WikiCooker, ParserInOut):
    """Class for parsing the wikipedia page and extracting tags data from it.

    Warnings
    --------
    Most parser methods are designed to fail gracefully so the extractions can
    proceed even when some subset of it failed. This has a dark side because
    it hides errors!!! All warning decorated methods are resilient to any
    exception defined in :mod:`wiki_music.utilities.exceptions` .

    References
    ----------
    https://www.crummy.com/software/BeautifulSoup/bs4/doc/: used to parse the
    wikipedia page

    Parameters
    ----------
    protected_vars: bool
        defines if certain variables should be initialized by __init__ method
        or not
    """

    def __init__(self, protected_vars: bool = True) -> None:

        log.debug("init parser")

        WikiCooker.__init__(self, protected_vars=protected_vars)
        ParserInOut.__init__(self, protected_vars=protected_vars)

        log.debug("init parser done")

    @warning(log)
    def get_release_date(self) -> str:
        """Gets album release date from information box in the
        top right corner of wikipedia page. Populates:attr:`wiki_music.DATE`

        Raises
        ------
        :exc:`utilities.exceptions.NoReleaseDateException`
            raised if no release date was extracted

        Returns
        -------
        str
            release year as a string
        """

        dates = self._sections["infobox"].find(class_="published")

        if dates:
            dates = datefinder.find_dates(dates.get_text())
            date_year = [d.strftime('%Y') for d in dates]
            self._release_date = list(set(date_year))[0]
        else:
            self._release_date = ""
            raise NoReleaseDateException

        return self._release_date

    @warning(log)
    def get_genres(self) -> List[str]:
        """Gets list of album genres from information box in the
        top right corner of wikipedia page. If found genre if only one then
        assigns is value to :attr:`GENRE`

        Raises
        ------
        :exc:`wiki_music.utilities.exceptions.NoGenreException`
            if no genres could be extracted from page

        Returns
        -------
        List[str]
            list of found genres
        """

        genres = self._sections["infobox"].find(class_="category hlist")

        if genres:
            self.genres = [g.string for g in genres.find_all(href=WIKI_GENRES,
                                                             title=True)]
        else:
            self.genres = []
            raise NoGenreException

        # auto select genre if only one was found
        if len(self.genres) == 1:
            self._selected_genre = self.genres[0]

        return self.genres

    @warning(log)
    def get_cover_art(self):
        """Gets album cover art information box in the top right corner
        of wikipedia page. Runs in a separate thread because the cover art
        data is not used by parser in any way, so it can be downloaded in
        the background. Populates :attr:`COVERART`

        Raises
        ------
        :exc:`wiki_music.utilities.exceptions.NoCoverArtException`
            if cover art url could not be found
        """

        # self.cover_art is not protected by lock, parser should have
        # more than enough time to get it before GUI requests it
        def cover_art_getter():

            """
            for child in self._sections["infobox"].children:
                if child.find("img") is not None:
                    image = child.find("img")
                    image_url = f"https:{image['src']}"

                    self.cover_art = get_image(image_url)
                    break
            """
            for img in self._sections["infobox"].find_all("img", src=True,
                                                          alt=True):
                if fuzz.token_set_ratio(img["alt"], self._album) > 90:
                    break

            if img:
                self.cover_art = get_image(f"https:{img['src']}")
            else:
                with open(path.join(FILES_DIR, "Na.jpg"), "rb") as f:
                    self.cover_art = bytearray(f.read())
                raise NoCoverArtException("Couldn't extract cover art from "
                                          "wikipedia page")

        Thread(target=cover_art_getter, name="CoverArtGetter").start()

    def get_composers(self) -> List[List[str]]:
        """Extracts composers from wikipedia page. Employs complex logic.
        First Person named entities are extracted by nltk. Then merges them
        with composers. After that uses this list of names to try to guess
        composers and coresponding tracks from short text above the table.

        See also
        --------
        :meth:`get_personnel`
            this method should run first because it populates the
            :attr:`_personnel` used by this method

        Warnings
        --------
        This method is not as robust as it should be. It fails for many
        types of formating.

        Returns
        -------
        List[List[str]]
            list of composers for every track
        """

        def check_name_complete(name, text):
            """Checks if name retrieved fromm text is complete or only part by
            checking the following words in text.

            Warnings
            --------
            This method is not really dependable, has quite poor results
            """

            # find out if next word starts with capital
            pos_1 = text.find(normalize(name)) + len(name) + 1
            # safety measure for when we hit the string end or
            # don´t find any entries
            if pos_1 > len(text) - 1 or pos_1 == -1:
                pos_1 = len(text) - 1
            # find out if the preceeding word starts with capital
            pos_2 = text.rfind(" ", 0, text.find(normalize(name)) - 1) + 1
            # if yes add it to name
            # useful if NLTK finds only one part of name

            if text[pos_1].isupper():
                surname = text[pos_1: text.find(" ", pos_1 + 1)]
                if surname not in name:
                    return name + " " + surname
            elif text[pos_2].isupper() and text[pos_2] != ".":
                surname = text[pos_2: text.find(" ", pos_2 + 1)]
                if surname not in name:
                    return name + " " + surname
            else:
                return name

        NLTK_names = set(self.NLTK_names + self._personnel)

        # get the short comment above the table which is marked as html
        # paragraph with <p>...</p>
        if self._sections["track_listing"][0].name == "p":
            html = self._sections["track_listing"][0].get_text()
        else:
            html = ""

        # find NLTK names that occure in sentence after specified phrases
        # split to sentences
        sentences = []

        for sentence in html.split("."):
            for d in DELIMITERS:
                if re.search(d, sentence, re.IGNORECASE):
                    sentences.append(sentence)

        # extract composers from sentences
        for sentence in sentences:
            parts = sentence.split("except")

            # find which track are affected by except
            index = []
            if len(parts) == 2:
                for i, tr in enumerate(self._tracks):
                    if caseless_contains(tr, parts[1]):
                        index.append(i)

            # assign composers to tracks
            for name in NLTK_names:

                if len(parts) == 2:
                    if caseless_contains(name, parts[1]):
                        n = check_name_complete(name, parts[1])

                        for ind in index:
                            self._composers[ind].append(n)

                if caseless_contains(name, parts[0]):
                    n = check_name_complete(name, parts[0])
                    for i, comp in enumerate(self._composers):
                        if i not in index:
                            if n not in comp:
                                self._composers[i].append(n)

        self._complete()

        return self._composers

    @warning(log)
    def get_contents(self) -> List[str]:
        """Extract page contets from keys in :attr:`_sections` dictionary.

        Raises
        ------
        :exc:`wiki_music.utilities.exceptions.NoContentsException`
            if no contents were retrieved

        Returns
        -------
        List[str]
            page contents as a list
        """

        # the last element is infobox which was added manually
        self._contents = [s.replace("_", " ").capitalize()
                          for s in self._sections.keys()][:-1]

        if len(self._contents) == 0:
            raise NoContentsException

        return self._contents

    @warning(log)
    def get_personnel(self) -> Tuple[List[str], List[List[int]]]:
        """Extract personnel from wikipedia page sections defined by:
        :const:`wiki_music.constants.parser_const.PERSONNEL_SECTIONS` then
        parse these entries for additional data like apperences on tracks.

        Raises
        ------
        :exc:`wiki_music.utilities.exceptions.NoPersonnelException`
            if no table or list with personnel was found

        Returns
        -------
        Tuple[List[str], List[List[int]]]
            two lists, first contains found personnel and the second has for
            each person list of tracks on which the person appeared
        """

        personnel = []
        appearences = []

        for s in PERSONNEL_SECTIONS:

            if s not in self._sections:
                continue

            for html in self._sections[s]:
                # if the toplevel tag is the list itself
                if html.name in ("ul", "ol"):
                    personnel.extend(self._html2python_list(html))

                # if the list is nested inside some other tags
                for h in html.find_all(["ul", "ol"]):
                    personnel.extend(self._html2python_list(h))

        for i, person in enumerate(personnel):

            # make space in appearences
            appearences.append([])

            # remove reference
            person = re.sub(r"\[ *\d+ *\]", "", person)

            # split to person and the rest
            try:
                person, appear = re.split(r" \W | as ", person, 1, flags=re.I)
            # if no delimiter is present skip to next
            except ValueError:
                continue

            # find references to song numbers
            for app in re.findall(r"\d{1,2}-\d{1,2}|\d{1,2}", appear):
                # when we find 3-6
                if "-" in app:
                    start, stop = [int(a) for a in app.split("-")]
                    a = [r for r in range(start, stop + 1)]
                    appearences[i].extend(a)
                # simple number
                else:
                    appearences[i].append(int(app))

            # find references to song names
            for j, t in enumerate(self._tracks):
                if re.match(t, appear, re.I):
                    appearences[i].append(j)

            # ensure no duplicates
            appearences[i] = list(set(appearences[i]))
            appearences[i] = [a - 1 for a in appearences[i]]
            personnel[i] = person

        self._personnel = personnel
        self._appearences = appearences

        self._complete()
        self._info_tracks()
        self._merge_artist_personnel()

        if len(personnel) == 0:
            raise NoPersonnelException

        return self._personnel, self._appearences

    @warning(log)
    def get_tracks(self) -> Tuple[List[str], List[List[str]]]:
        """Attempt to extract tracklist from html table or list on wikipedia.

        See also
        --------
        :meth:`_from_table`
            used to parse tracklist in htlm table
        :meth:`_from_list`
            used to parse tracklist in html list
        :meth:`_process_tracks`
            method called to parse raw extracted table and get
            song numbers, artists, composers ...

        Raises
        ------
        :exc:`wiki_music.utilities.exceptions.NoTracklistException`
            raised if no tracklist in any format was found

        Returns
        -------
        Tuple[List[str], List[List[str]]]
            list of tracks and for each track list of atrists
        """

        tables = []
        for html in self._sections["track_listing"]:
            # if the toplevel tag is the table itself
            if html.name == "table":
                if "tracklist" in html["class"]:
                    tables.extend(html)

            # if the list is nested inside some other tags
            for h in html.find_all("table", class_="tracklist"):
                tables.extend(h)

        if tables:
            data = self._from_table(tables)
        else:
            try:
                tables = []
                for s in self._sections["track_listing"]:
                    if s.name in ("ul", "ol"):
                        tables.append(s)
                    else:
                        tables.extend(s.find_all(["ul", "ol"]))
            except AttributeError:
                msg = (f"No tracklist found!\nURL: {self.url}\nprobably "
                       f"doesn´t belong to album: {self._album} by "
                       f"{self._band}")
                SharedVars.warning(msg)
                raise NoTracklistException(msg)
            else:
                data = []
                for t in tables:
                    data.extend(self._from_list(t))

        return self._process_tracks(data)

    def _process_tracks(self, data: List[List[str]]
                        ) -> Tuple[List[str], List[List[str]]]:
        """Process raw extracted list of tables with trackists for
        track details.
        
        Returns
        -------
        Tuple[List[str], List[List[str]]]
            list of tracks and for each track list of atrists
        """

        self._disk_sep.append(0)

        index = 1
        for CD in data:

            self._disks.append([f"{self._album} CD {index}", len(self)])
            index += 1
            for song in CD:
                if "no" in nc(song[0]):
                    # table header - possibly use in future
                    # posladny stlpec je length a ten väčšinou netreba
                    if "length" in nc(song[-1]):
                        self._header.append(song[:-1])
                    else:
                        self._header.append(song)
                elif re.match(ORDER_NUMBER, song[0]):
                    self._numbers.append(song[0].replace(".", ""))
                    tmp1, tmp2 = self._get_track(song[1])
                    self._tracks.append(tmp1)
                    self._subtracks.append(tmp2)

                    if len(song) > 3:
                        self._artists.append([])
                        self._composers.append([])

                        # all columns between track and track length belong to
                        # artists we assign them to artists or composers
                        # based on label in header
                        for i in range(2, len(song) - 1):
                            a = self._get_artist(song[i])
                            try:
                                is_composer = process.extractOne(
                                    self._header[-1][i], COMPOSER_HEADER,
                                    score_cutoff=90, scorer=fuzz.ratio)
                            except:
                                self._artists[-1].extend(a)
                            else:
                                if is_composer:
                                    self._composers[-1].extend(a)
                                else:
                                    self._artists[-1].extend(a)
                    else:
                        self._artists.append([])
                        self._composers.append([])
                elif "total" in nc(song[0]):
                    # total length summary
                    pass
                else:
                    # if all else passes than line must be disc title
                    self._disks[-1] = [song[0], len(self)]

        # bonus track are sometimes marked as another disc
        disks_filtered = [d for d in self._disks if "bonus" not in nc(d[0])]

        self._disk_sep = [i[1] for i in disks_filtered]
        self._disk_sep.append(len(self))
        self._disks = [i[0] for i in disks_filtered]

        # assign disc number to tracks
        for i, _ in enumerate(self._tracks):
            for j, _ in enumerate(self._disk_sep[:-1]):
                if self._disk_sep[j] <= i and i < self._disk_sep[j + 1]:
                    self._disc_num.append(j + 1)

        return self._tracks, self._artists

    def _info_tracks(self):
        """Parse track names for aditional information.

        Like artist, composer, type... . Also get rid of useless strings like
        bonus track, featuring... . These informations are assumed to be
        enclosed in brackets behind the track name.
        """

        self._types = []
        self._subtypes = []

        comp_flat = flatten_set(self._composers)

        # hladanie umelcov ked su v zatvorke za skladbou
        # + zbavovanie sa bonus track a pod.
        for i, tr in enumerate(self._tracks):

            self._types.append("")
            self._subtypes.append([])

            start_list = [m.start() for m in re.finditer(r'\(', tr)]
            end_list = [m.start() for m in re.finditer(r'\)', tr)]

            for start, end in zip(start_list, end_list):

                self._tracks[i] = re.sub(TO_DELETE, "", tr, re.I)

                artist = re.sub("[,:]", "", tr[start + 1:end])
                artist = re.split(r",|\/|\\", artist)

                for art in artist:
                    for un in UNWANTED:
                        art = re.sub(un, "", art, flags=re.IGNORECASE)

                    # TODO all these maybe should be in the UNWANTED loop??
                    # check against additional personnel
                    for person in self._personnel:
                        if fuzz.token_set_ratio(art, person) > 90:
                            self._artists[i].append(person)
                            self._tracks[i] = self._cut_out(tr, start, end)

                    # check agains composers
                    for comp in comp_flat:
                        if fuzz.token_set_ratio(art, comp) > 90:
                            self._artists[i].append(comp)
                            self._tracks[i] = self._cut_out(tr, start, end)

                    # check if instrumental, ...
                    _type, score = process.extractOne(
                        art, DEF_TYPES, scorer=fuzz.token_sort_ratio)
                    if score > 90:
                        self._types[i] = art  # _type
                        self._tracks[i] = self._cut_out(tr, start, end)

            if self._subtracks:
                for j, sbtr in enumerate(self._subtracks[i]):

                    self._subtypes[i] = [""] * len(sbtr)

                    start_list = [m.start() for m in re.finditer(r'\(', sbtr)]
                    end_list = [m.start() for m in re.finditer(r'\)', sbtr)]

                    for start, end in zip(start_list, end_list):

                        art = re.sub("[,:]", "", sbtr[start + 1:end]).split()

                        for a in art:
                            # check against additional personnel
                            for person in self._personnel:
                                if fuzz.token_set_ratio(a, person) > 90:
                                    self._artists[i].append(person)
                                    sbtr = self._cut_out(sbtr, start, end)
                                    self._subtracks[i][j] = sbtr

                            # check if instrumental, ...
                            _type, score = process.extractOne(
                                a, DEF_TYPES, scorer=fuzz.token_sort_ratio)
                            if score > 90:
                                self._subtypes[i][j] = _type
                                sbtr = self._cut_out(sbtr, start, end)
                                self._subtracks[i][j] = sbtr

    def _complete(self):
        """Recursively traverses: :attr:`_composers`, :attr:`artists` and
        :attr:`_personnel` and checks each name with each if some is found to
        be incomplete then it is replaced by longer version from other list.
        """

        to_complete = (self._composers, self._artists, self._personnel)
        delete: list = ["", " "]

        # complete everything with everything
        for to_replace in to_complete:
            for to_find in to_complete:
                complete_N_dim(to_replace, to_find)

        # sort artist alphabeticaly
        if self._artists:
            for a in self._artists:
                a.sort()

        for tc in to_complete:
            delete_N_dim(tc, delete)

        # get rid of feat., faeturing ...
        for tc in to_complete:
            for un in UNWANTED:
                replace_N_dim(tc, un)

        # get rid of artists duplicates
        for tc in to_complete:
            for i, t in enumerate(tc):
                if isinstance(t, list):
                    tc[i] = sorted(list(set(t)))

    def _merge_artist_personnel(self):
        """Assigns personnel which have appearences specified to coresponding
        list of track artists.
        """
        self._log.debug("merge artists and personnel")

        for person, appear in zip(self._personnel, self._appearences):
            for a in appear:
                self._artists[a].append(person)

    def merge_artist_composers(self):
        """Move all artists to composers list. This is done or left out based
        on user input"""

        for i, (c, a) in enumerate(zip(self._composers, self._artists)):
            self._composers[i] = sorted(list(filter(None, set(c + a))))

        self._artists = [""] * len(self._composers)

    @property
    @warning(log, show_GUI=False)
    def NLTK_names(self):
        """Use nltk to extract person names from supplied sections of the
        wikipedia page.

        See also
        --------
        :const:`wiki_music.constants.parser_const.PERSONNEL_SECTIONS`
            these sections of the page + track_listing are passed to nltk
            to look for names

        Raises
        ------
        :exc:`wiki_music.utilities.exceptions.NoNames2ExtractException`
            vhen the page doesn't have any of the sections defined in See also
            section. So no text can be provided to nltk. It makes no sense to
            try extraction from others parts of tha page as they are too
            cluttered by hardly classifiable information.
        """

        if not self._NLTK_names:

            document = ""
            for key, value in self._sections.items():

                if key in (PERSONNEL_SECTIONS + ("track_listing", )):
                    for val in value:
                        document += val.get_text(" ")

            # if none of the sections is present exit method
            if not document:
                raise NoNames2ExtractException

            try:
                stop = NLTK.nltk.corpus.stopwords.words('english')
            except AttributeError:
                raise NltkUnavailableException("NLTK not available!")

            document = ' '.join([i for i in document.split() if i not in stop])
            sentences = NLTK.nltk.tokenize.sent_tokenize(document)
            sentences = [NLTK.nltk.word_tokenize(sent) for sent in sentences]
            sentences = [NLTK.nltk.pos_tag(sent) for sent in sentences]

            names = []
            for tagged_sentence in sentences:
                for chunk in NLTK.nltk.ne_chunk(tagged_sentence):
                    if type(chunk) == NLTK.nltk.tree.Tree:
                        if chunk.label() == 'PERSON':
                            names.append(' '.join([c[0] for c in chunk]))

            names = sorted(list(set(names)))

            # TODO smetimes when two names are separated only by "and", "by"..
            # or such short word the two names are found together as one
            # and the sunsequent completion messes the right names
            # that were found
            """
            # filter incomplete names
            selected_names = []
            for n1 in names:
                name = n1
                for n2 in names:
                    if name in n2:
                        name = n2
                    else:
                        pass

                selected_names.append(name)
            """

            # filter out already found tracks
            filtered_names = [n for n in names
                              if fuzz.token_set_ratio(n, self._tracks) < 90]

        return self._NLTK_names
