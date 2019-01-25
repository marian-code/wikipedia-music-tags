import package_setup
import lazy_import

from utils import (colorama_init, count_spaces, delete_N_dim, find_N_dim,
                   json_dump, list_files, normalize, normalize_caseless,
                   replace_N_dim, write_roman, bracket, win_naming_convetion,
                   caseless_contains, flatten_set)

from fuzzywuzzy import process
from wiki_music import shared_vars, log_parser

fuzz = lazy_import.lazy_callable("fuzzywuzzy.fuzz")
Fore = lazy_import.lazy_callable("colorama.Fore")
BeautifulSoup = lazy_import.lazy_callable("bs4.BeautifulSoup")
read_tags = lazy_import.lazy_callable("libb.ID3_tags.read_tags")

codecs = lazy_import.lazy_module("codecs")
datefinder = lazy_import.lazy_module("datefinder")
dt = lazy_import.lazy_module("datetime")
nltk = lazy_import.lazy_module("nltk")
os = lazy_import.lazy_module("os")
re = lazy_import.lazy_module("re")
requests = lazy_import.lazy_module("requests")
sys = lazy_import.lazy_module("sys")
time = lazy_import.lazy_module("time")
warnings = lazy_import.lazy_module("warnings")
wiki = lazy_import.lazy_module("wikipedia")
pickle = lazy_import.lazy_module("pickle")
functools = lazy_import.lazy_module("functools")

warnings.filterwarnings('ignore', '.*code.*', )


def warning(function):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except AttributeError as e:
            print(e)
            log_parser.warning(e)
            shared_vars.warning = e
        except Exception as e:
            print(e)
            log_parser.warning(e)
            shared_vars.warning = e

    return wrapper


