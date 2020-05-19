"""Searching and Downloading Google Images to the local disk."""

# ! added for wiki_music ##################################################
from wiki_music.utilities.gui_utils import get_sizes
import logging
import queue
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from typing_extensions import TypedDict

    RespDict = TypedDict("RespDict", {"thumb": bytes,
                                      "dim": Tuple[int, Tuple[int, int]],
                                      "url": str})

# ! added for wiki_music ##################################################

# Import Libraries
import bs4
import time  # Importing the time library to check the time of code execution
import os
import ssl
import datetime
import json
import re
import socket
import urllib.request
from urllib.request import Request, urlopen
from urllib.request import URLError, HTTPError
from urllib.parse import quote
import http.client
from http.client import IncompleteRead
http.client._MAXHEADERS = 1000


log = logging.getLogger(__name__)

log.info("Loaded google images download")


class googleimagesdownload:

    # ! added for wiki_music ##################################################
    def __init__(self):
        self.stack: "queue.Queue[RespDict]" = queue.Queue()
        self._exit: bool = False
        self.max: int  = 100

        # this iterator contains the parsed info contained in the `AF_initDataCallback` script (2020 format)
        # it can then be called in _get_next_item()
        # NOTE: never access this directly, always use self._get_AF_initDataCallback()
        self._info_AF_initDataCallback = None
    
    def close(self):
        self._exit = True
    # ! added for wiki_music ##################################################

    def download_page(self, url):
        """Downloading entire Web Document (Raw Page Content)."""
        try:
            headers = {}
            headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req)
            respData = str(resp.read())
            return respData
        except Exception as e:
            print("Could not open URL. Please check your internet connection and/or ssl settings")

    def format_object(self, obj):
        """Format the object in readable format."""
        formatted_object = {}
        formatted_object['image_format'] = obj['ity']
        formatted_object['image_height'] = obj['oh']
        formatted_object['image_width'] = obj['ow']
        formatted_object['image_link'] = obj['ou']
        formatted_object['image_description'] = obj['pt']
        formatted_object['image_host'] = obj['rh']
        formatted_object['image_source'] = obj['ru']
        formatted_object['image_thumbnail_url'] = obj['tu']
        return formatted_object

    def build_url_parameters(self, arguments):
        """Building URL parameters."""
        if arguments['language']:
            lang = "&lr="
            lang_param = {"Arabic":"lang_ar","Chinese (Simplified)":"lang_zh-CN","Chinese (Traditional)":"lang_zh-TW","Czech":"lang_cs","Danish":"lang_da","Dutch":"lang_nl","English":"lang_en","Estonian":"lang_et","Finnish":"lang_fi","French":"lang_fr","German":"lang_de","Greek":"lang_el","Hebrew":"lang_iw ","Hungarian":"lang_hu","Icelandic":"lang_is","Italian":"lang_it","Japanese":"lang_ja","Korean":"lang_ko","Latvian":"lang_lv","Lithuanian":"lang_lt","Norwegian":"lang_no","Portuguese":"lang_pt","Polish":"lang_pl","Romanian":"lang_ro","Russian":"lang_ru","Spanish":"lang_es","Swedish":"lang_sv","Turkish":"lang_tr"}
            lang_url = lang+lang_param[arguments['language']]
        else:
            lang_url = ''

        if arguments['time_range']:
            json_acceptable_string = arguments['time_range'].replace("'", "\"")
            d = json.loads(json_acceptable_string)
            time_range = ',cdr:1,cd_min:' + d['time_min'] + ',cd_max:' + d['time_max']
        else:
            time_range = ''

        if arguments['exact_size']:
            size_array = [x.strip() for x in arguments['exact_size'].split(',')]
            exact_size = ",isz:ex,iszw:" + str(size_array[0]) + ",iszh:" + str(size_array[1])
        else:
            exact_size = ''

        built_url = "&tbs="
        counter = 0
        params = {'color':[arguments['color'],{'red':'ic:specific,isc:red', 'orange':'ic:specific,isc:orange', 'yellow':'ic:specific,isc:yellow', 'green':'ic:specific,isc:green', 'teal':'ic:specific,isc:teel', 'blue':'ic:specific,isc:blue', 'purple':'ic:specific,isc:purple', 'pink':'ic:specific,isc:pink', 'white':'ic:specific,isc:white', 'gray':'ic:specific,isc:gray', 'black':'ic:specific,isc:black', 'brown':'ic:specific,isc:brown'}],
                  'color_type':[arguments['color_type'],{'full-color':'ic:color', 'black-and-white':'ic:gray','transparent':'ic:trans'}],
                  'usage_rights':[arguments['usage_rights'],{'labeled-for-reuse-with-modifications':'sur:fmc','labeled-for-reuse':'sur:fc','labeled-for-noncommercial-reuse-with-modification':'sur:fm','labeled-for-nocommercial-reuse':'sur:f'}],
                  'size':[arguments['size'],{'large':'isz:l','medium':'isz:m','icon':'isz:i','>400*300':'isz:lt,islt:qsvga','>640*480':'isz:lt,islt:vga','>800*600':'isz:lt,islt:svga','>1024*768':'visz:lt,islt:xga','>2MP':'isz:lt,islt:2mp','>4MP':'isz:lt,islt:4mp','>6MP':'isz:lt,islt:6mp','>8MP':'isz:lt,islt:8mp','>10MP':'isz:lt,islt:10mp','>12MP':'isz:lt,islt:12mp','>15MP':'isz:lt,islt:15mp','>20MP':'isz:lt,islt:20mp','>40MP':'isz:lt,islt:40mp','>70MP':'isz:lt,islt:70mp'}],
                  'type':[arguments['type'],{'face':'itp:face','photo':'itp:photo','clipart':'itp:clipart','line-drawing':'itp:lineart','animated':'itp:animated'}],
                  'time':[arguments['time'],{'past-24-hours':'qdr:d','past-7-days':'qdr:w'}],
                  'aspect_ratio':[arguments['aspect_ratio'],{'tall':'iar:t','square':'iar:s','wide':'iar:w','panoramic':'iar:xw'}],
                  'format':[arguments['format'],{'jpg':'ift:jpg','gif':'ift:gif','png':'ift:png','bmp':'ift:bmp','svg':'ift:svg','webp':'webp','ico':'ift:ico'}]}
        for key, value in params.items():
            if value[0] is not None:
                ext_param = value[1][value[0]]
                # counter will tell if it is first param added or not
                if counter == 0:
                    # add it to the built url
                    built_url = built_url + ext_param
                    counter += 1
                else:
                    built_url = built_url + ',' + ext_param
                    counter += 1
        built_url = lang_url+built_url+exact_size+time_range
        return built_url

    def build_search_url(self, search_term, params, url, specific_site, safe_search):
        """Building main search URL."""
        #check safe_search
        safe_search_string = "&safe=active"
        # check the args and choose the URL
        if url:
            url = url
        elif specific_site:
            url = 'https://www.google.com/search?q=' + quote(
                search_term) + '&as_sitesearch=' + specific_site + '&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch' + params + '&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'
        else:
            url = 'https://www.google.com/search?q=' + quote(
                search_term) + '&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch' + params + '&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'

        #safe search check
        if safe_search:
            url = url + safe_search_string

        # print(url)
        return url

    def download_image_thumbnail(self,image_url,main_directory,dir_name,return_image_name,print_urls,socket_timeout,print_size,no_download_thumbs):
        """Download Images."""
        # ! altered for wiki_music ############################################
        wiki_music_thumb = None
        try:
            req = Request(image_url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"})
            try:
                # timeout time to download an image
                if socket_timeout:
                    timeout = float(socket_timeout)
                else:
                    timeout = 10

                response = urlopen(req, None, timeout)
                data = response.read()
                response.close()

                path = remove_illegal_characters(main_directory + "/" + dir_name + " - thumbnail" + "/" + return_image_name)

                try:
                    if no_download_thumbs:
                        # ! altered for wiki_music ############################################
                        wiki_music_thumb = data
                    else:
                        output_file = open(path, 'wb')
                        output_file.write(data)
                        output_file.close()
                except OSError as e:
                    download_status = 'fail'
                    download_message = "OSError on an image...trying next one..." + " Error: " + str(e)
                except IOError as e:
                    download_status = 'fail'
                    download_message = "IOError on an image...trying next one..." + " Error: " + str(e)

                download_status = 'success'
                download_message = "Completed Image Thumbnail ====> " + return_image_name


            except UnicodeEncodeError as e:
                download_status = 'fail'
                download_message = "UnicodeEncodeError on an image...trying next one..." + " Error: " + str(e)

        except HTTPError as e:  # If there is any HTTPError
            download_status = 'fail'
            download_message = "HTTPError on an image...trying next one..." + " Error: " + str(e)

        except URLError as e:
            download_status = 'fail'
            download_message = "URLError on an image...trying next one..." + " Error: " + str(e)

        except ssl.CertificateError as e:
            download_status = 'fail'
            download_message = "CertificateError on an image...trying next one..." + " Error: " + str(e)

        except IOError as e:  # If there is any IOError
            download_status = 'fail'
            download_message = "IOError on an image...trying next one..." + " Error: " + str(e)
        # ! altered for wiki_music ############################################
        return download_status, download_message, wiki_music_thumb

    def download_image(self,image_url,image_format,main_directory,dir_name,count,print_urls,socket_timeout,prefix,print_size,no_numbering,no_download):
        """Download Images."""
        # keep everything after the last '/'
        image_name = str(image_url[(image_url.rfind('/')) + 1:])
        image_name = image_name.lower()
        # if no extension then add it
        # remove everything after the image name
        if image_format == "":
            image_name = image_name + "." + "jpg"
        elif image_format == "jpeg":
            image_name = image_name[:image_name.find(image_format) + 4]
        else:
            image_name = image_name[:image_name.find(image_format) + 3]

        # prefix name in image
        if prefix:
            prefix = prefix + " "
        else:
            prefix = ''

        return_image_name = prefix + str(count) + ". " + image_name

        # ! added for wiki_music ##############################################
        if no_download:
            size = get_sizes(image_url)
            if not size[1]:
                return "fail", "Unknown image size", return_image_name, None, {"dim": (None, (None, None)), "url": ""}
            else:
                img = {"dim": size, "url": image_url}
                return "success", "Printed url without downloading", return_image_name, None, img
        # ! added for wiki_music ##############################################
        try:
            req = Request(image_url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"})
            try:
                # timeout time to download an image
                if socket_timeout:
                    timeout = float(socket_timeout)
                else:
                    timeout = 10

                response = urlopen(req, None, timeout)
                data = response.read()
                response.close()

                if no_numbering:
                    path = main_directory + "/" + dir_name + "/" + prefix + image_name
                else:
                    path = main_directory + "/" + dir_name + "/" + prefix + str(count) + ". " + image_name

                try:
                    output_file = open(path, 'wb')
                    output_file.write(data)
                    output_file.close()
                    absolute_path = os.path.abspath(path)
                except OSError as e:
                    download_status = 'fail'
                    download_message = "OSError on an image...trying next one..." + " Error: " + str(e)
                    return_image_name = ''
                    absolute_path = ''

                #return image name back to calling method to use it for thumbnail downloads
                download_status = 'success'
                download_message = "Completed Image ====> " + prefix + str(count) + ". " + image_name

            except UnicodeEncodeError as e:
                download_status = 'fail'
                download_message = "UnicodeEncodeError on an image...trying next one..." + " Error: " + str(e)
                return_image_name = ''
                absolute_path = ''

            except URLError as e:
                download_status = 'fail'
                download_message = "URLError on an image...trying next one..." + " Error: " + str(e)
                return_image_name = ''
                absolute_path = ''

        except HTTPError as e:  # If there is any HTTPError
            download_status = 'fail'
            download_message = "HTTPError on an image...trying next one..." + " Error: " + str(e)
            return_image_name = ''
            absolute_path = ''

        except URLError as e:
            download_status = 'fail'
            download_message = "URLError on an image...trying next one..." + " Error: " + str(e)
            return_image_name = ''
            absolute_path = ''

        except ssl.CertificateError as e:
            download_status = 'fail'
            download_message = "CertificateError on an image...trying next one..." + " Error: " + str(e)
            return_image_name = ''
            absolute_path = ''

        except IOError as e:  # If there is any IOError
            download_status = 'fail'
            download_message = "IOError on an image...trying next one..." + " Error: " + str(e)
            return_image_name = ''
            absolute_path = ''

        except IncompleteRead as e:
            download_status = 'fail'
            download_message = "IncompleteReadError on an image...trying next one..." + " Error: " + str(e)
            return_image_name = ''
            absolute_path = ''

        # ! altered for wiki_music ############################################
        return download_status,download_message,return_image_name,absolute_path, {"dim": (None, (None, None)), "url": ""}

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
            except:
                final_object = ""

            return final_object, end_object

    def _get_all_items(self, page, main_directory, dir_name, limit, arguments):
        """Getting all links with the help of '_images_get_next_image'."""

        try:
            self._parse_AF_initDataCallback(page)
        except Exception as e:
            print('WARNING: _parse_AF_initDataCallback failed', e)

        items = []
        abs_path = []
        errorCount = 0
        i = 0
        count = 1
        while count < limit+1:
            object, end_content = self._get_next_item(page)
            if object == "no_links":
                break
            elif object == "":
                page = page[end_content:]
            elif arguments['offset'] and count < int(arguments['offset']):
                    count += 1
                    page = page[end_content:]
            else:
                #format the item for readability
                object = self.format_object(object)
                if arguments['metadata']:
                    print("\nImage Metadata: " + str(object))

                #download the images
                # ! altered for wiki_music ####################################
                download_status,download_message,return_image_name,absolute_path, wiki_music_image = self.download_image(object['image_link'],object['image_format'],main_directory,dir_name,count,arguments['print_urls'],arguments['socket_timeout'],arguments['prefix'],arguments['print_size'],arguments['no_numbering'],arguments['no_download'])
                #print(download_message)
                if download_status == "success":

                    # download image_thumbnails
                    if arguments['thumbnail']:
                        # ! altered for wiki_music ############################
                        download_status, download_message_thumbnail, wiki_music_thumb = self.download_image_thumbnail(object['image_thumbnail_url'],main_directory,dir_name,return_image_name,arguments['print_urls'],arguments['socket_timeout'],arguments['print_size'],arguments['no_download_thumbs'])
                        print(download_message_thumbnail)
                    else:
                        wiki_music_thumb = bytes()

                    count += 1
                    object['image_filename'] = return_image_name
                    items.append(object)  # Append all the links in the list named 'Links'
                    abs_path.append(absolute_path)
                else:
                    errorCount += 1
                    wiki_music_thumb = bytes()

                # ! added for wiki_music ######################################
                wiki_music_image["thumb"] = wiki_music_thumb
                self.stack.put(wiki_music_image)
                # ! added for wiki_music ######################################

                #delay param
                if arguments['delay']:
                    time.sleep(int(arguments['delay']))

                page = page[end_content:]
            i += 1

            # ! added for wiki_music ##########################################
            if self._exit:
                print("Album art search exiting ...")
                return items, errorCount, abs_path

            # ! added for wiki_music ##########################################
        if count < limit:
            print("\n\nUnfortunately all " + str(
                limit) + " could not be downloaded because some images were not downloadable. " + str(
                count-1) + " is all we got for this search filter!")
        return items,errorCount,abs_path

    def _parse_AF_initDataCallback(self, page):
        """Parse data callback.

        Parameters
        ----------
        page:
            html string
        Returns
        -------
            self._info_AF_initDataCallback, this is an iterator containing rg_meta objects
        """

        def get_metas(page):
            """
            the this works by parsing the info in the page scripts
            See the js code in: https://gist.github.com/FarisHijazi/6c9ba3fb315d0ce9bfa62c10dfa8b2f8
            :returns a list of objects, these contain the image info
            how it works:
              there's a <script> that contains the images info, the code in it contains `AF_initDataCallback`
              this contains the image data
            """
            bs = bs4.BeautifulSoup(page, 'lxml')
            # get scripts
            scripts = bs.select('script[nonce]')

            def get_element_text(element):
                return element.text
 

            scriptTexts = map(get_element_text, scripts)
            # choose only those with AF_initDataCallback
            scriptTexts = [stext for stext in scriptTexts if bool(re.match('^AF_initDataCallback', stext))]

            def parse_json(t):
                try:
                    t = t.encode('utf8').decode("unicode_escape")

                    # this will trim the code to choose only the part with the data arrays
                    start, end = "data:function(){return ",  "]\n}});"
                    data_str = t[t.index(start) + len(start): t.rindex(end) + 1]
                    json_obj = json.loads(data_str)
                    return json_obj
                except Exception as e:
                    print('WARNING:', e, t)
                    return {}

            entries = list(map(parse_json, scriptTexts))
            entry = entries[-1]
            imgMetas = map(lambda meta: meta[1], entry[31][0][12][2])  # confirmed

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
                            rg_meta['st'] = siteAndNameInfo['183836587'][0]  # infolink
                            rg_meta['rh'] = rg_meta['st']
                    except:
                        pass

                    return rg_meta

                except Exception as e:
                    print("WARNING:", e, meta)

            metas = list(filter(None, map(meta_array2meta_dict, imgMetas)))
            return metas

        metas = get_metas(page)
        self._info_AF_initDataCallback = iter(metas)
        return self._info_AF_initDataCallback

    def download(self,arguments):
        """Bulk Download."""

        # ! added for wiki_music ##############################################
        self.__init__()
        # ! added for wiki_music ##############################################

        ######Initialization and Validation of user arguments
        if arguments['keywords']:
            search_keyword = [str(item) for item in arguments['keywords'].split(',')]

        # both time and time range should not be allowed in the same query
        if arguments['time'] and arguments['time_range']:
            raise ValueError('Either time or time range should be used in a query. Both cannot be used at the same time.')

        # both time and time range should not be allowed in the same query
        if arguments['size'] and arguments['exact_size']:
            raise ValueError('Either "size" or "exact_size" should be used in a query. Both cannot be used at the same time.')

        # both image directory and no image directory should not be allowed in the same query
        if arguments['image_directory'] and arguments['no_directory']:
            raise ValueError('You can either specify image directory or specify no image directory, not both!')

        # Additional words added to keywords
        if arguments['suffix_keywords']:
            suffix_keywords = [" " + str(sk) for sk in arguments['suffix_keywords'].split(',')]
        else:
            suffix_keywords = ['']

        # Additional words added to keywords
        if arguments['prefix_keywords']:
            prefix_keywords = [str(sk) + " " for sk in arguments['prefix_keywords'].split(',')]
        else:
            prefix_keywords = ['']

        # Setting limit on number of images to be downloaded
        if arguments['limit']:
            limit = int(arguments['limit'])
        else:
            limit = 100

        # ! added for wiki_music ##############################################
        self.max = limit

        if arguments['url']:
            current_time = str(datetime.datetime.now()).split('.')[0]
            search_keyword = [current_time.replace(":", "_")]

        # If url argument not present then keywords is mandatory argument
        if arguments['url'] is None and arguments['keywords'] is None:
            raise ValueError('-------------------------------\n'
                  'Uh oh! Keywords is a required argument \n\n'
                  'Please refer to the documentation on guide to writing queries \n'
                  'https://github.com/hardikvasa/google-images-download#examples'
                  '\n\nexiting!\n'
                  '-------------------------------')

        # If this argument is present, set the custom output directory
        if arguments['output_directory']:
            main_directory = arguments['output_directory']
        else:
            main_directory = "downloads"

        # Proxy settings
        if arguments['proxy']:
            os.environ["http_proxy"] = arguments['proxy']
            os.environ["https_proxy"] = arguments['proxy']
            ######Initialization Complete

        paths = {}
        for pky in prefix_keywords:
            for sky in suffix_keywords:     # 1.for every suffix keywords
                i = 0
                while i < len(search_keyword):      # 2.for every main keyword
                    iteration = "\n" + "Item no.: " + str(i + 1) + " -->" + " Item name = " + str(pky) + str(search_keyword[i] + str(sky))
                    print(iteration)
                    print("Evaluating...")
                    search_term = pky + search_keyword[i] + sky

                    if arguments['image_directory']:
                        dir_name = arguments['image_directory']
                    elif arguments['no_directory']:
                        dir_name = ''
                    else:
                        dir_name = search_term + ('-' + arguments['color'] if arguments['color'] else '')   #sub-directory

                    params = self.build_url_parameters(arguments)     #building URL with params

                    url = self.build_search_url(search_term,params,arguments['url'],arguments['specific_site'],arguments['safe_search'])      #building main search url

                    if limit < 101:
                        raw_html = self.download_page(url)  # download page
                    else:
                        raise ValueError("Cannot download more than 100 images")

                    items,errorCount,abs_path = self._get_all_items(raw_html,main_directory,dir_name,limit,arguments)    #get all image items and download images
                    paths[pky + search_keyword[i] + sky] = abs_path

                    #dumps into a json file
                    if arguments['extract_metadata']:
                        try:
                            if not os.path.exists("logs"):
                                os.makedirs("logs")
                        except OSError as e:
                            print(e)
                        json_file = open("logs/"+search_keyword[i]+".json", "w")
                        json.dump(items, json_file, indent=4, sort_keys=True)
                        json_file.close()

                    i += 1
                    print("\nErrors: " + str(errorCount) + "\n")
        if arguments['print_paths']:
            print(paths)

        return paths

def remove_illegal_characters(string):
    string = str(string)

    badchars = re.compile(r'[^A-Za-z0-9_. ]+|^\.|\.$|^ | $|^$')
    badnames = re.compile(r'(aux|com[1-9]|con|lpt[1-9]|prn)(\.|$)')

    try:
        name = badchars.sub('_', string)
        if badnames.match(name):
            name = '_' + name
        return name
    except Exception as e:
        print("ERROR cleaning filename:", e)
    return string
