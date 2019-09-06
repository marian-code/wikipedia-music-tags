from functools import wraps
from time import sleep

from fuzzywuzzy import process
from lazy_import import lazy_callable, lazy_module

from utilities.loggers import log_parser
from utilities.parser_utils import *  # pylint: disable=unused-wildcard-import
from utilities.sync import SharedVars
from utilities.utils import *  # pylint: disable=unused-wildcard-import
from utilities.wrappers import for_all_methods, time_methods, warning

from . import read_tags, TAGS

nc = normalize_caseless

Thread = lazy_callable("threading.Thread")
Lock = lazy_callable("threading.Lock")
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
NLTK.run_import()  # imports nltk in separate thread

__all__ = ["WikipediaParser"]

settings_dict = yaml_load(os.path.join(module_path(), "settings",
                                       "constants.yml"))
DEF_TYPES = settings_dict["DEF_TYPES"]
UNWANTED = settings_dict["UNWANTED"]
TO_DELETE = settings_dict["TO_DELETE"]
DELIMITERS = settings_dict["DELIMITERS"]
CONTENTS_IDS = settings_dict["CONTENTS_IDS"]
HEADER_CATEGORY = settings_dict["HEADER_CATEGORY"]

colorama_init(autoreset=True)


# TODO doesn't work without GUI
def terminate(message: str):
    SharedVars.ask_exit = message
    SharedVars.wait_exit = True

    while SharedVars.wait_exit:
        sleep(0.05)

    if SharedVars.terminate_app:
        sys.exit()


class DataExtractors:
    """ Extracts various table formats from wikipedia. """

    @classmethod
    def _from_table(cls, tables: list) -> list:

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
    def _from_list(cls, tables: list) -> list:

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

        return data

    @classmethod
    def get_track(cls, data: str) -> (list, list):

        tracks = []
        subtracks = []

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
                if "bonus" in nc(tmp[start + 1:end]):
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


class VariableProxy:
    """ Properties with same names as tags act as a proxy to parser variables
        for convenient access."""

    @property
    def ALBUM(self) -> str:
        return self.album

    @ALBUM.setter
    def ALBUM(self, value: str):
        self.album = value

    @property
    def ALBUMARTIST(self) -> str:
        return self.band

    @ALBUMARTIST.setter
    def ALBUMARTIST(self, value: str):
        self.band = value

    @property
    def ARTIST(self) -> list:
        return self.artists

    @ARTIST.setter
    def ARTIST(self, value: list):
        self.artists = value

    @property
    def COMPOSER(self) -> list:
        return self.composers

    @COMPOSER.setter
    def COMPOSER(self, value: list):
        self.composers = value

    @property
    def DATE(self) -> str:
        return self.release_date

    @DATE.setter
    def DATE(self, value: str):
        self.release_date = value

    @property
    def DISCNUMBER(self) -> list:
        return self.disc_num

    @DISCNUMBER.setter
    def DISCNUMBER(self, value: list):
        self.disc_num = value

    @property
    def GENRE(self) -> str:
        return self.selected_genre

    @GENRE.setter
    def GENRE(self, value: str):
        self.selected_genre = value

    @property
    def LYRICS(self) -> list:
        return self.lyrics

    @LYRICS.setter
    def LYRICS(self, value: list):
        self.lyrics = value

    @property
    def UNSYNCEDLYRICS(self) -> list:
        return self.lyrics

    @UNSYNCEDLYRICS.setter
    def UNSYNCEDLYRICS(self, value: list):
        self.lyrics = value

    @property
    def TITLE(self) -> list:
        return self.tracks

    @TITLE.setter
    def TITLE(self, value: list):
        self.tracks = value

    @property
    def TRACKNUMBER(self) -> list:
        return self.numbers

    @TRACKNUMBER.setter
    def TRACKNUMBER(self, value: list):
        self.numbers = value

    @property
    def FILE(self) -> list:
        return self.files

    @FILE.setter
    def FILE(self, value: list):
        self.files = value

    @property
    def TYPE(self) -> list:
        return self.bracketed_types

    @TYPE.setter
    def TYPE(self, value: list):
        self.bracketed_types = value


