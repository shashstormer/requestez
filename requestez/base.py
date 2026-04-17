import abc
import os
import random
import time
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from requests.structures import CaseInsensitiveDict
from m3u8 import parse as _parse
from .helpers import log, pbar

try:
    from moviepy.video.io.VideoFileClip import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    VideoFileClip = None
    MOVIEPY_AVAILABLE = False


class BaseSession(ABC):
    """
    Abstract Base Class for Synchronous Sessions.
    Contains common logic for Referer tracking, downloader, and anti-bot measures.
    """
    def __init__(self, human_browsing=False):
        self.headers = CaseInsensitiveDict({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/114.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                      'image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
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

    @abstractmethod
    def _perform_request(self, method: str, url: str, **kwargs) -> Any:
        """Must return a response object with: status_code, headers, url, text, content, and iter_content()"""
        pass

    def where_to(self, url, headers=None, post=False, body=None, notify=True):
        if headers is None:
            headers = {}
        _headers = self.headers.copy()
        if self.last_html_url:
            _headers['Referer'] = self.last_html_url
        _headers.update(headers)
        if notify:
            log("getting :", url, end="", color="yellow")
        
        kwargs = {"headers": _headers, "allow_redirects": False}
        if post:
            kwargs["data"] = body
            resp = self._perform_request("POST", url, **kwargs)
        else:
            resp = self._perform_request("GET", url, **kwargs)
            
        if notify:
            log("\rgot : ", resp.url, "\ncode : ", resp.status_code, color="green")
        
        ret = {
            "to": resp.headers.get("Location", url),
            "headers": resp.headers,
            "cookies": getattr(resp, "cookies", {})
        }
        return ret

    def get(self, url, headers=None, post=False, body=None, notify=True, text=True, return_final_page_url=False,
            return_cookies=False, set_html=True, sleep_for_anti_bot=True):
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
        
        kwargs = {"headers": _headers, "timeout": 60}
        if post:
            kwargs["data"] = body
            response = self._perform_request("POST", url, **kwargs)
        else:
            response = self._perform_request("GET", url, **kwargs)

        if 'text/html' in response.headers.get('Content-Type', '') and set_html:
            self.last_html_url = str(response.url)
        
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
            cookies = getattr(response, "cookies", {})
            if isinstance(resp, dict):
                resp.update({"cookies": cookies})
            else:
                resp = {"resp": resp, "cookies": cookies}
        return resp

    def post(self, url, headers=None, post=True, body=None, notify=True, text=True, return_final_page_url=False,
             return_cookies=False, set_html=False, sleep_for_anti_bot=True):
        return self.get(url=url, headers=headers, post=post, body=body, notify=notify, text=text,
                        return_final_page_url=return_final_page_url,
                        return_cookies=return_cookies, set_html=set_html, sleep_for_anti_bot=sleep_for_anti_bot)

    def download(self, url, file_name, headers=None, continue_download=True, bar_end="\n", color="reset", quiet=False):
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
            
        response = self._perform_request("GET", url, headers=_headers, cookies=cookies, stream=True)
        
        total_size = int(response.headers.get('content-length', 0))
        with open(file_name, 'ab') as file:
            if not quiet:
                _pbar = pbar(total=total_size, unit='kb')
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                if not quiet:
                    _pbar.update(plus=len(chunk), color=color, finish=bar_end)

    def download_m3u8(self, url, folder_name, headers=None, color="reset", multiple_threads=False, max_threads=5):
        if headers is None:
            headers = {}
        _headers = self.headers.copy()
        if self.last_html_url:
            _headers['Referer'] = self.last_html_url
        _headers.update(headers)
        
        response = self.get(url, headers=_headers, text=False)
        playlist = _parse(response.text)
        segments = playlist['segments']
        domain_start = "/".join(url.split('/')[:-1])
        count, paths = self._download_segments(segments, folder_name, domain=domain_start, color=color,
                                               multiple_threads=multiple_threads, max_threads=max_threads)
        return [response.text, count, paths]

    def _download_segments(self, segments, folder_name, domain, color="reset", multiple_threads=False, max_threads=5):
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
        folder_name = file_name.split(".")[0]
        playlist, count, paths = self.download_m3u8(url, folder_name, headers=headers, color=color,
                                                    multiple_threads=multiple_threads, max_threads=max_threads)
        output_file_name = file_name
        success = self._join_segments(output_file_name, paths[0], color=color)
        return [playlist, count, paths, success]


class BaseAsyncSession(ABC):
    """
    Abstract Base Class for Asynchronous Sessions.
    Contains common logic for Referer tracking and browser-like navigation.
    """
    def __init__(self):
        self._current_url: Optional[str] = None
        self.default_headers: Dict[str, str] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/114.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                      'image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            "SEC-CH-UA-MOBILE": "?0",
            "SEC-CH-UA-PLATFORM": "Linux",
        }

    @property
    def current_url(self) -> Optional[str]:
        return self._current_url

    @abstractmethod
    async def _perform_request(self, method: str, url: str, **kwargs) -> Any:
        """Must return a response object with: status_code, headers, url, text, content, json()"""
        pass

    async def _request(
            self,
            method: str,
            url: str,
            read_as: str = "json",
            *,
            suppress_referer: bool = False,
            update_url: bool = False,
            **kwargs,
    ) -> Tuple[int, Any, Any]:
        headers = self.default_headers.copy()
        headers.update(kwargs.get("headers", {}).copy())
        if (
                "Referer" not in headers
                and not suppress_referer
                and self._current_url
        ):
            headers["Referer"] = self._current_url

        kwargs["headers"] = headers
        
        response = await self._perform_request(method, url, **kwargs)
        
        content = None
        try:
            if read_as == "json":
                content = response.json()
            elif read_as == "text":
                content = response.text
            elif read_as == "bytes":
                content = response.content
        except Exception as e:
            print(f"Error reading response body from {url}: {e}")

        if 200 <= response.status_code < 300 and update_url:
            self._current_url = str(response.url)

        return response.status_code, response.headers, content

    async def get(self, url: str, read_as: str = "json", **kwargs):
        return await self._request("GET", url, read_as=read_as, **kwargs)

    async def post(self, url: str, read_as: str = "json", **kwargs):
        return await self._request("POST", url, read_as=read_as, **kwargs)

    async def put(self, url: str, read_as: str = "json", **kwargs):
        return await self._request("PUT", url, read_as=read_as, **kwargs)

    async def delete(self, url: str, read_as: str = "json", **kwargs):
        return await self._request("DELETE", url, read_as=read_as, **kwargs)

    async def patch(self, url: str, read_as: str = "json", **kwargs):
        return await self._request("PATCH", url, read_as=read_as, **kwargs)

    async def navigate(self, url: str, read_as: str = "json", **kwargs):
        return await self._request("GET", url, read_as=read_as, update_url=True, **kwargs)

    async def open(self, url: str, read_as: str = "json", **kwargs):
        return await self._request("GET", url, read_as=read_as, suppress_referer=True, update_url=True, **kwargs)

    @abstractmethod
    async def save_data(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def load_data(self, data: Dict[str, Any]):
        pass
