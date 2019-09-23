from fuzzywuzzy import process
from lazy_import import lazy_callable, lazy_module

from wiki_music import GUI_RUNNING
from wiki_music.constants.colors import GREEN, LBLUE, LGREEN, LYELLOW, RESET
from wiki_music.constants.parser_const import *
from wiki_music.constants.tags import EXTENDED_TAGS
from wiki_music.utilities import (NoTracklistException, SharedVars,
                                  for_all_methods, get_image, log_parser,
                                  time_methods, warning)
from wiki_music.utilities.parser_utils import *  # pylint: disable=unused-wildcard-import
from wiki_music.utilities.utils import *  # pylint: disable=unused-wildcard-import

from ..ID3_tags import read_tags, write_tags
from .extractors import DataExtractors
from .preload import WikiCooker
from .proxy import VariableProxy

nc = normalize_caseless

Thread = lazy_callable("threading.Thread")
fuzz = lazy_callable("fuzzywuzzy.fuzz")
find_dates = lazy_callable("datefinder.find_dates")
Parallel = lazy_callable("joblib.Parallel")
delayed = lazy_callable("joblib.delayed")

os = lazy_module("os")
re = lazy_module("re")
pickle = lazy_module("pickle")
NLTK.run_import()  # imports nltk in separate thread

__all__ = ["WikipediaParser"]

colorama_init(autoreset=True)