@for_all_methods(time_methods, exclude=["Preload"])
class WikiCooker:

    def __init__(self, protected_vars=True):

        # control
        self.wiki_downloaded = False
        self.soup_ready = False
        self.preload_running = False
        self.getter_lock = Lock()
        self.error_msg = None

        self._url = None

        # pass reference of current class instance to subclass
        self.Preload.outer_instance = self

        if protected_vars:
            # variables
            self.album = ""
            self.band = ""
            self.formated_html = None
            self.info_box_html = None
            self.page = None
            self.soup = None

    class Preload:

        _preload_thread = None
        outer_instance = None

        @classmethod
        def start(cls):
            cls.stop()

            cls.outer_instance.wiki_downloaded = False
            cls.outer_instance.soup_ready = False
            cls.outer_instance.error_msg = None

            log_parser.debug(f"Starting wikipedia preload for: "
                             f"{cls.outer_instance.album} by "
                             f"{cls.outer_instance.band}")

            cls._preload_thread = ThreadWithTrace(
                target=cls.outer_instance._preload_run,
                name="WikiPreload")
            cls._preload_thread.start()

        @classmethod
        def stop(cls):

            if cls.outer_instance.preload_running:

                log_parser.debug(f"Stoping wikipedia preload for: "
                                 f"{cls.outer_instance.album} by "
                                 f"{cls.outer_instance.band}")
                cls._preload_thread.kill()
                cls._preload_thread.join()

                cls.outer_instance.preload_running = False

    @property
    def url(self):
        if self._url is None:
            try:
                self._url = str(self.page.url)
            except AttributeError:
                self._url = os.path.join(module_path(), "output", self.album,
                                         'page.pkl')
        return self._url

    def _check_band(self) -> bool:

        try:
            for child in self.info_box_html.children:
                if child.find(href="/wiki/Album") is not None:
                    album_artist = (child
                                    .find(href="/wiki/Album")
                                    .parent.get_text())
                    break

        except AttributeError as e:
            return False
        else:
            if fuzz.token_set_ratio(nc(self.band),
               nc(album_artist)) < 90:
                b = re.sub(r"[Bb]y|[Ss]tudio album", "", album_artist).strip()
                e = (f"The Wikipedia entry for album: {self.album} belongs to "
                     f"band: {b}\nThis probably means that entry for: "
                     f"{self.album} by {self.band} does not exist.")
                print(e)
                log_parser.exception(e)
                terminate(e)

                return False
            else:
                return True  # band found on page matches input

    def _preload_run(self):

        self.preload_running = True

        self.get_wiki(preload=True)

        if not self.error_msg:
            self.cook_soup()

            if not self.error_msg:
                log_parser.info(f"Preload finished successfully, "
                                f"found: {self.url}")

        if self.error_msg:
            log_parser.info(f"Preload unsucessfull: {self.error_msg}")

        self.preload_running = False

    def get_wiki(self, preload=False) -> str:

        # when function is called from application,
        # wait until all preloads are finished and then continue
        if not preload:
            while self.preload_running:
                sleep(0.05)

        if self.wiki_downloaded:
            return self.error_msg

        if SharedVars.offline_debbug:
            return self._from_disk()
        else:
            return self._from_web()

    def _from_web(self) -> str:

        searches = [f"{self.album} ({self.band} album)",
                    f"{self.album} (album)",
                    self.album]

        try:
            for query in searches:
                self.page = wiki.page(title=query, auto_suggest=True)
                summ = nc(self.page.summary)
                if nc(self.band) in summ and nc(self.album) in summ:
                    break
            else:
                self.error_msg = "Could not get wikipedia page."

        except wiki.exceptions.DisambiguationError as e:
            print("Found entries: {}\n...".format("\n".join(e.options[:3])))
            for option in e.options:
                if self.band in option:
                    print(f"\nSelecting: {option}\n")
                    self.page = wiki.page(option)
                    break
            else:
                self.error_msg = ("Couldn't select best album entry "
                                  "from wikipedia")

        except wiki.exceptions.PageError:
            try:
                self.page = wiki.page(f"{self.album} {self.band}")
            except wiki.exceptions.PageError as e:
                self.error_msg = "Album was not found on wikipedia"

        except (wiki.exceptions.HTTPTimeoutError, Exception) as e:
            self.error_msg = ("Search failed probably due to "
                              "poor internet connetion.")
        else:
            self.error_msg = None
            self.wiki_downloaded = True

        return self.error_msg

    def _from_disk(self) -> str:

        fname = os.path.join(module_path(), "output", self.album, 'page.pkl')
        if os.path.isfile(fname):
            with open(fname, 'rb') as infile:
                self.page = pickle.load(infile)
            self.error_msg = None
            self.wiki_downloaded = True
        else:
            self.error_msg = "Cannot find cached offline version of page."

        return self.error_msg

    def cook_soup(self) -> str:

        if self.soup_ready:
            return self.error_msg

        # make BeautifulSoup black magic
        self.soup = BeautifulSoup(self.page.html(), features="lxml")
        self.formated_html = self.soup.get_text()
        self.info_box_html = self.soup.find("table",
                                            class_="infobox vevent haudio")

        # check if the album belongs to band that was requested
        if self._check_band():
            self.soup_ready = True
            self.error_msg = None
        else:
            self.error_msg = "Album doesnt't belong to the requested band"

        return self.error_msg