class wikipedia_parser:

    def __init__(self):
        colorama_init()

        # define variables
        self.album = None
        self.appearences = []
        self.artists = []
        self.band = None
        self.bracketed_types = []
        self.composers = []
        self.contents = []
        self.disc_num = []
        self.disk_sep = []
        self.disks = []
        self.files = []
        self.formated_html = None
        self.genres = None
        self.header = []
        self.lyrics = []
        self.NLTK_names = []
        self.numbers = []
        self.page = None
        self.personnel = []
        self.raw_html = None
        self.release_date = None
        self.selected_genre = None
        self.soup = None
        self.sub_types = []
        self.subtracks = []
        self.composers = []
        self.tracks = []
        self.types = []
        self.cover_art = None

        # misc
        self.url = None
        self.work_dir = None
        self.info_box_html = None
        self.data_collect = None
        self.contents_raw = []
        self.debug_folder = None
        self.cover_art_file = None

        # TODO control
        # self.lock = Lock()

    @warning
    def RELEASE_DATE(self):

        self.release_date = ""

        for child in self.info_box_html.children:
            if child.find(class_="published") is not None:
                dates = child.find(class_="published")
                break

        dates = datefinder.find_dates(str(dates))

        date_year = [d.strftime('%Y') for d in dates]
        date_year = list(set(date_year))

        self.release_date = date_year[0]

    @warning
    def GENRES(self):

        self.genres = []

        for child in self.info_box_html.children:
            if child.find(class_="category hlist") is not None:
                genres_html = child.find(class_="category hlist")
                break

        # match "/wiki/SOMETHING" where SOMWETHING is not Music_genre
        gndr = (genres_html.findAll(href=re.compile(r"/wiki/(?!Music_genre)")))
        g = [g.string for g in gndr]

        self.genres = g

    @warning
    def COVER_ART(self):

        try:
            for child in self.info_box_html.children:
                if child.find("img") is not None:
                    image = child.find("img")
                    break

            image_url = "https:{}".format(image["src"])

            self.cover_art = requests.get(image_url).content
        except NameError:
            with open("files/Na.jpg", "rb") as imageFile:
                f = imageFile.read()
                self.cover_art = bytearray(f)

    def check_BAND(self) -> bool:

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
            shared_vars.warning = e
            return True
        else:
            if fuzz.token_set_ratio(normalize_caseless(self.band),
               normalize_caseless(album_artist)) < 90:
                e = ("The Wikipedia entry for album: " + self.album +
                     " belongs to band: " +
                     re.sub(r"[Bb]y|[Ss]tudio album", "",
                            album_artist).strip() +
                     "\nThis probably means that entry for: " +
                     self.album +
                     " by " + self.band + " does not exist.")
                print(e)
                log_parser.warning(e)
                shared_vars.ask_exit = e

                return False
            else:
                return True  # band found on page matches input

    def COMPOSERS(self):

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
            shared_vars.exception = e
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

    def BASIC_OUT(self):

        # save page object for offline debbug
        fname = os.path.join(self.debug_folder, 'page.pkl')
        with open(fname, 'wb') as output:
            pickle.dump(self.page, output, pickle.HIGHEST_PROTOCOL)

        # save formated html to file
        self.raw_html = self.soup.prettify()

        fname = os.path.join(self.debug_folder, 'html.txt')
        if not os.path.isfile(fname):
            with open(fname, 'w', encoding='utf8') as file:
                file.write(self.raw_html)

        # save html converted to text
        self.formated_html = self.soup.get_text()

        fname = os.path.join(self.debug_folder, 'plain.txt')
        if not os.path.isfile(fname):
            with open(fname, 'w', encoding='utf8') as file:
                file.write(self.formated_html)

    def CONTENTS(self):

        self.contents = self.soup.find("div", class_="toc")
        try:
            self.contents = self.contents.get_text()
        except AttributeError as e:
            print(e)
            log_parser.warning(e)
            shared_vars.warning = e

            self.contents = []
            self.contents_raw = []

            ids = ["Track_listing", "Personnel", "Credits", "References"]

            index = 1
            for _id in ids:
                if self.soup.find(class_="mw-headline", id=_id) is not None:
                    self.contents_raw.append(_id)
                    self.contents.append("{} {}".format(index, _id))
                    index += 1

        else:
            self.contents = self.contents.split("\n")
            self.contents = list(filter(None, self.contents))

            if "Contents" in self.contents[0]:
                self.contents.pop(0)

            self.contents_raw = []
            for item in self.contents:
                if len(re.findall(r'\d+', item)) > 1:
                    item = "   " + item
                else:
                    self.contents_raw.append(item.split(' ', 1)[1])

    def PERSONNEL(self):

        stop = None
        for i, item in enumerate(self.contents_raw):
            if "personnel" in normalize_caseless(item):
                stop = self.contents_raw[i + 1]
                break
            elif "credits" in normalize_caseless(item):
                stop = self.contents_raw[i + 1]
                break

        # if pos is not initialized this means
        # that there is no additional presonel
        # entry on the page. Thus no info can
        # be retrieved and the function exits
        if stop is None:
            return [], []

        start = int(self.formated_html.find("\nPersonnel"))
        if start == -1:
            start = int(self.formated_html.find("\nCredits"))

        end = int(self.formated_html.find("\n" + stop, start))

        self.personnel = self.formated_html[start:end]

        self.appearences = []
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

            temp = list(map(int, temp_new))
            temp = [i - 1 for i in temp]

            for i, tr in enumerate(self.tracks):
                if fuzz.token_set_ratio(tr, person) > 90:
                    temp.append(str(i))

            if len(temp) > 0 and temp is not None:
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

        for i in range(len(self.appearences)):
            self.appearences[i] = list(map(int, self.appearences[i]))
            self.appearences[i] = list(filter(lambda x: x <= int(len(self.numbers)), self.appearences[i]))

    def TRACKS(self):

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
        if len(self.data_collect) == 0:

            try:
                tables = self.soup.find(id="Track_listing").parent
            except AttributeError as e:
                print(e)
                log_parser.warning(e)
                shared_vars.warning = ("No tracklist found!\nURL: " +
                                       self.url +
                                       "\nprobably doesn´t belong to album:" +
                                       " " + self.album + " by " + self.band)
                sys.exit()

            table = tables.find_next_sibling("ol")
            if table is None:
                table = tables.find_next_sibling("ul")

            try:
                rows = []
                for child in table.children:
                    if child.string != "\n":
                        rows.append(child.string)
            except AttributeError as e:
                print(e)
                log_parser.warning(e)
                shared_vars.warning = ("No tracklist found!\nIt is probaly"
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

    # TODO probably not used
    def __clear_ref__(self, data: list) -> list:

        # odstranenie referencii
        for i, d in enumerate(data):
            if "[" in d:
                start = d.find("[")
                end = d.find("]", start)
                # max dvojciferne referencie zaporne je vtedy ak sa nenajde ]
                if end - start < 4 and end - start > 0:
                    data[i] = d[:start].strip()

        return data

    def process_TRACKS(self):

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
                        temp[j] = tmp[:start] + tmp[end + 1:]
                        temp[j] = tmp.strip()
                    # odstranenie bonus track
                    if "bonus" in normalize_caseless(tmp[start + 1:end]):
                        temp[j] = tmp[:start] + tmp[end + 1:]
                        temp[j] = tmp.strip()

            tracks.append(temp[0].strip())
            subtracks.append(temp[1:len(temp)])

            return tracks, subtracks

        def ART(data):
            temp = re.split(",|&", data)
            for j, tmp in enumerate(temp):
                temp[j] = (re.sub(",", "", tmp)).strip()

            return temp

        header_cat = ["lyrics", "text", "music", "compose"]

        self.disk_sep.append(0)

        index = 1
        for CD_data in self.data_collect:

            self.disks.append([self.album + " CD " +
                               str(index), len(self.numbers)])
            index += 1
            for row in CD_data:
                if "no" in normalize_caseless(row[0]):
                    # table header - possibly use in future
                    # posladny stlpec je length a ten väčšinou netreba
                    if "length" in normalize_caseless(row[-1]):
                        self.header.append(row[:-1])
                    else:
                        self.header.append(row)
                elif row[0].replace(".", "").isdigit() is True:
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
                                if score is True:
                                    self.composers[-1].extend(ART(row[i]))
                                else:
                                    self.artists[-1].extend(ART(row[i]))
                            except:
                                self.artists[-1].extend(ART(row[i]))
                    else:
                        self.artists.append([]*1)
                        self.composers.append([]*1)
                elif "total" in normalize_caseless(row[0]):
                    # total length summary
                    pass
                else:
                    # if all else passes than line must be disc title
                    self.disks[-1] = [row[0], len(self.numbers)]

        # bonus track are sometimes marked as another disc
        disks_filtered = []
        for disc in self.disks:
            if "bonus" not in normalize_caseless(disc[0]):
                disks_filtered.append(disc)

        self.disk_sep = [i[1] for i in disks_filtered]
        self.disk_sep.append(len(self.numbers))
        self.disks = [i[0] for i in disks_filtered]

        # assign disc number to tracks
        for i, _ in enumerate(self.tracks):
            for j, _ in enumerate(self.disk_sep[:-1]):
                if self.disk_sep[j] <= i and i < self.disk_sep[j + 1]:
                    self.disc_num.append(j + 1)

    def info_TRACKS(self):

        # TODO restructure
        def_types = ["Instrumental",
                     "Acoustic",
                     "Orchestral",
                     "Live",
                     "Piano Version"]
        # TODO not covering capitalized versions
        unwanted = ["featuring", "feat.", "feat", "narration by", "narration"]
        to_delete = ["bonus track", "bonus"]

        self.types = []
        self.sub_types = []

        comp_flat = flatten_set(self.composers)

        # hladanie umelcov ked su v zatvorke za skladbou
        # + zbavovanier sa bonus track a pod.
        for j, tr in enumerate(self.tracks):

            self.types.append("")
            self.sub_types.append([])

            if "(" in tr:

                start_list = [m.start() for m in re.finditer(r'\(', tr)]
                end_list = [m.start() for m in re.finditer(r'\)', tr)]

                for start, end in zip(start_list, end_list):

                    artist = re.sub("[,:]", "", tr[start + 1:end])

                    for td in to_delete:
                        if td in normalize_caseless(artist):
                            self.tracks[j] = (tr[:start - 1] +
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
                                self.artists[j].append(person)
                                self.tracks[j] = (tr[:start] + tr[end + 1:])
                                self.tracks[j] = tr.strip()

                        # check agains composers
                        for comp in comp_flat:
                            if fuzz.token_set_ratio(art, comp) > 90:
                                self.artists[j].append(comp)
                                self.tracks[j] = (tr[:start] + tr[end + 1:])
                                self.tracks[j] = tr.strip()

                        # check if instrumental, ...
                        for typ in def_types:
                            if fuzz.token_set_ratio(art, typ) > 90:
                                self.types[j] = process.extractOne(art, def_types, scorer=fuzz.token_sort_ratio)[0]
                                self.tracks[j] = (tr[:start] + tr[end + 1:])
                                self.tracks[j] = tr.strip()
                                break

            if len(self.subtracks) != 0:
                for i, sbtr in enumerate(self.subtracks[j]):
                    self.sub_types[j] = [""] * len(sbtr)
                    if "(" in sbtr[i]:

                        start_list = [m.start() for m in re.finditer(r'\(', tr)]
                        end_list = [m.start() for m in re.finditer(r'\)', tr)]

                        for start, end in zip(start_list, end_list):

                            art = re.sub("[,:]", "", sbtr[i][start + 1:end])
                            art = art.split(" ")

                            for i in range(len(art)):
                                # check against additional personnel
                                for person in self.personnel:
                                    if fuzz.token_set_ratio(art[i], person) > 90:
                                        self.artists[j].append(person)
                                        self.subtracks[j][i] = sbtr[i][:start] + sbtr[i][end + 1:]
                                        self.subtracks[j][i] = sbtr[i].strip()

                                # check if instrumental, ...
                                for typ in def_types:
                                    if fuzz.token_set_ratio(art[i], typ) > 90:
                                        self.sub_types[j][i] = process.extractOne(art[i], def_types, scorer=fuzz.token_sort_ratio)[0]
                                        self.subtracks[j][i] = sbtr[i][:start] + sbtr[i][end + 1:]
                                        self.subtracks[j][i] = sbtr[i].strip()
                                        break

        # get rid of artists duplicates
        for i, art in enumerate(self.artists):
            self.artists[i] = sorted(list(set(art)))

    def COMPLETE(self):

        to_complete = [self.composers, self.artists, self.personnel]
        unwanted = ["featuring", "feat.", "feat"]

        # complete everything with everything
        for i in range(len(to_complete)):
            for j in range(len(to_complete)):
                # TODO doesnt return function probably modifies only local copy 
                replace_N_dim(to_complete[i], to_complete[j])

        # sort artist alphabeticaly
        if len(self.artists) > 0:
            for i, _ in enumerate(self.artists):
                self.artists[i].sort()

        # sort tracklist composers alphabeticaly
        # if len(self.tracklist_composers) > 0:
        #    for i in range(len(self.tracklist_composers)):
        #        self.tracklist_composers[i].sort()

        # get rid of feat., faeturing ...
        for i in range(len(to_complete)):
            for un in unwanted:
                # TODO doesnt return function probably modifies only local copy 
                delete_N_dim(to_complete[i], un)

    def WIKI(self):

        # TODO implement timeout error

        def parse_results(results):
            # old method
            # print(results)
            for r in results:
                r = normalize_caseless(r)
                if ("album" in r and normalize_caseless(self.album) in r):
                    #print("found:", r)
                    return r

            return None
            

            # TODO new method
            """
            print(results)
            print(process.extractOne("{} {} album".format(self.album, self.band), results, scorer=fuzz.token_sort_ratio))

            return None
            """

        # TODO new method
        """
        searches = [self.album, "{} (album)".format(self.album),
                    "{} ({} album)".format(self.album, self.band)]
        """

        # old method
        searches = [self.album]

        try:
            results = []
            for s in searches:
                results += wiki.search(s)
                querry = parse_results(results)
                if querry is not None:
                    break

            if querry is None:
                querry = self.album

            self.page = wiki.page(querry)

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
                shared_vars.warning = e
                print(Fore.LIGHTYELLOW_EX + "Album was not found!!" +
                      Fore.RESET)
                sys.exit()

        except wiki.exceptions.HTTPTimeoutError as e:
            print(e)
            log_parser.exception(e)
            shared_vars.exception = ("Search failed probably due to"
                                     "poor internet connetion")
            sys.exit()

        self.url = self.page.url

    def cook_soup(self):

        # make BeautifulSoup black magic
        self.raw_html = str(self.page.html())
        self.soup = BeautifulSoup(self.raw_html, "lxml")
        self.formated_html = self.soup.get_text()
        self.info_box_html = self.soup.find("table",
                                            class_="infobox vevent haudio")

        # check if the album belongs to band that was requested
        self.check_BAND()

    # TODO from here rewrite in more pythonic way
    def DISK_WRITE(self):

        self.bracketed_types = bracket(self.types)

        # compute number of spaces
        spaces, _ = count_spaces(self.tracks, self.bracketed_types)

        # write to file
        for j in range(len(self.disks)):

            fname = self.debug_folder + '/tracklist_{}.txt'.format(j)
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(self.disks[j] + u'\n')
                for i in range(self.disk_sep[j], self.disk_sep[j + 1]):
                    if len(self.artists) > 0:
                        if i + 1 < 10:
                            f.write(str(self.numbers[i]) + ".  " +
                                    self.tracks[i] + " " +
                                    self.bracketed_types[i] + spaces[i] +
                                    ", ".join(self.artists[i]) + u'\n')
                        else:
                            f.write(str(self.numbers[i]) + ". " +
                                    self.tracks[i] + " " +
                                    self.bracketed_types[i] + spaces[i] +
                                    ", ".join(self.artists[i]) + u'\n')
                    else:
                        if i + 1 < 10:
                            f.write(str(self.numbers[i]) + ".  " +
                                    self.tracks[i] + " " +
                                    self.bracketed_types[i] + spaces[i] +
                                    u'\n')
                        else:
                            f.write(str(self.numbers[i]) + ". " +
                                    self.tracks[i] + " " +
                                    self.bracketed_types[i] + spaces[i] +
                                    u'\n')

                    for k in range(len(self.subtracks[i])):
                        f.write("  " + write_roman(k + 1) + ". " +
                                self.subtracks[i][k] + " " +
                                self.sub_types[i][k] + u'\n')

        # save found personel to file
        with open(self.debug_folder + '/personnel.txt',
                  'w', encoding='utf8') as file:

            for i in range(len(self.personnel)):

                if len(self.appearences[i]) > 0:
                    file.write(self.personnel[i] + " - ")
                    temp = 50

                    for k in range(len(self.appearences[i])):
                        for j in range(len(self.disk_sep) - 1):

                            if (int(self.appearences[i][k]) >
                                    self.disk_sep[j] and
                                    int(self.appearences[i][k]) <
                                    self.disk_sep[j + 1]):
                                break
                        try:
                            j
                        # this is triggered if no tracklist was loaded
                        except NameError as e:
                            print(e)
                            log_parser.exception(e)
                            shared_vars.exception = e
                            continue
                        if j != temp:
                            file.write(self.disks[j] + ": " +
                                       self.numbers[int(self.appearences[i][k])])
                            temp = j
                        else:
                            file.write(self.numbers[int(self.appearences[i][k])])

                        if k != len(self.appearences[i]) - 1:
                            file.write(", ")
                    file.write(u'\n')
                else:
                    file.write(self.personnel[i] + u'\n')

    def print_tracklist(self):

        # compute number of spaces
        spaces, length = count_spaces(self.tracks, self.bracketed_types)

        # print to console
        for j in range(len(self.disks)):
            print("\n" + Fore.GREEN + str(j + 1) + ". Disk: " +
                  Fore.RESET, self.disks[j])

            try:
                print(Fore.LIGHTGREEN_EX + self.header[j][0] + " " +
                      self.header[j][1], end="")
            except:
                pass
            try:
                print(" "*(length + len(self.header[j][1])) +
                      self.header[j][2], end="")
            except:
                pass
            try:
                print(", " + self.header[j][3], end="")
            except:
                pass
            print(Fore.RESET)

            for i in range(self.disk_sep[j], self.disk_sep[j + 1]):
                print(f"{self.numbers[i]: >{2}}" + ". " + self.tracks[i] +
                      " " + self.bracketed_types[i] + spaces[i] +
                      ", ".join(self.artists[i]) +
                      ", ".join(self.composers[i]))

                for k in range(len(self.subtracks[i])):
                    print("  " + write_roman(k + 1) + ". " +
                          self.subtracks[i][k] + " " + self.sub_types[i][k])

    def print_personnel(self):

        if len(self.personnel) == 0:
            print("---\n")

        for i in range(len(self.personnel)):
            if len(self.appearences[i]) > 0:
                print(self.personnel[i] + " - ", end="")
                temp = 50
                for k in range(len(self.appearences[i])):
                    for j in range(len(self.disk_sep) - 1):
                        if (int(self.appearences[i][k]) > self.disk_sep[j] and
                           int(self.appearences[i][k]) < self.disk_sep[j + 1]):
                            break
                    try:
                        j
                    # this is triggered if no tracklist was loaded
                    except NameError as e:
                        print(e)
                        log_parser.exception(e)
                        shared_vars.exception = e
                        continue
                    if j != temp:
                        print("Disc", j + 1, ": " +
                              self.numbers[int(self.appearences[i][k])],
                              end="")
                        temp = j
                    else:
                        print(self.numbers[int(self.appearences[i][k])],
                              end="")

                    if k != len(self.appearences[i]) - 1:
                        print(", ", end="")
                print("")
            else:
                print(self.personnel[i])

    def merge_artist_personnel(self):

        for person, apper in zip(self.personnel, self.appearences):
            for a in apper:
                self.artists[a].append(person)

    # TODO to here rewrite in more pythonic way
    def data_to_dict(self, reassign_files=True):

        self.bracketed_types = bracket(self.types)

        if reassign_files is True:
            max_length = len(max(self.tracks, key=len))

            # write data to ID3 tags
            files = list_files(self.work_dir)

            print(Fore.GREEN + "\nFound files:" + Fore.RESET)
            print("\n".join(files), "\n")
            print(Fore.GREEN + "Assigning files to tracks:" + Fore.RESET)

            for i, tr in enumerate(self.tracks):
                self.tracks[i] = tr.strip()
                found = False

                # TODO restructure
                for path in files:
                    f = os.path.split(path)[1]
                    if (normalize_caseless(win_naming_convetion(tr)) in
                        normalize_caseless(f) and
                        normalize_caseless(self.types[i]) in
                        normalize_caseless(f)):

                        found = True
                        break

                if found is True:
                    print(Fore.LIGHTYELLOW_EX + tr + Fore.RESET,
                          "-"*(1 + max_length - len(tr)) + ">",
                          path)

                    self.files.append(path)

                elif found is False:
                    print(Fore.LIGHTBLUE_EX + tr + Fore.RESET,
                          "."*(2 + max_length - len(tr)),
                          "Does not have a matching file!")

                    self.files.append("")

        file_counter = 0
        dict_data = []
        for i, _ in enumerate(self.tracks):

            if self.files[i] == "" or self.files[i] == " ":
                f = None
                file_counter += 1
            else:
                f = self.files[i]

            dict = {
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

            dict_data.append(dict)

        if shared_vars.write_json is True:
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
        if len(self.files) != 0:
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
        self.info_TRACKS()

        # put song types in brackets
        self.bracketed_types = bracket(self.types)

        if len(self.files) == 0:
            shared_vars.describe = "No music files to Load"
        else:
            shared_vars.describe = "Files loaded sucesfully"

    def extract_names(self):

        # pass to NLTK only relevant part of page
        stop = self.contents_raw[-1]
        for i, item in enumerate(self.contents_raw):
            if "references" in normalize_caseless(item):
                stop = item

        start = int(self.formated_html.find("\nTrack listing"))
        end = int(self.formated_html.find("\n" + stop))
        document = self.formated_html[start:end]

        # NLTK extraction
        stop = nltk.corpus.stopwords.words('english')

        document = ' '.join([i for i in document.split() if i not in stop])
        sentences = nltk.sent_tokenize(document)
        sentences = [nltk.word_tokenize(sent) for sent in sentences]
        sentences = [nltk.pos_tag(sent) for sent in sentences]

        names = []
        for tagged_sentence in sentences:
            for chunk in nltk.ne_chunk(tagged_sentence):
                if type(chunk) == nltk.tree.Tree:
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

        filtered_names = []
        for n in names:
            if fuzz.token_set_ratio(n, self.tracks) < 90:
                filtered_names.append(n)

        self.NLTK_names = filtered_names