@for_all_methods(time_methods)
class WikipediaParser(DataExtractors, WikiCooker, VariableProxy):

    def __init__(self, protected_vars=True):

        # atributes protected from GUIs reinit method
        # when new search is started
        WikiCooker.__init__(self, protected_vars=protected_vars)
        VariableProxy.__init__(self)

        # lists 1D
        self.contents = []
        self.tracks = []
        self.types = []
        self.disc_num = []
        self.disk_sep = []
        self.disks = []
        self.genres = []
        self.header = []
        self.lyrics = []
        self.NLTK_names = []
        self.numbers = []
        self.personnel = []
        self._bracketed_types = []

        # lists 2D
        self.appearences = []
        self.artists = []
        self.composers = []
        self.sub_types = []
        self.subtracks = []
        self.data_collect = None

        # bytearray
        self.cover_art = None

        # strings
        if protected_vars:
            self.work_dir = None
            self.log = MultiLog(log_parser)
        self.release_date = None
        self.selected_genre = None
        self._debug_folder = None

    def __len__(self):
        return len(self.numbers)

    def __bool__(self):
        return self.__len__()

    @property
    def bracketed_types(self):
        if not self._bracketed_types:
            self._bracketed_types = bracket(self.types)
            return self._bracketed_types
        else:
            return self._bracketed_types

    @property
    def debug_folder(self):
        if self._debug_folder is None:
            _win_name = win_naming_convetion(self.album, dir_name=True)
            self._debug_folder = os.path.join("output", _win_name)

        return self._debug_folder

    @property
    def files(self):
        if len(self._files) < len(self.tracks):
            self.reassign_files()

        return self._files

    @files.setter
    def files(self, files):
        self._files = files

    def list_files(self):
        self.files = list_files(self.work_dir)

    @warning(log_parser)
    def get_release_date(self):

        for child in self.info_box_html.children:
            if child.find(class_="published") is not None:
                dates = child.find(class_="published")

                dates = find_dates(str(dates))
                date_year = [d.strftime('%Y') for d in dates]
                date_year = list(set(date_year))

                self.release_date = date_year[0]
                break
        else:
            self.release_date = ""

    @warning(log_parser)
    def get_genres(self):

        for child in self.info_box_html.children:
            if child.find(class_="category hlist") is not None:
                genres_html = child.find(class_="category hlist")

                # match "/wiki/SOMETHING" where SOMWETHING is not Music_genre
                ref = re.compile(r"/wiki/(?!Music_genre)")
                gndr = (genres_html.findAll(href=ref))
                self.genres = [g.string for g in gndr]
                break
        else:
            self.genres = []

    @warning(log_parser)
    def get_cover_art(self):

        # self.cover_art is not protected by lock, parser shoul have more than
        # enough time to get it before GUI requests it
        def cover_art_getter():

            for child in self.info_box_html.children:
                if child.find("img") is not None:
                    image = child.find("img")
                    image_url = f"https:{image['src']}"

                    self.cover_art = get_image(image_url)
                    break
            else:
                with open("files/Na.jpg", "rb") as imageFile:
                    f = imageFile.read()
                    self.cover_art = bytearray(f)

        Thread(target=cover_art_getter, name="CoverArtGetter").start()

    def get_composers(self):

        def check_name_complete(name, text):

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
        try:
            self.extract_names()
        except Exception as e:
            print(e)
            log_parser.exception(e)
            SharedVars.exception = e
            self.NLTK_names = []

        self.NLTK_names = set(self.NLTK_names + self.personnel)

        start = self.soup.find("span", class_="mw-headline",
                               id="Track_listing")
        end = start.find_next("table", class_="tracklist")

        def loop_until(text, firstElement):
            try:
                text += firstElement.get_text()
            except AttributeError:
                pass
            if (firstElement.next.next == end):
                return text
            else:
                # Using double next to skip the string nodes themselves
                return loop_until(text, firstElement.next)

        html = loop_until('', start)
        html = re.sub(r"\[edit\]", "", html)
        html = normalize(html)

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

    def basic_out(self):

        os.makedirs(self.debug_folder, exist_ok=True)

        # save page object for offline debbug
        fname = os.path.join(self.debug_folder, 'page.pkl')
        with open(fname, 'wb') as output:
            pickle.dump(self.page, output, pickle.HIGHEST_PROTOCOL)

        # save formated html to file
        html = self.soup.prettify()
        fname = os.path.join(self.debug_folder, 'page.html')
        if not os.path.isfile(fname):
            with open(fname, 'w', encoding='utf8') as outfile:
                outfile.write(html)

        # save html converted to text
        fname = os.path.join(self.debug_folder, 'page.txt')
        if not os.path.isfile(fname):
            with open(fname, 'w', encoding='utf8') as outfile:
                outfile.write(self.formated_html)

    def get_contents(self):

        contents = self.soup.find("div", class_="toc")
        try:
            contents = contents.get_text()
        except AttributeError as e:
            print(e)
            log_parser.warning(e)
            SharedVars.warning = str(e)

            contents = []

            index = 1
            for _id in CONTENTS_IDS:
                if self.soup.find(class_="mw-headline", id=_id) is not None:
                    self.contents.append(_id)
                    contents.append(f"{index} {_id}")
                    index += 1

        else:
            contents = contents.split("\n")
            contents = list(filter(None, contents))

            if "Contents" in contents[0]:
                contents.pop(0)

            for item in contents:
                if len(re.findall(r'\d+', item)) > 1:
                    item = f"   {item}"
                else:
                    self.contents.append(item.split(' ', 1)[1])

    def get_personnel(self):

        for i, item in enumerate(self.contents):
            if "personnel" in nc(item):
                stop = self.contents[i + 1]
                break
            elif "credits" in nc(item):
                stop = self.contents[i + 1]
                break
        else:
            # if pos is not initialized this means
            # that there is no additional presonel
            # entry on the page. Thus no info can
            # be retrieved and the function exits
            return [], []

        start = int(self.formated_html.find("\nPersonnel"))
        if start == -1:
            start = int(self.formated_html.find("\nCredits"))

        end = int(self.formated_html.find("\n" + stop, start))

        self.personnel = self.formated_html[start:end]
        self.personnel = self.personnel.split("\n")

        f = [" (", " | "]
        for it, person in enumerate(self.personnel):
            p = normalize(person)
            p = re.sub('[^A-Za-z0-9 ()]+', '|', p)
            pos = 100
            for i in f:
                if i in p:
                    if(p.find(i) < pos and p.find(i) > 0):
                        pos = p.find(i)

            if(pos == 100):
                self.personnel[it] = ""
            else:
                self.personnel[it] = person[:pos].strip()

            # tu su cisla od 1 ale cislovanie list numbers
            # zacina od nuly - treba o 1 posunut
            temp = list(re.findall(r'\d+', person))
            pos = [m.start() for m in re.finditer(r'\d+', person)]

            temp_new = []
            for i, tmp in enumerate(temp):
                # zbavit sa cisel referencii
                if (person.rfind("[", 0, pos[i]) != -1 and
                   person.find("]", pos[i]) != -1):
                    pass
                # odstranit ak je cislo obsiahnute v nazve skladby
                elif (person.rfind("\"", 0, pos[i]) != -1 and
                      person.find("\"", pos[i]) != -1):
                    pass
                else:
                    temp_new.append(tmp)

            temp = [int(t) - 1 for t in temp_new]

            for i, tr in enumerate(self.tracks):
                if fuzz.token_set_ratio(tr, person) > 90:
                    temp.append(str(i))

            if temp and temp is not None:
                self.appearences.append(temp)
            else:
                self.appearences.append([])

        # delete empty list entries
        temp_p = []
        temp_a = []

        for i, person in enumerate(self.personnel):
            self.personnel[i] = (person
                                 .encode('utf-8', 'ignore').decode("utf-8"))
            if person != "":
                temp_p.append(person)
                temp_a.append(self.appearences[i])

        # delete duplicates
        self.personnel = []
        self.appearences = []

        for tp, ta in zip(temp_p, temp_a):
            if tp not in self.personnel:
                self.personnel.append(tp)
                self.appearences.append(ta)
            else:
                for i, person in enumerate(self.personnel):
                    if tp in person:
                        if not ta:
                            self.appearences[i].extend(ta)

        num_length = len(self.numbers)
        for i, app in enumerate(self.appearences):
            self.appearences[i] = list(map(int, app))
        for i, app in enumerate(self.appearences):
            self.appearences[i] = list(filter(lambda x: x <= num_length, app))

    def get_tracks(self):

        tables = self.soup.findAll("table", class_="tracklist")

        if tables is not None:
            self.data_collect = self._from_table(tables)
        else:
            try:
                tables = self.soup.find(id="Track_listing").parent
            except AttributeError as e:
                print(e)
                log_parser.warning(e)
                msg = (f"No tracklist found!\nURL: {self.url}\nprobably "
                       f"doesn´t belong to album: {self.album} by {self.band}")
                SharedVars.warning = msg
                raise NoTracklistException(msg)
            else:
                self.data_collect = self._from_list(tables)

    def process_tracks(self):

        self.disk_sep.append(0)

        index = 1
        for CD_data in self.data_collect:

            self.disks.append([f"{self.album} CD {index}", len(self.numbers)])
            index += 1
            for row in CD_data:
                if "no" in nc(row[0]):
                    # table header - possibly use in future
                    # posladny stlpec je length a ten väčšinou netreba
                    if "length" in nc(row[-1]):
                        self.header.append(row[:-1])
                    else:
                        self.header.append(row)
                elif row[0].replace(".", "").isdigit():
                    self.numbers.append(row[0].replace(".", ""))
                    tmp1, tmp2 = self.get_track(row[1])
                    self.tracks.extend(tmp1)
                    self.subtracks.extend(tmp2)

                    cols = len(row)
                    if cols > 3:
                        self.artists.append([])
                        self.composers.append([])

                        # all columns between track and track length belong to
                        # artists we assign them to artists or composers
                        # based on label in header
                        for i in range(2, cols - 1):
                            a = self.get_artist(row[i])
                            try:
                                score = process.extractOne(self.header[-1][i],
                                                           HEADER_CATEGORY,
                                                           score_cutoff=90,
                                                           scorer=fuzz.ratio)
                            except:
                                self.artists[-1].extend(a)
                            else:
                                if score:
                                    self.composers[-1].extend(a)
                                else:
                                    self.artists[-1].extend(a)
                    else:
                        self.artists.append([] * 1)
                        self.composers.append([] * 1)
                elif "total" in nc(row[0]):
                    # total length summary
                    pass
                else:
                    # if all else passes than line must be disc title
                    self.disks[-1] = [row[0], len(self.numbers)]

        # bonus track are sometimes marked as another disc
        disks_filtered = [d for d in self.disks if "bonus" not in nc(d[0])]

        self.disk_sep = [i[1] for i in disks_filtered]
        self.disk_sep.append(len(self.numbers))
        self.disks = [i[0] for i in disks_filtered]

        # assign disc number to tracks
        for i, _ in enumerate(self.tracks):
            for j, _ in enumerate(self.disk_sep[:-1]):
                if self.disk_sep[j] <= i and i < self.disk_sep[j + 1]:
                    self.disc_num.append(j + 1)

    def info_tracks(self):

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

                artist = re.sub("[,:]", "", tr[start + 1:end])

                for td in TO_DELETE:
                    if td in nc(artist):
                        self.tracks[i] = self.cut_out(tr, start, end)
                        break

                artist = re.split(r",|\/|\\", artist)

                for art in artist:
                    for un in UNWANTED:
                        art = re.sub(un, "", art, flags=re.IGNORECASE)

                    # check against additional personnel
                    for person in self.personnel:
                        if fuzz.token_set_ratio(art, person) > 90:
                            self.artists[i].append(person)
                            self.tracks[i] = self.cut_out(tr, start, end)

                    # check agains composers
                    for comp in comp_flat:
                        if fuzz.token_set_ratio(art, comp) > 90:
                            self.artists[i].append(comp)
                            self.tracks[i] = self.cut_out(tr, start, end)

                    # check if instrumental, ...
                    _type, score = process.extractOne(
                        art, DEF_TYPES, scorer=fuzz.token_sort_ratio)
                    if score > 90:
                        self.types[i] = art  # _type
                        self.tracks[i] = self.cut_out(tr, start, end)

            if self.subtracks:
                for j, sbtr in enumerate(self.subtracks[i]):

                    self.sub_types[i] = [""] * len(sbtr)

                    start_list = [m.start() for m in re.finditer(r'\(', sbtr)]
                    end_list = [m.start() for m in re.finditer(r'\)', sbtr)]

                    for start, end in zip(start_list, end_list):

                        art = re.sub("[,:]", "", sbtr[start + 1:end])
                        art = art.split(" ")

                        for a in art:
                            # check against additional personnel
                            for person in self.personnel:
                                if fuzz.token_set_ratio(a, person) > 90:
                                    self.artists[i].append(person)
                                    sbtr = self.cut_out(sbtr, start, end)
                                    self.subtracks[i][j] = sbtr

                            # check if instrumental, ...
                            _type, score = process.extractOne(
                                a, DEF_TYPES, scorer=fuzz.token_sort_ratio)
                            if score > 90:
                                self.sub_types[i][j] = _type
                                sbtr = self.cut_out(sbtr, start, end)
                                self.subtracks[i][j] = sbtr

    def complete(self):

        to_complete = [self.composers, self.artists, self.personnel]
        delete = ["", " "]

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

    def disk_write(self):

        for i, tracklist in enumerate(self.tracklist_2_str(to_file=True), 1):
            fname = os.path.join(self.debug_folder, f"tracklist_{i}.txt")
            with open(fname, "w", encoding="utf-8") as f:
                f.write(tracklist)

        # save found personel to file
        with open(os.path.join(self.debug_folder, "personnel.txt"),
                  "w", encoding="utf8") as f:

            f.write(self.personnel_2_str())

    def tracklist_2_str(self, to_file=True) -> list:

        def _set_color():
            if to_file:
                return [""] * 3
            else:
                return GREEN, LGREEN, RESET

        # compute number of spaces
        spaces, length = count_spaces(self.tracks, self.bracketed_types)

        G, LG, R = _set_color()

        # convert to string
        tracklists = []
        for j, (ds, hd) in enumerate(zip(self.disks, self.header)):
            s = ""
            s += f"{G}\n{j + 1}. Disk:{R} {ds}"
            if len(hd) >= 2:
                s += f" {LG}{hd[0]} {hd[1]}"
            if len(hd) >= 3:
                s += f"{' '*(length + len(hd[1]))}{hd[2]}"
            if len(hd) >= 4:
                s += f", {hd[3]}"
            s += f"{R}\n"

            for i in range(self.disk_sep[j], self.disk_sep[j + 1]):
                s += (f"{self.numbers[i]:>2}. {self.tracks[i]} "
                      f"{self.bracketed_types[i]}{spaces[i]} "
                      f"{', '.join(self.artists[i] + self.composers[i])}\n")

                for k, (sbtr, sbtp) in enumerate(zip(self.subtracks[i],
                                                     self.sub_types[i])):
                    s += (f"  {write_roman(k + 1)}. {sbtr} {sbtp}\n")

            tracklists.append(s)

        return tracklists

    def print_tracklist(self):
        print("\n".join(self.tracklist_2_str(to_file=False)))

    def personnel_2_str(self):

        s = ""
        if not self.personnel:
            s += "---\n"

        for pers, app in zip(self.personnel, self.appearences):

            if app:
                s += pers + " - "
                temp = 50

                for k, a in enumerate(app):
                    for j, _ in enumerate(self.disk_sep[:-1]):

                        if (a > self.disk_sep[j] and
                            a < self.disk_sep[j + 1]):  # noqa E129

                            if j != temp:
                                s += f"{self.disks[j]}: {self.numbers[a]}"
                                temp = j
                            else:
                                s += self.numbers[a]

                            if k != len(app) - 1:
                                s += ", "
                            break
                    else:
                        continue

                s += u'\n'
            else:
                s += pers + u'\n'

        return s

    def merge_artist_personnel(self):

        for person, appear in zip(self.personnel, self.appearences):
            for a in appear:
                self.artists[a].append(person)

    def reassign_files(self):

        wnc = win_naming_convetion
        max_length = len(max(self.tracks, key=len))

        # write data to ID3 tags
        disk_files = list_files(self.work_dir)
        files = []

        print(GREEN + "\nFound files:")
        print(*disk_files, sep="\n")
        print(GREEN + "\nAssigning files to tracks:")

        for i, tr in enumerate(self.tracks):
            self.tracks[i] = tr.strip()

            for path in disk_files:
                f = os.path.split(path)[1]
                if (nc(wnc(tr)) in nc(f) and nc(self.types[i]) in nc(f)):  # noqa E129

                    print(LYELLOW + tr + RESET,
                          "-" * (1 + max_length - len(tr)) + ">", path)
                    files.append(path)
                    break
            else:
                print(LBLUE + tr + RESET, "." * (2 + max_length - len(tr)),
                      "Does not have a matching file!")

                files.append(None)

        self.files = files

    def data_to_dict(self) -> list:

        dict_data = []
        for i, _ in enumerate(self.tracks):

            tags = dict()

            for t in EXTENDED_TAGS:
                attr = getattr(self, t)
                if isinstance(attr, list):
                    tags[t] = attr[i]
                else:
                    tags[t] = attr

            dict_data.append(tags)

        if SharedVars.write_json:
            yaml_dump(dict_data, self.work_dir)
            print("Saved YAML file")

        return dict_data

    def read_files(self):

        # initialize variables
        self.__init__(protected_vars=False)

        self.list_files()

        for fl in self.files:

            for key, value in read_tags(fl).items():

                # TODO need more elegant way to avoid this difference
                # between read tags and parser attributes
                if key == "COMMENT":
                    continue

                if isinstance(getattr(self, key), list):
                    getattr(self, key).append(value)
                else:
                    setattr(self, key, value)

        if self.files:
            # look for aditional artists in brackets behind track names and
            # complete artists names again with new info
            self.info_tracks()

            self.log.info("Files loaded sucesfully")
        else:
            self.album = ""
            self.band = ""
            self.selected_genre = ""
            self.release_date = ""

            self.log.info("No music files to Load")

    def extract_names(self):

        # pass to NLTK only relevant part of page
        for item in self.contents:
            if "references" in nc(item):
                stop = item
                break
        else:
            stop = self.contents[-1]

        start = self.formated_html.find("\nTrack listing")
        end = self.formated_html.find(f"\n{stop}")
        document = self.formated_html[start:end]

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

    def write_tags(self, lyrics_only: bool=False) -> bool:

        if not any(self.files):
            return False
        else:
            # for data in self.data_to_dict():
            #     write_tags(data, lyrics_only=lyrics_only)

            Parallel(n_jobs=len(self), prefer="threads")(
                delayed(write_tags)(data, lyrics_only=lyrics_only)
                for data in self.data_to_dict())

            return True
