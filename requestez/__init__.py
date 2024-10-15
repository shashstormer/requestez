import random
import time
import requests
import os
from m3u8 import parse as _parse
from requests.structures import CaseInsensitiveDict
from .helpers import log, pbar
import threading

try:
    from moviepy.video.io.VideoFileClip import VideoFileClip

    MOVIEPY_AVAILABLE = True
except ImportError:
    VideoFileClip = None
    MOVIEPY_AVAILABLE = False


class Session:
    def __init__(self, human_browsing=False):
        """
        :param human_browsing: not required in most cases, you may use this in case of ratelimits or anti-bot measures
        """
        self.session = requests.Session()
        self.headers = CaseInsensitiveDict({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/114.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                      'image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            # 'Accept-Encoding': 'gzip, deflate, br',
            # you can add this if you want but will have to implement decompression
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
            "headers": "headers",  # CaseInsensitive dict
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
            if response.status_code == 200:
                log("\rgot : ", response.url, "\ncode : ", response.status_code, color="green")
            elif 200 < response.status_code < 400:
                log("\rgot : ", response.url, "\ncode : ", response.status_code, color="yellow")
            else:
                log("\rgot : ", response.url, "\ncode : ", response.status_code, color="red")
        if return_final_page_url:
            resp = {"resp": resp, "url": response.url}
        if return_cookies:
            if isinstance(resp, dict):
                resp.update({"cookies": response.cookies})
            else:
                resp = {"resp": resp, "cookies": response.cookies}
        return resp

    def download(self, url, file_name, headers=None, continue_download=True, bar_end="\n", color="reset", quiet=False):
        """
        method to download any file, it will resume download if file already exists
        :param quiet: True to not print anything, False to print Status
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
            if not continue_download and not quiet:
                raise FileExistsError("file already exists")
            if not continue_download and quiet:
                return False
            file_size = os.path.getsize(file_name)
            headers['Range'] = f'bytes={file_size}-'
        response = self.session.get(url, headers=_headers, cookies=cookies, stream=True)

        total_size = int(response.headers.get('content-length', 0))
        with open(file_name, 'ab') as file:
            if not quiet:
                _pbar = pbar(total=total_size, unit='kb')
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                if not quiet:
                    _pbar.update(plus=len(chunk), color=color, finish=bar_end)

    def download_m3u8(self, url, folder_name, headers=None, color="reset", multiple_threads=False, max_threads=5):
        """
        method to download m3u8 file and all its segments in a folder.
        :param max_threads: Max threads to spawn when downloading in multithreaded mode.
        :param multiple_threads: Download using multiple threads (for servers with each request speed cap will improve speed but may download slower if insufficient bandwidth on client)
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
        domain_start = "/".join(url.split('/')[:-1])
        count, paths = self._download_segments(segments, folder_name, domain=domain_start, color=color,
                                               multiple_threads=multiple_threads, max_threads=max_threads)
        return [response.text, count, paths]

    def _download_segments(self, segments, folder_name, domain, color="reset", multiple_threads=False, max_threads=5):
        """
        method to download segments of a m3u8 file
        :param segments: list from m3u8.parse()['segments']
        :param folder_name: folder name to be saved as
        :param color: color of progress bar, default is reset
        :return: number of segments downloaded
        """
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        bar = pbar(total=len(segments), unit='segment', color=color)
        seg_download_count = 0
        file_names = []
        thread_list = []
        for segment in segments:
            if not segment['uri'].startswith("http"):
                segment_url = f"{domain}/{segment['uri']}"
            else:
                segment_url = segment['uri']
            segment_file_name = segment_url.split("?")[0].split("/")[-1]
            segment_file_path = os.path.join(folder_name, segment_file_name)
            if multiple_threads:
                bar.update(seg_download_count, new_line=False)
            else:
                bar.update(seg_download_count, new_line=True)
            file_names.append(segment_file_path)
            if multiple_threads:
                while len(thread_list) >= max_threads:
                    for thread in thread_list:
                        if not thread.is_alive():
                            thread_list.remove(thread)
                thread = threading.Thread(target=self.download, args=(
                segment_url, segment_file_path, None, False, "\r\033[F\033[F", color, True))
                thread.start()
                thread_list.append(thread)
            else:
                self.download(segment_url, segment_file_path, bar_end="\r\033[F\033[F", color=color)
            seg_download_count += 1
        else:
            while len(thread_list) != 0:
                for thread in thread_list:
                    if not thread.is_alive():
                        thread_list.remove(thread)
        return [seg_download_count, [file_names, folder_name]]

    @staticmethod
    def _join_segments(output_file_name, segment_paths, color="reset"):
        if not MOVIEPY_AVAILABLE:
            log("moviepy not installed", color="red", log_level="c")
            log("install moviepy to use this feature", color="red", log_level="c")
            log("pip install moviepy[optional]", color="red", log_level="c")
            log("or", color="red", log_level="c")
            log("pip install requestez[optional]", color="red", log_level="c")
            return False
        log("joining segments", color=color)
        bar = pbar(total=len(segment_paths), unit='segment', color=color)
        for segment_path in segment_paths:
            bar.update(plus=1, new_line=False)
            clip = VideoFileClip(segment_path)
            clip.write_videofile(output_file_name, append=True, codec='libx264', audio_codec='aac')
        return True

    def download_m3u8_as_mp4(self, url, file_name, headers=None, color="reset", multiple_threads=False, max_threads=5):
        """
        method to download m3u8 file and all its segments in a folder.
        :param max_threads: Max threads to spawn when downloading in multithreaded mode.
        :param multiple_threads: Download using multiple threads (for servers with each request speed cap will improve speed but may download slower if insufficient bandwidth on client)
        :param url: url of m3u8 file to be downloaded IT SHOULD NOT BE A MASTER PLAYLIST (MASTER.m3u8)
        :param file_name: file name to be saved as
        :param headers: additional headers to be sent while requesting
        :param color: color of progress bar, default is reset
        :return:
        """
        folder_name = file_name.split(".")[0]
        playlist, count, paths = self.download_m3u8(url, folder_name, headers=headers, color=color,
                                                    multiple_threads=multiple_threads, max_threads=max_threads)
        output_file_name = file_name
        success = self._join_segments(output_file_name, paths[0], color=color)
        return [playlist, count, paths, success]

    def post(self, url, headers=None, post=True, body=None, notify=True, text=True, return_final_page_url=False,
             return_cookies=False, set_html=False, sleep_for_anti_bot=True):
        return self.get(url=url, headers=headers, post=post, body=body, notify=notify, text=text,
                        return_final_page_url=return_final_page_url,
                        return_cookies=return_cookies, set_html=set_html, sleep_for_anti_bot=sleep_for_anti_bot)
