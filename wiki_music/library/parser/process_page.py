""" This module containns the whole parser with all the inherited subclasses.
Class :class:`WikipediaParser` has complete functionallity but its methods need
to be called in the correst order to give sensible results.
"""

import re  # lazy loaded
from os import path
from threading import Thread
from typing import List

import datefinder  # lazy loaded
import fuzzywuzzy.fuzz as fuzz  # lazy loaded
import fuzzywuzzy.process as process  # lazy loaded

from wiki_music.constants import FILES_DIR
from wiki_music.constants.parser_const import *
from wiki_music.utilities import (NLTK, SharedVars,
                                  caseless_contains, complete_N_dim,
                                  delete_N_dim, flatten_set, for_all_methods,
                                  get_image, log_parser, normalize,
                                  normalize_caseless, replace_N_dim,
                                  time_methods, warning)
from wiki_music.utilities.exceptions import *

from .base import ParserBase
from .extractors import DataExtractors
from .in_out import ParserInOut
from .preload import WikiCooker

nc = normalize_caseless

NLTK.run_import()  # imports nltk in separate thread

log_parser.debug("parser imports done")

__all__ = ["WikipediaParser"]


@for_all_methods(time_methods)
class WikipediaParser(DataExtractors, WikiCooker, ParserInOut):
    """ Class for parsing the wikipedia page and extracting tags data from it.

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

        log_parser.debug("init parser")

        WikiCooker.__init__(self, protected_vars=protected_vars)
        ParserInOut.__init__(self, protected_vars=protected_vars)

        log_parser.debug("init parser done")

    @warning(log_parser)
    def get_release_date(self):
        """ Gets album release date from information box in the
        top right corner of wikipedia page. Populates:attr:`wiki_music.DATE`

        Raises
        ------
        :exc:`utilities.exceptions.NoReleaseDateException`
            raised if no release date was extracted
        """

        dates = self.sections["infobox"].find(class_="published")

        if dates:
            dates = datefinder.find_dates(dates.get_text())
            date_year = [d.strftime('%Y') for d in dates]
            self.release_date = list(set(date_year))[0]
        else:
            self.release_date = ""
            raise NoReleaseDateException

    @warning(log_parser)
    def get_genres(self):
        """ Gets list of album genres from information box in the
        top right corner of wikipedia page. If found genre if only one then
        assigns is value to :attr:`GENRE`

        Raises
        ------
        :exc:`wiki_music.utilities.exceptions.NoGenreException`
            if no genres could be extracted from page
        """

        genres = self.sections["infobox"].find(class_="category hlist")

        if genres:
            self.genres = [g.string for g in genres.find_all(href=WIKI_GENRES,
                                                             title=True)]
        else:
            self.genres = []
            raise NoGenreException

        # auto select genre if only one was found
        if len(self.genres) == 1:
            self.selected_genre = self.genres[0]

    @warning(log_parser)
    def get_cover_art(self):
        """ Gets album cover art information box in the top right corner
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
            for child in self.sections["infobox"].children:
                if child.find("img") is not None:
                    image = child.find("img")
                    image_url = f"https:{image['src']}"

                    self.cover_art = get_image(image_url)
                    break
            """
            for img in self.sections["infobox"].find_all("img", src=True,
                                                         alt=True):
                if fuzz.token_set_ratio(img["alt"], self.album) > 90:
                    break

            if img:
                self.cover_art = get_image(f"https:{img['src']}")
            else:
                with open(path.join(FILES_DIR, "Na.jpg"), "rb") as f:
                    self.cover_art = bytearray(f.read())
                raise NoCoverArtException("Couldn't extract cover art from "
                                          "wikipedia page")

        Thread(target=cover_art_getter, name="CoverArtGetter").start()

    def get_composers(self):
        """ Extracts composers from wikipedia page. Employs complex logic.
        First Person named entities are extracted by nltk. Then merges them
        with composers. After that uses this list of names to try to guess
        composers and coresponding tracks from short text above the table.

        See also
        --------
        :meth:`get_personnel`
            this method should run first because it populates the
            :attr:`personnel` used by this method

        Warnings
        --------
        This method is not as robust as it should be. It fails for many
        types of formating.
        """

        def check_name_complete(name, text):
            """ Checks if name retrieved fromm text is complete or only part by
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

        # extract names from text using NLTK
        self.extract_names()

        self.NLTK_names = set(self.NLTK_names + self.personnel)

        # get the short comment above the table which is marked as html
        # paragraph with <p>...</p>
        if self.sections["track_listing"][0].name == "p":
            html = self.sections["track_listing"][0].get_text()
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
                for i, tr in enumerate(self.tracks):
                    if caseless_contains(tr, parts[1]):
                        index.append(i)

            # assign composers to tracks
            for name in self.NLTK_names:

                if len(parts) == 2:
                    if caseless_contains(name, parts[1]):
                        n = check_name_complete(name, parts[1])

                        for ind in index:
                            self.composers[ind].append(n)

                if caseless_contains(name, parts[0]):
                    n = check_name_complete(name, parts[0])
                    for i, comp in enumerate(self.composers):
                        if i not in index:
                            if n not in comp:
                                self.composers[i].append(n)

    @warning(log_parser)
    def get_contents(self):
        """ Extract page contets from keys in :attr:`sections` dictionary.
        
        Raises
        ------
        :exc:`wiki_music.utilities.exceptions.NoContentsException`
            if no contents were retrieved
        """

        # the last element is infobox which was added manually
        self.contents = [s.replace("_", " ").capitalize()
                         for s in self.sections.keys()][:-1]

        if len(self.contents) == 0:
            raise NoContentsException

    @warning(log_parser)
    def get_personnel(self):
        """ Extract personnel from wikipedia page sections defined by:
        :const:`wiki_music.constants.parser_const.PERSONNEL_SECTIONS` then
        parse these entries for additional data like apperences on tracks.

        Raises
        ------
        :exc:`wiki_music.utilities.exceptions.NoPersonnelException`
            if no table or list with personnel was found
        """

        personnel = []
        appearences = []
        
        for s in PERSONNEL_SECTIONS:

            if s not in self.sections:
                continue

            for html in self.sections[s]:
                # if the toplevel tag is the list itself
                if html.name in ("ul", "ol"):
                    personnel.extend(self._html2python_list(html))
            
                # if the list is nested inside some other tags
                for h in html.find_all(["ul", "ol"]):
                    personnel.extend(self._html2python_list(h))

        if len(personnel) == 0:
            raise NoPersonnelException

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
            for j, t in enumerate(self.tracks):
                if re.match(t, appear, re.I):
                    appearences[i].append(j)

            # ensure no duplicates
            appearences[i] = list(set(appearences[i]))
            appearences[i] = [a - 1 for a in appearences[i]]
            personnel[i] = person

            #print(person, "|", appear, "|", appearences[i])               

        self.personnel = personnel
        self.appearences = appearences

    @warning(log_parser)
    def _get_tracks(self):
        """ Method that attempts to extract tracklist from table or list
        format on the wikipedia page.

        See also
        --------
        :meth:`_from_table`
            used to parse tracklist in htlm table
        :meth:`_from_list`
            used to parse tracklist in html list
        :meth:`process_tracks`
            method called to parse raw extracted table and get
            song numbers, artists, composers ...

        Raises
        ------
        :exc:`wiki_music.utilities.exceptions.NoTracklistException`
            raised if no tracklist in any format was found
        """

        tables = self.soup.find_all("table", class_="tracklist")

        if tables:
            data = self._from_table(tables)
        else:
            try:
                tables = []
                for s in self.sections["track_listing"]:
                    if s.name in ("ul", "ol"):
                        tables.append(s)
                    else:
                        tables.extend(s.find_all(["ul", "ol"]))
            except AttributeError as e:
                log_parser.warning(e)
                msg = (f"No tracklist found!\nURL: {self.url}\nprobably "
                       f"doesn´t belong to album: {self.album} by {self.band}")
                SharedVars.warning(msg)
                raise NoTracklistException(msg)
            else:
                data = []
                for t in tables:
                    data.extend(self._from_list(t))

        self.process_tracks(data)

    def process_tracks(self, data: List[List[str]]):
        """ Process raw extracted list of tables with trackist for
        track details. """

        self.disk_sep.append(0)

        index = 1
        for CD in data:

            self.disks.append([f"{self.album} CD {index}", len(self)])
            index += 1
            for song in CD:
                if "no" in nc(song[0]):
                    # table header - possibly use in future
                    # posladny stlpec je length a ten väčšinou netreba
                    if "length" in nc(song[-1]):
                        self.header.append(song[:-1])
                    else:
                        self.header.append(song)
                elif re.match(ORDER_NUMBER, song[0]):
                    self.numbers.append(song[0].replace(".", ""))
                    tmp1, tmp2 = self._get_track(song[1])
                    self.tracks.append(tmp1)
                    self.subtracks.append(tmp2)

                    if len(song) > 3:
                        self.artists.append([])
                        self.composers.append([])

                        # all columns between track and track length belong to
                        # artists we assign them to artists or composers
                        # based on label in header
                        for i in range(2, len(song) - 1):
                            a = self._get_artist(song[i])
                            try:
                                is_composer = process.extractOne(
                                    self.header[-1][i], COMPOSER_HEADER,
                                    score_cutoff=90, scorer=fuzz.ratio)
                            except:
                                self.artists[-1].extend(a)
                            else:
                                if is_composer:
                                    self.composers[-1].extend(a)
                                else:
                                    self.artists[-1].extend(a)
                    else:
                        self.artists.append([])
                        self.composers.append([])
                elif "total" in nc(song[0]):
                    # total length summary
                    pass
                else:
                    # if all else passes than line must be disc title
                    self.disks[-1] = [song[0], len(self)]

        # bonus track are sometimes marked as another disc
        disks_filtered = [d for d in self.disks if "bonus" not in nc(d[0])]

        self.disk_sep = [i[1] for i in disks_filtered]
        self.disk_sep.append(len(self))
        self.disks = [i[0] for i in disks_filtered]

        # assign disc number to tracks
        for i, _ in enumerate(self.tracks):
            for j, _ in enumerate(self.disk_sep[:-1]):
                if self.disk_sep[j] <= i and i < self.disk_sep[j + 1]:
                    self.disc_num.append(j + 1)

    def info_tracks(self):
        """ Parse track names for aditional information like
        artist, composer, type... . Also get rid of useless strings like
        bonus track, featuring... . These informations are assumed to be
        enclosed in brackets behind the track name.
        """

        self.types = []
        self.sub_types = []

        comp_flat = flatten_set(self.composers)

        # hladanie umelcov ked su v zatvorke za skladbou
        # + zbavovanie sa bonus track a pod.
        for i, tr in enumerate(self.tracks):

            self.types.append("")
            self.sub_types.append([])

            start_list = [m.start() for m in re.finditer(r'\(', tr)]
            end_list = [m.start() for m in re.finditer(r'\)', tr)]

            for start, end in zip(start_list, end_list):

                self.tracks[i] = re.sub(TO_DELETE, "", tr, re.I)

                artist = re.sub("[,:]", "", tr[start + 1:end])
                artist = re.split(r",|\/|\\", artist)

                for art in artist:
                    for un in UNWANTED:
                        art = re.sub(un, "", art, flags=re.IGNORECASE)

                    # TODO all these maybe should be in the UNWANTED loop??
                    # check against additional personnel
                    for person in self.personnel:
                        if fuzz.token_set_ratio(art, person) > 90:
                            self.artists[i].append(person)
                            self.tracks[i] = self._cut_out(tr, start, end)

                    # check agains composers
                    for comp in comp_flat:
                        if fuzz.token_set_ratio(art, comp) > 90:
                            self.artists[i].append(comp)
                            self.tracks[i] = self._cut_out(tr, start, end)

                    # check if instrumental, ...
                    _type, score = process.extractOne(
                        art, DEF_TYPES, scorer=fuzz.token_sort_ratio)
                    if score > 90:
                        self.types[i] = art  # _type
                        self.tracks[i] = self._cut_out(tr, start, end)

            if self.subtracks:
                for j, sbtr in enumerate(self.subtracks[i]):

                    self.sub_types[i] = [""] * len(sbtr)

                    start_list = [m.start() for m in re.finditer(r'\(', sbtr)]
                    end_list = [m.start() for m in re.finditer(r'\)', sbtr)]

                    for start, end in zip(start_list, end_list):

                        art = re.sub("[,:]", "", sbtr[start + 1:end]).split()

                        for a in art:
                            # check against additional personnel
                            for person in self.personnel:
                                if fuzz.token_set_ratio(a, person) > 90:
                                    self.artists[i].append(person)
                                    sbtr = self._cut_out(sbtr, start, end)
                                    self.subtracks[i][j] = sbtr

                            # check if instrumental, ...
                            _type, score = process.extractOne(
                                a, DEF_TYPES, scorer=fuzz.token_sort_ratio)
                            if score > 90:
                                self.sub_types[i][j] = _type
                                sbtr = self._cut_out(sbtr, start, end)
                                self.subtracks[i][j] = sbtr

    def complete(self):
        """ Recursively traverses: :attr:`composers`, :attr:`artists` and
        :attr:`personnel` and checks each name with each if some is found to be
        incomplete then it is replaced by longer version from other list.
        """ 

        to_complete = (self.composers, self.artists, self.personnel)
        delete: list = ["", " "]

        # complete everything with everything
        for to_replace in to_complete:
            for to_find in to_complete:
                complete_N_dim(to_replace, to_find)

        # sort artist alphabeticaly
        if self.artists:
            for a in self.artists:
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

    def merge_artist_personnel(self):
        """ Assigns personnel which have appearences specified to coresponding
        list of track artists.
        """

        for person, appear in zip(self.personnel, self.appearences):
            for a in appear:
                self.artists[a].append(person)

    def merge_artist_composers(self):
        """ Move all artists to composers list. This is done or left out based
        on user input. """

        for i, (c, a) in enumerate(zip(self.composers, self.artists)):
            self.composers[i] = sorted(list(filter(None, set(c + a))))

        self.artists = [""] * len(self.composers)

    @warning(log_parser, show_GUI=False)
    def extract_names(self):
        """ Used nltk to estract person names from supplied sections of the
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

        document = ""
        for key, value in self.sections.items():

            if key in (PERSONNEL_SECTIONS + ("track_listing", )):
                for val in value:
                    document += val.get_text(" ")

        # if none of the sections is present exit method
        if not document:
            raise NoNames2ExtractException

        stop = NLTK.nltk.corpus.stopwords.words('english')

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
        # and the sunsequent completion messes the right names that were found
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
                          if fuzz.token_set_ratio(n, self.tracks) < 90]

        self.NLTK_names = filtered_names
