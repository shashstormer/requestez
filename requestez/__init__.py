import random
import time
import requests
import os
from m3u8 import parse as _parse
import requests.exceptions
from requests.structures import CaseInsensitiveDict
from helpers import log, pbar


class Session:
    def __init__(self, human_browsing=False):
        """
        :param human_browsing: not required in most cases, you may use this in case of ratelimits or anti bot measures
        """
        self.session = requests.Session()
        self.headers = CaseInsensitiveDict({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/114.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                      'image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            # 'Accept-Encoding': 'gzip, deflate, br',  # you can add this if you want but will have to implement decompression
            'Connection': 'keep-alive',
            'Referer': None,
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            "SEC-CH-UA-MOBILE": "?0",
            "SEC-CH-UA-PLATFORM": "Linux",
        })
        self.last_html_url = None
        self.human_browsing = human_browsing
        self.min_sleep = 1
        self.max_sleep = 7

    def where_to(self, url, headers=None, post=False, body=None, notify=True):
        """

        :param url: url to be requested
        :param headers: additional headers to be sent
        :param post: if True, post request will be sent
        :param body: body to be sent with post request
        :param notify: if True, will print the url and status code
        :return: {
            "to": "url",
            "headers": "headers",  # caseinsensitive dict
            "cookies": "cookies"   # requests.cookies.RequestsCookieJar
        }
        """
        ret = {}
        if headers is None:
            headers = {}
        _headers = self.headers.copy()
        if self.last_html_url:
            _headers['Referer'] = self.last_html_url
        _headers.update(headers)
        if notify:
            log("getting :", url, end="", color="yellow")
        if post:
            resp = self.session.post(url, headers=_headers, data=body, allow_redirects=False)
        else:
            resp = self.session.get(url, headers=_headers, allow_redirects=False)
        if notify:
            log("\rgot : ", resp.url, "\ncode : ", resp.status_code, color="green")
        ret["to"] = resp.headers.get("Location", url)
        ret["headers"] = resp.headers
        ret["cookies"] = resp.cookies
        return ret

    def get(self, url, headers=None, post=False, body=None, notify=True, text=True, return_final_page_url=False,
            return_cookies=False, set_html=True, sleep_for_anti_bot=True):
        """
        method to fetch any url, with additional features it also the last html page requested as referer
        if you do not want this to happen for a specific request then set last_html_url to None before calling this method
        the headers passed as argument will be merged with the default headers and override any conflicting keys
        :param url: url to be fetched
        :param headers: additional headers to be sent while requesting
        :param post: if True, post request will be sent
        :param body: body to be sent with post request
        :param notify: if True, will print the url and status code
        :param text: if True, will return text, else will return response object
        :param return_final_page_url: if True, will return final page url {"resp": "text", "url": "final_url"}
        :param return_cookies: if True, will return cookies {"resp": "text", "cookies": "cookies"} if return_final_page_url is also true then even the url will be present
        :param set_html: if True, will set self.last_html_url to response.url if response is html
        :param sleep_for_anti_bot: if True, will sleep for random time between self.min_sleep and self.max_sleep
        :return: default is text when text = True, else returns response object
        """
        if self.human_browsing and sleep_for_anti_bot:
            time.sleep(random.randint(self.min_sleep, self.max_sleep))
        if notify:
            log("getting :", url, end="", color="yellow")
        if headers is None:
            headers = {}
        _headers = self.headers.copy()
        if self.last_html_url:
            _headers['Referer'] = self.last_html_url
        _headers.update(headers)
        if not post:
            response = self.session.get(url, headers=_headers, timeout=60)
        else:
            response = self.session.post(url, headers=_headers, data=body, timeout=60)
        if 'text/html' in response.headers.get('Content-Type', '') and set_html:
            self.last_html_url = response.url
        if text:
            resp = response.text
        else:
            resp = response
        if notify:
            if resp.status_code == 200:
                log("\rgot : ", response.url, "\ncode : ", response.status_code, color="green")
            elif 200 < resp.status_code < 400:
                log("\rgot : ", response.url, "\ncode : ", response.status_code, color="yellow")
            else:
                log("\rgot : ", response.url, "\ncode : ", response.status_code, color="red")
        if return_final_page_url:
            resp = {"resp": resp, "url": response.url}
        if return_cookies:
            if type(resp) == dict:
                resp.update({"cookies": response.cookies})
            else:
                resp = {"resp": resp, "cookies": response.cookies}
        return resp

    def download(self, url, file_name, headers=None, continue_download=True, bar_end="\n", color="reset", ):
        """
        method to download any file, it will resume download if file already exists
        :param url: url to be downloaded
        :param file_name: file name to be saved as
        :param headers: additional headers to be sent while requesting
        :param continue_download: if True, will resume download if file already exists
        :param bar_end: end of progress bar, default is new line
        :param color: color of progress bar, default is reset
        :return: None
        """
        if headers is None:
            headers = {}
        _headers = self.headers.copy()
        if self.last_html_url:
            _headers['Referer'] = self.last_html_url
        _headers.update(headers)
        try:
            cookies = _headers.pop("Cookie")
        except KeyError:
            cookies = None
        if os.path.exists(file_name):
            if not continue_download:
                raise FileExistsError("file already exists")
            file_size = os.path.getsize(file_name)
            headers['Range'] = f'bytes={file_size}-'
        response = self.session.get(url, headers=_headers, cookies=cookies, stream=True)

        total_size = int(response.headers.get('content-length', 0))
        with open(file_name, 'ab') as file:
            _pbar = pbar(total=total_size, unit='kb')
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                _pbar.update(plus=len(chunk), color=color, finish=bar_end)

    def download_m3u8(self, url, folder_name, headers=None, color="reset"):
        """
        method to download m3u8 file and all its segments in a folder
        :param url: url of m3u8 file to be downloaded IT SHOULD NOT BE A MASTER PLAYLIST (MASTER.m3u8)
        :param folder_name: folder name to be saved as
        :param headers: additional headers to be sent while requesting
        :param color: color of progress bar, default is reset
        :return:
        """
        if headers is None:
            headers = {}
        _headers = self.headers.copy()
        if self.last_html_url:
            _headers['Referer'] = self.last_html_url
        _headers.update(headers)
        response = self.session.get(url, headers=_headers)
        playlist = _parse(response.text)
        segments = playlist['segments']
        self._download_segments(segments, folder_name, color=color)
        return response.text

    def _download_segments(self, segments, folder_name, color="reset"):
        """
        method to download segments of m3u8 file
        :param segments: list from m3u8.parse()['segments']
        :param folder_name: folder name to be saved as
        :param color: color of progress bar, default is reset
        :return: number of segments downloaded
        """
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        bar = pbar(total=len(segments), unit='segment', color=color)
        seg_download_count = 0
        for segment in segments:
            segment_url = segment['uri']
            segment_file_name = segment_url.split("?")[0].split("/")[-1]
            segment_file_path = os.path.join(folder_name, segment_file_name)
            bar.update(seg_download_count, new_line=True)
            self.download(segment_url, segment_file_path, bar_end="\r\033[F\033[F", color=color)
            seg_download_count += 1
        return seg_download_count

    def post(self, url, headers=None, post=True, body=None, notify=True, text=True, return_final_page_url=False,
             return_cookies=False, set_html=False, sleep_for_anti_bot=True):
        return self.get(url=url, headers=headers, post=post, body=body, notify=notify, text=text,
                        return_final_page_url=return_final_page_url,
                        return_cookies=return_cookies, set_html=set_html, sleep_for_anti_bot=sleep_for_anti_bot)
