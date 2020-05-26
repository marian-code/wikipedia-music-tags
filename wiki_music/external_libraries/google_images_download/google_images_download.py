"""Searching and Downloading Google Images."""

import datetime
import http.client
import json
import logging
import queue
import re
from ssl import CertificateError
from typing import TYPE_CHECKING, Tuple
from urllib.parse import quote
from urllib.request import HTTPError, Request, URLError, urlopen

from bs4 import BeautifulSoup

from wiki_music.utilities.gui_utils import get_sizes

if TYPE_CHECKING:
    from typing_extensions import TypedDict

    RespDict = TypedDict("RespDict", {"thumb": bytes,
                                      "dim": Tuple[int, Tuple[int, int]],
                                      "url": str})

__all__ = ["GoogleImagesDownload"]

http.client._MAXHEADERS = 1000

log = logging.getLogger(__name__)
log.info("Loaded google images download")


class GoogleImagesDownload:

    HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux i686) "
                             "AppleWebKit/537.17 (KHTML, like Gecko) "
                             "Chrome/24.0.1312.27 "
                             "Safari/537.17"}
    ERROR = "{} on an image...trying next one... Error: {}"

    LANG_PARAM = {
        "Arabic": "lang_ar",
        "Chinese (Simplified)": "lang_zh-CN",
        "Chinese (Traditional)": "lang_zh-TW",
        "Czech": "lang_cs",
        "Danish": "lang_da",
        "Dutch": "lang_nl",
        "English": "lang_en",
        "Estonian": "lang_et",
        "Finnish": "lang_fi",
        "French": "lang_fr",
        "German": "lang_de",
        "Greek": "lang_el",
        "Hebrew": "lang_iw ",
        "Hungarian": "lang_hu",
        "Icelandic": "lang_is",
        "Italian": "lang_it",
        "Japanese": "lang_ja",
        "Korean": "lang_ko",
        "Latvian": "lang_lv",
        "Lithuanian": "lang_lt",
        "Norwegian": "lang_no",
        "Portuguese": "lang_pt",
        "Polish": "lang_pl",
        "Romanian": "lang_ro",
        "Russian": "lang_ru",
        "Spanish": "lang_es",
        "Swedish": "lang_sv",
        "Turkish": "lang_tr"
    }

    URL_PARAMS = {
        'color': {'red': 'ic:specific,isc:red',
                  'orange': 'ic:specific,isc:orange',
                  'yellow': 'ic:specific,isc:yellow',
                  'green': 'ic:specific,isc:green',
                  'teal': 'ic:specific,isc:teel',
                  'blue': 'ic:specific,isc:blue',
                  'purple': 'ic:specific,isc:purple',
                  'pink': 'ic:specific,isc:pink',
                  'white': 'ic:specific,isc:white',
                  'gray': 'ic:specific,isc:gray',
                  'black': 'ic:specific,isc:black',
                  'brown': 'ic:specific,isc:brown'},
        'color_type': {'full-color': 'ic:color',
                       'black-and-white': 'ic:gray',
                       'transparent': 'ic:trans'},
        'usage_rights': {'labeled-for-reuse-with-modifications': 'sur:fmc',
                         'labeled-for-reuse': 'sur:fc',
                         'labeled-for-noncommercial-reuse-with-modification': 'sur:fm',
                         'labeled-for-nocommercial-reuse': 'sur:f'},
        'size': {'large': 'isz:l',
                 'medium': 'isz:m',
                 'icon': 'isz:i',
                 '>400*300': 'isz:lt,islt:qsvga',
                 '>640*480': 'isz:lt,islt:vga',
                 '>800*600': 'isz:lt,islt:svga',
                 '>1024*768': 'visz:lt,islt:xga',
                 '>2MP': 'isz:lt,islt:2mp',
                 '>4MP': 'isz:lt,islt:4mp',
                 '>6MP': 'isz:lt,islt:6mp',
                 '>8MP': 'isz:lt,islt:8mp',
                 '>10MP': 'isz:lt,islt:10mp',
                 '>12MP': 'isz:lt,islt:12mp',
                 '>15MP': 'isz:lt,islt:15mp',
                 '>20MP': 'isz:lt,islt:20mp',
                 '>40MP': 'isz:lt,islt:40mp',
                 '>70MP': 'isz:lt,islt:70mp'},
        'type': {'face': 'itp:face',
                 'photo': 'itp:photo',
                 'clipart': 'itp:clipart',
                 'line-drawing': 'itp:lineart',
                 'animated': 'itp:animated'},
        'time': {'past-24-hours': 'qdr:d',
                 'past-7-days': 'qdr:w'},
        'aspect_ratio': {'tall': 'iar:t',
                         'square': 'iar:s',
                         'wide': 'iar:w',
                         'panoramic': 'iar:xw'},
        'format': {'jpg': 'ift:jpg',
                   'gif': 'ift:gif',
                   'png': 'ift:png',
                   'bmp': 'ift:bmp',
                   'svg': 'ift:svg',
                   'webp': 'webp',
                   'ico': 'ift:ico'}
        }

    def __init__(self) -> None:
        self.stack: "queue.Queue[RespDict]" = queue.Queue()
        self._exit: bool = False
        self.max: int = 100
        self.parameters: dict = {}

        # this iterator contains the parsed info contained in the
        # `AF_initDataCallback` script (2020 format)
        # it can then be called in _get_next_item()
        # NOTE: never access this directly,
        # always use self._get_AF_initDataCallback()
        self._info_AF_initDataCallback = None

    def close(self):
        """Exit search."""
        self._exit = True

    def args(self, key, default=None):
        """Get value from passed in arguments by key."""
        return self.arguments.get(key, default)

    def download_page(self, url):
        """Downloading entire Web Document (Raw Page Content)."""
        try:
            req = Request(url, headers=self.HEADERS)
            with urlopen(req) as resp:
                return str(resp.read())
        except Exception as e:
            log.exception(e)
            print(f"Could not open URL. Please check your internet "
                  f"connection and/or ssl settings: {e}")

    @staticmethod
    def format_object(obj):
        """Format the object in readable format."""
        return {
            'image_format': obj['ity'],
            'image_height': obj['oh'],
            'image_width': obj['ow'],
            'image_link': obj['ou'],
            'image_description': obj['pt'],
            'image_host': obj['rh'],
            'image_source': obj['ru'],
            'image_thumbnail_url': obj['tu']
        }

    def build_url_parameters(self):
        """Building URL parameters."""
        if self.args('language'):
            lang = "&lr="
            lang_url = lang + self.LANG_PARAM[self.args('language')]
        else:
            lang_url = ''

        if self.args('time_range'):
            json_acceptable_string = self.args('time_range').replace("'", "\"")
            d = json.loads(json_acceptable_string)
            time_range = f',cdr:1,cd_min:{d["time_min"]},cd_max:{d["time_max"]}'
        else:
            time_range = ''

        if self.args('exact_size'):
            size_array = [x.strip() for x in self.args('exact_size').split(',')]
            exact_size = f",isz:ex,iszw:{size_array[0]},iszh:{size_array[1]}"
        else:
            exact_size = ''

        built_url = "&tbs="

        counter = 0
        for key, value in self.URL_PARAMS.items():
            if self.args(key):
                ext_param = value[self.args(key)]
                # counter will tell if it is first param added or not
                if counter == 0:
                    # add it to the built url
                    built_url = built_url + ext_param
                    counter += 1
                else:
                    built_url = built_url + ',' + ext_param
                    counter += 1

        built_url = lang_url + built_url + exact_size + time_range
        return built_url

    @staticmethod
    def build_search_url(search_term, params, url, specific_site,
                         safe_search):
        """Building main search URL."""
        # check the args and choose the URL
        if url:
            url = url
        elif specific_site:
            url = (
                f'https://www.google.com/search?q={quote(search_term)}'
                f'&as_sitesearch={specific_site}&espv=2&biw=1366&bih=667&'
                f'site=webhp&source=lnms&tbm=isch{params}&sa=X&ei='
                f'XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'
            )
        else:
            url = (
                f'https://www.google.com/search?q={quote(search_term)}'
                f'&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch'
                f'{params}&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'
            )

        #safe search check
        if safe_search:
            url = url + "&safe=active"

        return url

    def download_image_thumbnail(self, image_url, return_image_name):
        """Download Images."""
        wiki_music_thumb = None
        download_status = False
        req = Request(image_url, headers=self.HEADERS)

        # timeout time to download an image
        if self.args('socket_timeout'):
            timeout = float(self.args('socket_timeout'))
        else:
            timeout = 10

        try:
            with urlopen(req, None, timeout) as response:
                wiki_music_thumb = response.read()

            download_status = True
            download_message = (f"Completed Image Thumbnail ====> "
                                f"{return_image_name}")

        except UnicodeEncodeError as e:
            download_message = self.ERROR.format("UnicodeEncodeError", e)
        except HTTPError as e:
            download_message = self.ERROR.format("HTTPError", e)
        except URLError as e:
            download_message = self.ERROR.format("URLError", e)
        except CertificateError as e:
            download_message = self.ERROR.format("CertificateError", e)
        except IOError as e:
            download_message = self.ERROR.format("IOError", e)
        finally:
            return download_status, download_message, wiki_music_thumb

    @staticmethod
    def download_image(image_url, image_format, count):
        """Download Images."""
        # keep everything after the last '/'
        image_name = str(image_url[(image_url.rfind('/')) + 1:])
        image_name = image_name.lower()
        # if no extension then add it
        # remove everything after the image name
        if image_format == "":
            image_name += ".jpg"
        elif image_format == "jpeg":
            image_name = image_name[:image_name.find(image_format) + 4]
        else:
            image_name = image_name[:image_name.find(image_format) + 3]

        return_image_name = f"{count}. {image_name}"

        size = get_sizes(image_url)
        if not size[1]:
            return (False, "Unknown image size", return_image_name,
                    {"dim": (None, (None, None)), "url": ""})
        else:
            return (True, "Printed url without downloading",
                    return_image_name, {"dim": size, "url": image_url})

    def _get_next_item(self, s):
        """Finding 'Next Image' from the given raw page."""
        start_line = s.find('rg_meta notranslate')
        if start_line == -1:  # If no links are found then give an error!
            try:
                final_object = next(self._info_AF_initDataCallback)
                return final_object, 0
            except StopIteration:
                # if StopIteration is raised, break from loop
                end_quote = 0
                link = "no_links"
                return link, end_quote
        else:
            start_line = s.find('class="rg_meta notranslate">')
            start_object = s.find('{', start_line + 1)
            end_object = s.find('</div>', start_object + 1)
            object_raw = str(s[start_object:end_object])
            #remove escape characters based on python version

            try:
                object_decode = bytes(object_raw, "utf-8").decode("unicode_escape")
                final_object = json.loads(object_decode)
            except Exception:
                log.exception(e)
                final_object = ""

            return final_object, end_object

    def _get_all_items(self, page, limit):
        """Getting all links with the help of '_images_get_next_image'."""

        try:
            self._parse_AF_initDataCallback(page)
        except Exception as e:
            log.exception(e)
            print('WARNING: _parse_AF_initDataCallback failed', e)

        items = []
        error_count = 0
        i = 0
        count = 1
        while count < limit + 1:
            item, end_content = self._get_next_item(page)
            if item == "no_links":
                break
            elif item == "":
                page = page[end_content:]
            elif self.args('offset') and count < int(self.args('offset')):
                count += 1
                page = page[end_content:]
            else:
                # format the item for readability
                item = self.format_object(item)

                # download the images
                download_status, _, return_image_name, wiki_music_image = (
                    self.download_image(item['image_link'],
                                        item['image_format'],
                                        count)
                )
                if download_status:

                    # download image_thumbnails
                    if self.args('thumbnail'):
                        _, download_message_thumbnail, wiki_music_thumb = (
                            self.download_image_thumbnail(
                                item['image_thumbnail_url'],
                                return_image_name)
                        )
                        print(download_message_thumbnail)
                    else:
                        wiki_music_thumb = bytes()

                    count += 1
                    item['image_filename'] = return_image_name
                    # Append all the links in the list named 'Links'
                    items.append(item)
                else:
                    error_count += 1
                    wiki_music_thumb = bytes()

                wiki_music_image["thumb"] = wiki_music_thumb
                self.stack.put(wiki_music_image)

                page = page[end_content:]
            i += 1

            if self._exit:
                print("Album art search exiting ...")
                return items, error_count

        if count < limit:
            print(f"\n\nUnfortunately all {limit} could not be downloaded "
                  f"because some images were not downloadable. {count - 1} "
                  f"is all we got for this search filter!")
        return items, error_count

    def _parse_AF_initDataCallback(self, page):
        """Parse data callback.

        How it works: there's a <script> that contains the images info,
        the code in it contains `AF_initDataCallback` this contains
        the image data

        Parameters
        ----------
        page:
            html string

        References
        ----------
        https://gist.github.com/FarisHijazi/6c9ba3fb315d0ce9bfa62c10dfa8b2f8
            See the js code

        Returns
        -------
            self._info_AF_initDataCallback, this is an iterator containing rg_meta objects
        """

        def parse_json(t):
            try:
                t = t.encode('utf8').decode("unicode_escape")

                # this will trim the code to choose only
                # the part with the data arrays
                start, end = "data:function(){return ",  "]\n}});"
                data_str = t[t.index(start) + len(start): t.rindex(end) + 1]
                json_obj = json.loads(data_str)
                return json_obj
            except Exception as e:
                log.exception(e)
                print('WARNING:', e, t)
                return {}

        def meta_array2meta_dict(meta):
            rg_meta = {
                'id': '',  # thumbnail
                'tu': '', 'th': '', 'tw': '',  # original
                'ou': '', 'oh': '', 'ow': '',  # site and name
                'pt': '', 'st': '',  # titles
                'ity': 'gif',
                'rh': 'IMAGE_HOST',
                'ru': 'IMAGE_SOURCE',
            }
            try:
                rg_meta['id'] = meta[1]
                # thumbnail
                rg_meta['tu'], rg_meta['th'], rg_meta['tw'] = meta[2]
                # original
                rg_meta['ou'], rg_meta['oh'], rg_meta['ow'] = meta[3]

                siteAndNameInfo = meta[9] or meta[11]
                # site and name
                try:
                    if '2003' in siteAndNameInfo:
                        rg_meta['ru'] = siteAndNameInfo['2003'][2]
                        rg_meta['pt'] = siteAndNameInfo['2003'][3]
                    elif '2008' in siteAndNameInfo:
                        rg_meta['pt'] = siteAndNameInfo['2008'][2]

                    if '183836587' in siteAndNameInfo:
                        # infolink
                        rg_meta['st'] = siteAndNameInfo['183836587'][0]
                        rg_meta['rh'] = rg_meta['st']
                except Exception as e:
                    log.exception(e)
                    pass

                return rg_meta

            except Exception as e:
                log.exception(e)
                print("WARNING:", e, meta)

        bs = BeautifulSoup(page, 'lxml')
        # get scripts
        scripts = bs.select('script[nonce]')

        scriptTexts = [element.text for element in scripts]
        # choose only those with AF_initDataCallback
        scriptTexts = [stext for stext in scriptTexts
                       if bool(re.match('^AF_initDataCallback', stext))]

        entry = parse_json(scriptTexts[-1])
        # confirmed
        imgMetas = map(lambda meta: meta[1], entry[31][0][12][2])

        metas = list(filter(None, map(meta_array2meta_dict, imgMetas)))

        self._info_AF_initDataCallback = iter(metas)
        return self._info_AF_initDataCallback

    def download(self, arguments: dict):
        """Bulk Download."""

        self.__init__()

        self.arguments = arguments

        # Initialization and Validation of user arguments
        if self.args('keywords'):
            search_keyword = [str(item) for item in
                              self.args('keywords').split(',')]

        # both time and time range should not be allowed in the same query
        if self.args('time') and self.args('time_range'):
            raise ValueError('Either time or time range should be used '
                             'in a query. '
                             'Both cannot be used at the same time.')

        # both time and time range should not be allowed in the same query
        if self.args('size') and self.args('exact_size'):
            raise ValueError('Either "size" or "exact_size" should be used '
                             'in a query. '
                             'Both cannot be used at the same time.')

        # Setting limit on number of images to be downloaded
        if self.args('limit'):
            limit = int(self.args('limit'))
        else:
            limit = 100

        self.max = limit

        if self.args('url'):
            current_time = str(datetime.datetime.now()).split('.')[0]
            search_keyword = [current_time.replace(":", "_")]

        # If url argument not present then keywords is mandatory argument
        if not self.args('url') and not self.args('keywords'):
            raise ValueError(
                '-------------------------------\n'
                'Uh oh! Keywords is a required argument \n\n'
                'Please refer to the documentation on guide to writing queries \n'
                'https://github.com/hardikvasa/google-images-download#examples'
                '\n\nexiting!\n'
                '-------------------------------'
            )

        for i, search_term in enumerate(search_keyword, 1):
            print(f"\nItem no.: {i} --> Item name = {search_term}")
            print("Evaluating...")

            # building URL with params
            params = self.build_url_parameters()

            # building main search url
            url = self.build_search_url(search_term, params, self.args('url'),
                                        self.args('specific_site'),
                                        self.args('safe_search'))

            if limit < 101:
                raw_html = self.download_page(url)  # download page
            else:
                raise ValueError("Cannot download more than 100 images")

            # get all image items and download images
            items, errorCount = self._get_all_items(raw_html, limit)

            print(f"\nErrors: {errorCount}\n")