@for_all_methods(time_methods)
class WikipediaParser(DataExtractors, WikiCooker, VariableProxy):

    def __init__(self, protected_vars=True):

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
        self.release_date = None
        self.selected_genre = None
        self._debug_folder = None

        # atributes protected from GUIs reinit method
        # when new search is started
        WikiCooker.__init__(self, protected_vars=protected_vars)

    def __len__(self):
        return len(self.numbers)

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
                SharedVars.warning = (f"No tracklist found!\nURL: {self.url}"
                                      f"\nprobably doesn´t belong to album: "
                                      f"{self.album} by {self.band}")
                sys.exit()
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

        print(Fore.GREEN + "\nFound files:")
        print(*disk_files, sep="\n")
        print(Fore.GREEN + "\nAssigning files to tracks:")

        for i, tr in enumerate(self.tracks):
            self.tracks[i] = tr.strip()

            for path in disk_files:
                f = os.path.split(path)[1]
                if (nc(wnc(tr)) in nc(f) and nc(self.types[i]) in nc(f)):  # noqa E129

                    print(Fore.LIGHTYELLOW_EX + tr + Fore.RESET,
                          "-" * (1 + max_length - len(tr)) + ">",
                          path)
                    files.append(path)
                    break
            else:
                print(Fore.LIGHTBLUE_EX + tr + Fore.RESET,
                      "." * (2 + max_length - len(tr)),
                      "Does not have a matching file!")

                files.append(None)

        self.files = files

    def data_to_dict(self) -> list:

        if not any(self.files):
            print(Fore.GREEN + "No mathing file was found, "
                  "tags won´t be written")

            return []

        TAGS = TAGS + ("FILE", "TYPE")

        dict_data = []
        for i, _ in enumerate(self.tracks):

            tags = dict()

            for t in TAGS:
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

                if isinstance(getattr(self, key), list):
                    getattr(self, key).append(value)
                else:
                    setattr(self, key, value)

        if self.files:
            # look for aditional artists in brackets behind track names and
            # complete artists names again with new info
            self.info_tracks()

            SharedVars.describe = "Files loaded sucesfully"
        else:
            self.album = ""
            self.band = ""
            self.selected_genre = ""
            self.release_date = ""

            SharedVars.describe = "No music files to Load"

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
