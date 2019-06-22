from time import sleep

from fuzzywuzzy import process
from lazy_import import lazy_callable, lazy_module

from utilities.parser_utils import *
from utilities.utils import *
nc = normalize_caseless

from utilities.loggers import log_parser
from utilities.sync import SharedVars
from utilities.wrappers import warning, time_methods, for_all_methods
from .ID3_tags import read_tags

Thread = lazy_callable("threading.Thread")
fuzz = lazy_callable("fuzzywuzzy.fuzz")
Fore = lazy_callable("colorama.Fore")
BeautifulSoup = lazy_callable("bs4.BeautifulSoup")

datefinder = lazy_module("datefinder")
dt = lazy_module("datetime")
os = lazy_module("os")
re = lazy_module("re")
requests = lazy_module("requests")
sys = lazy_module("sys")
wiki = lazy_module("wikipedia")
pickle = lazy_module("pickle")
NLTK.run_import()  # imports nltk to global variables in separate thread

__all__ = ["WikipediaParser"]


@for_all_methods(time_methods)
class WikipediaParser:

    def __init__(self, protected_vars=True):
        colorama_init()

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
        self.work_dir = None
        self.release_date = None
        self.selected_genre = None
        self._debug_folder = None
        self._url = None

        # atributes protected from GUIs reinit when new search is started
        if protected_vars:
            # control
            self.getting_wiki = False
            self.cooking_soup = False
            self.wiki_downloaded = False
            self.soup_ready = False
            self.preload_running = False
            self.preload_stop = False

            # variables
            self.album = ""
            self.band = ""
            self.formated_html = None
            self.info_box_html = None
            self.page = None
            self.soup = None
            self._files = []

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
            self._debug_folder = os.path.join("output",
                                              win_naming_convetion(self.album,
                                                dir_name=True))

        return self._debug_folder

    @property
    def url(self):
        if self._url is None:
            self._url = self.page.url

        return self._url

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

    # TODO try magic methods
    def __setitem__(self, key, item):
        self.lock.acquire()
        attrs = [self.selected_genre, self.release_date, self.album, self.band,
                 self.numbers, self.tracks, self.types, self.disc_num,
                 self.artists, self.lyrics, self.composers, self.files]

        for i, itm in enumerate(item):
            if isinstance(itm, list):
                attrs[i][key] = itm
            else:
                attrs[i] = itm
        self.lock.release()

    def __getitem__(self, key):
        return [self.selected_genre, self.release_date, self.album, self.band,
                self.numbers[key], self.tracks[key], self.types[key],
                self.disc_num[key], self.artists[key], self.lyrics[key],
                self.composers[key], self.files[key]]

    @warning(log_parser)
    def get_release_date(self):

        for child in self.info_box_html.children:
            if child.find(class_="published") is not None:
                dates = child.find(class_="published")

                dates = datefinder.find_dates(str(dates))
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

                    self.cover_art = requests.get(image_url).content
                    break
            else:
                with open("files/Na.jpg", "rb") as imageFile:
                    f = imageFile.read()
                    self.cover_art = bytearray(f)

        Thread(target=cover_art_getter, name="CoverArtGetter").start()

    def check_band(self) -> bool:

        try:
            for child in self.info_box_html.children:
                if child.find(href="/wiki/Album") is not None:
                    album_artist = (child
                                    .find(href="/wiki/Album")
                                    .parent.get_text())
                    break

        except AttributeError as e:
            print(e)
            log_parser.warning(e)
            SharedVars.warning = e
            return True
        else:
            if fuzz.token_set_ratio(nc(self.band),
               nc(album_artist)) < 90:
                e = ("The Wikipedia entry for album: " + self.album +
                     " belongs to band: " +
                     re.sub(r"[Bb]y|[Ss]tudio album", "",
                            album_artist).strip() +
                     "\nThis probably means that entry for: " +
                     self.album +
                     " by " + self.band + " does not exist.")
                print(e)
                log_parser.warning(e)
                SharedVars.ask_exit = e

                return False
            else:
                return True  # band found on page matches input

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
        delimiters = ["written by", "composed by", "lyrics by", "music by",
                      "arrangements by", "vocal lines by"]

        for sentence in html.split("."):
            for d in delimiters:
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

        # save page object for offline debbug
        fname = os.path.join(self.debug_folder, 'page.pkl')
        with open(fname, 'wb') as output:
            pickle.dump(self.page, output, pickle.HIGHEST_PROTOCOL)

        # save formated html to file
        html = self.soup.prettify()

        fname = os.path.join(self.debug_folder, 'html.txt')
        if not os.path.isfile(fname):
            with open(fname, 'w', encoding='utf8') as outfile:
                outfile.write(html)

        # save html converted to text
        fname = os.path.join(self.debug_folder, 'plain.txt')
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
            SharedVars.warning = e

            contents = []

            ids = ["Track_listing", "Personnel", "Credits", "References"]

            index = 1
            for _id in ids:
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
                if (person.rfind("[", 0,   pos[i]) != -1 and
                   person.find("]", pos[i]) != -1):
                    pass
                # odstranit ak je cislo obsiahnute v nazve skladby
                elif (person.rfind("\"", 0,   pos[i]) != -1 and
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

        # should match strings containing "tracklist"
        tables = self.soup.findAll("table", class_=re.compile("tracklist"))

        self.data_collect = []
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
                rowD = []
                cells = row.findAll(["td", "th"])

                for j, cell in enumerate(cells):
                    # lots of cells span cols and rows so lets deal with that
                    cspan = int(cell.get('colspan', 1))
                    rspan = int(cell.get('rowspan', 1))

                    for k in range(rspan):
                        for l in range(cspan):
                            data[i+k][j+l] += cell.text

                data.append(rowD)

            for i in range(nrows):
                data[i] = list(filter(None, data[i]))
            data = list(filter(None, data))
            self.data_collect.append(data)

        # if tracklist is not in table - fall back to this method of extraction
        if not self.data_collect:

            try:
                tables = self.soup.find(id="Track_listing").parent
            except AttributeError as e:
                print(e)
                log_parser.warning(e)
                SharedVars.warning = ("No tracklist found!\nURL: " +
                                       self.url +
                                       "\nprobably doesn´t belong to album:" +
                                       " " + self.album + " by " + self.band)
                sys.exit()

            table = tables.find_next_sibling("ol")
            if table is None:
                table = tables.find_next_sibling("ul")

            try:
                rows = [ch for ch in table.children if ch.string != "\n"]
            except AttributeError as e:
                print(e)
                log_parser.warning(e)
                SharedVars.warning = ("No tracklist found!\nIt is probaly"
                                       "contained in some unknown format")
                sys.exit()

            data = []
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

            self.data_collect.append(data)

    def process_tracks(self):

        def TR(data):

            tracks = []
            subtracks = []

            # extract tracks and subtracks
            temp = data.split("\n")
            for j, tmp in enumerate(temp):
                if j > 0:
                    # replace " with space, delete empty spaces,
                    # remove numbering if there is any
                    temp[j] = (tmp.replace("\"", "")
                               .strip().split(' ', 1)[1])
                else:
                    temp[j] = tmp.replace("\"", "").strip()

                if "(" in tmp:
                    start = tmp.find("(")
                    end = tmp.find(")", start)
                    # odstranenie zatvoriek s casom
                    if tmp[start + 1:end].replace(":", "").isdigit():
                        temp[j] = tmp[:start] + tmp[end + 1:].strip()
                    # odstranenie bonus track
                    if "bonus" in nc(tmp[start + 1:end]):
                        temp[j] = tmp[:start] + tmp[end + 1:].strip()

            tracks.append(temp[0].strip())
            subtracks.append(temp[1:len(temp)])

            return tracks, subtracks

        def ART(data):
            temp = re.split(",|&", data)
            return [(re.sub(",", "", tmp)).strip() for tmp in temp]

        header_cat = ["lyrics", "text", "music", "compose"]

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
                    tmp1, tmp2 = TR(row[1])
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
                            try:
                                score = process.extractOne(self.header[-1][i],
                                                           header_cat,
                                                           score_cutoff=90,
                                                           scorer=fuzz.ratio)
                                if score:
                                    self.composers[-1].extend(ART(row[i]))
                                else:
                                    self.artists[-1].extend(ART(row[i]))
                            except:
                                self.artists[-1].extend(ART(row[i]))
                    else:
                        self.artists.append([]*1)
                        self.composers.append([]*1)
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

        def_types = ["Instrumental", "Acoustic", "Orchestral", "Live",
                     "Piano Version"]
        unwanted = ["featuring", "feat.", "feat", "narration by", "narration"]
        to_delete = ["bonus track", "bonus"]

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

                for td in to_delete:
                    if td in nc(artist):
                        self.tracks[i] = (tr[:start - 1] +
                                          tr[end + 1:]).strip()
                        break

                artist = re.split(r",|\/|\\", artist)

                for art in artist:
                    for un in unwanted:
                        art = art.replace(un, "").strip()
                        art = art.replace(un.capitalize(), "").strip()

                    # check against additional personnel
                    for person in self.personnel:
                        if fuzz.token_set_ratio(art, person) > 90:
                            self.artists[i].append(person)
                            tr = (tr[:start] + tr[end + 1:])
                            self.tracks[i] = tr.strip()

                    # check agains composers
                    for comp in comp_flat:
                        if fuzz.token_set_ratio(art, comp) > 90:
                            self.artists[i].append(comp)
                            tr = (tr[:start] + tr[end + 1:])
                            self.tracks[i] = tr.strip()

                    # check if instrumental, ...
                    _type, score = process.extractOne(
                        art, def_types, scorer=fuzz.token_sort_ratio)
                    if score > 90:
                        self.types[i] = _type
                        tr = tr[:start] + tr[end + 1:]
                        self.tracks[i] = tr.strip()

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
                                    sbtr = sbtr[:start] + sbtr[end + 1:]
                                    self.subtracks[i][j] = sbtr.strip()

                            # check if instrumental, ...
                            _type, score = process.extractOne(
                                a, def_types, scorer=fuzz.token_sort_ratio)
                            if score > 90:
                                self.sub_types[i][j] = _type
                                sbtr = sbtr[:start] + sbtr[end + 1:]
                                self.subtracks[i][j] = sbtr.strip()

        # get rid of artists duplicates
        for art in self.artists:
            art = sorted(list(set(art)))

    def complete(self):

        to_complete = [self.composers, self.artists, self.personnel]
        unwanted = ["featuring", "feat.", "feat", "naration by"]
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
            for un in unwanted:
                replace_N_dim(tc, un)

    def preload(self):

        if self.album and self.band:
            self.preload_running = True
            self.get_wiki()
            if self.preload_stop:
                self.preload_running = False
                log_parser.debug("Preload aborted")
                return
            self.cook_soup()
            self.preload_running = False
        else:
            log_parser.debug("Input fields empty, aborting preload")

    # TODO implement timeout error
    def get_wiki(self):

        # if GUI already started downloading page wait for finish and than exit
        while self.getting_wiki:
            sleep(0.05)
            if not self.getting_wiki:
                return

        self.getting_wiki = True

        searches = [f"{self.album} ({self.band} album)",
                    f"{self.album} (album)",
                    self.album]

        try:
            for query in searches:
                self.page = wiki.page(title=query, auto_suggest=True)
                summ = nc(self.page.summary)
                if nc(self.band) in summ and nc(self.album) in summ:
                    break

        except wiki.exceptions.DisambiguationError as e:
            print("Found entries: ")
            print("\n".join(e.options[:3]), "\n...")
            for option in e.options:
                if self.band in option:
                    break

            print("\nSelecting: " + option + "\n")
            self.page = wiki.page(option)

        except wiki.exceptions.PageError:
            try:
                self.page = wiki.page(self.album + " " + self.band)
            except wiki.exceptions.PageError as e:
                log_parser.warning(e)
                SharedVars.warning = "Album was not found!!"
                print(Fore.LIGHTYELLOW_EX + "Album was not found!!" +
                      Fore.RESET)
                sys.exit()

        except wiki.exceptions.HTTPTimeoutError as e:
            print(e)
            log_parser.exception(e)
            SharedVars.exception = ("Search failed probably due to"
                                     "poor internet connetion")
            sys.exit()

        self.getting_wiki = False
        self.wiki_downloaded = True

    def cook_soup(self):

        # TODO preparation for preloading
        # if GUI already started downloading page wait for finish and than exit
        while self.cooking_soup:
            sleep(0.05)
            if not self.cooking_soup:
                return

        self.cooking_soup = True

        # make BeautifulSoup black magic
        self.soup = BeautifulSoup(self.page.html(), "lxml")
        self.formated_html = self.soup.get_text()
        self.info_box_html = self.soup.find("table",
                                            class_="infobox vevent haudio")

        # check if the album belongs to band that was requested
        if not self.check_band():
            SharedVars.wait_exit = True
            while SharedVars.wait_exit:
                sleep(0.01)

            # If user wants to terminate program, the GUI
            #  makes the application thread throw exception and exit
            assert not SharedVars.terminate_app

        self.cooking_soup = False
        self.soup_ready = True

    # TODO try asyncio for disk write (https://github.com/Tinche/aiofiles)
    # TODO and for getters 
    def disk_write(self):

        for i, tracklist in enumerate(self.tracklist_2_str(to_file=True), 1):
            fname = os.path.join(self.debug_folder, f"tracklist_{i}.txt")
            with open(fname, "w", encoding="utf-8") as f:
                f.write(tracklist)

        # save found personel to file
        with open(os.path.join(self.debug_folder, "personnel.txt"),
                  "w", encoding="utf8") as f:

            f.write(self.personnel_2_str())

    def tracklist_2_str(self, to_file=True):

        # compute number of spaces
        spaces, length = count_spaces(self.tracks, self.bracketed_types)

        if not to_file:
            G = Fore.GREEN
            LG = Fore.LIGHTGREEN_EX
            R = Fore.RESET
        else:
            G = ""
            LG = ""
            R = ""

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
            s += R

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

        print(Fore.GREEN + "\nFound files:" + Fore.RESET)
        print("\n".join(disk_files), "\n")
        print(Fore.GREEN + "Assigning files to tracks:" + Fore.RESET)

        for i, tr in enumerate(self.tracks):
            self.tracks[i] = tr.strip()

            for path in disk_files:
                f = os.path.split(path)[1]
                if (nc(wnc(tr)) in nc(f) and nc(self.types[i]) in nc(f)):  # noqa E129

                    print(Fore.LIGHTYELLOW_EX + tr + Fore.RESET,
                          "-"*(1 + max_length - len(tr)) + ">",
                          path)
                    files.append(path)
                    break
            else:
                print(Fore.LIGHTBLUE_EX + tr + Fore.RESET,
                      "."*(2 + max_length - len(tr)),
                      "Does not have a matching file!")

                files.append("")

        self.files = files

    def data_to_dict(self):

        file_counter = 0
        dict_data = []
        for i, _ in enumerate(self.tracks):

            if self.files[i] == "" or self.files[i] == " ":
                f = None
                file_counter += 1
            else:
                f = self.files[i]

            dictionary = {
                    "ALBUM": self.album,
                    "ALBUMARTIST": self.band,
                    "ARTIST": self.artists[i],
                    "COMPOSER": self.composers[i],
                    "DATE": self.release_date,
                    "DISCNUMBER": self.disc_num[i],
                    "file": f,
                    "GENRE": self.selected_genre,
                    "LYRICS": self.lyrics[i],
                    "TITLE": self.tracks[i],
                    "TRACKNUMBER": self.numbers[i],
                    "type": self.bracketed_types[i],
                }

            dict_data.append(dictionary)

        if SharedVars.write_json:
            json_dump(dict_data, self.work_dir)
            print("Saved!")

        if file_counter == len(self.tracks):
            print(Fore.GREEN + """No mathing file was found,
                  tags won´t be written""" + Fore.RESET)
            writeable = False
        else:
            writeable = True

        return dict_data, writeable

    def read_files(self):

        self.list_files()

        file_names = []
        artists_data = []
        composers_data = []
        disc_num_data = []
        lyrics_data = []
        numbers_data = []
        tracks_data = []
        for i, fl in enumerate(self.files):
            path, f = os.path.split(fl)
            # match digits, zero or one whitespace characters, zero or one dot
            # zero or one dash, zero or one whitespace characters
            f = re.sub(r"\d\s?\.?-?\s?", "", f)
            file_names.append(os.path.join(path, f))

            (album, band, artists, composers, release_date, disc_num,
             genre, lyrics, track, number) = read_tags(fl)

            # individual tags
            artists_data.append(sorted(re.split(r",\s?", artists)))
            composers_data.append(sorted(re.split(r",\s?", composers)))
            disc_num_data.append(disc_num)
            lyrics_data.append(lyrics)
            numbers_data.append(number)

            if track is "" or track is " " or track is None:
                tracks_data.append(file_names[i])
            else:
                tracks_data.append(track)

        self.artists = artists_data
        self.composers = composers_data
        self.disc_num = disc_num_data
        self.lyrics = lyrics_data
        self.numbers = numbers_data
        self.tracks = tracks_data

        # common tags
        if self.files:
            self.album = album
            self.band = band
            self.selected_genre = genre
            self.release_date = release_date
        else:
            self.album = ""
            self.band = ""
            self.selected_genre = ""
            self.release_date = ""

        # look for aditional artists in brackets behind track names and
        # complete artists names again with new info
        self.info_tracks()

        if not self.files:
            SharedVars.describe = "No music files to Load"
        else:
            SharedVars.describe = "Files loaded sucesfully"

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

if __name__ == "__main__":
    pass
