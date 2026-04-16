import asyncio
import datetime
from http.cookies import Morsel

import httpx
import time
from typing import Optional, Any, Dict, List, Tuple, Literal

READ_AS_OPTIONS = Literal['json', 'text' , 'bytes']

class Session:
    """
    An asynchronous HTTP session class with browser-like context
    and JSON-serializable state persistence.

    Handles 'Referer' headers automatically based on navigation.
    - open(): Simulates opening a new URL (no Referer). Updates current URL.
    - navigate(): Simulates clicking a link (sends Referer). Updates current URL.
    - get()/post()/etc.: Simulates XHR (sends Referer). Does *not* update URL.
    """

    def __init__(self):
        """Initializes the Session."""
        self._client: Optional[httpx.AsyncClient] = None
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

    async def __aenter__(self):
        """Asynchronously initializes the AsyncClient."""
        self._client = httpx.AsyncClient(follow_redirects=True)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Asynchronously closes the AsyncClient."""
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        """Provides access to the underlying httpx.AsyncClient."""
        if self._client is None or self._client.is_closed:
            raise RuntimeError(
                "Session is not active. "
                "Use 'async with Session() as session:' syntax."
            )
        return self._client

    @property
    def current_url(self) -> Optional[str]:
        """Returns the current page URL."""
        return self._current_url

    async def _request(
            self,
            method: str,
            url: str,
            read_as: READ_AS_OPTIONS = "json",
            *,
            suppress_referer: bool = False,
            update_url: bool = False,
            **kwargs,
    ) -> Tuple[int, Any, Any]:
        """
        Internal helper for making HTTP requests.

        Args:
            method (str): HTTP method.
            url (str): The URL to request.
            read_as (str | None): How to read the response body.
                ("json", "text", "bytes", or None).
            suppress_referer (bool): If True, do not send a 'Referer' header.
            update_url (bool): If True, update self._current_url on success.
            **kwargs: Additional arguments for aiohttp.ClientSession.request.

        Returns:
            tuple: (status_code, headers, body)
        """
        headers = {}
        if self.default_headers:
            headers = self.default_headers.copy()
        headers.update(kwargs.get("headers", {}).copy())
        if (
                "Referer" not in headers
                and not suppress_referer
                and self._current_url
        ):
            headers["Referer"] = self._current_url

        kwargs["headers"] = headers

        if "follow_redirects" not in kwargs:
            kwargs["follow_redirects"] = True

        response = await self.client.request(method, url, **kwargs)
        content = None
        try:
            if read_as == "json":
                content = response.json()
            elif read_as == "text":
                content = response.text
            elif read_as == "bytes":
                content = response.content
        except (httpx.DecodingError, asyncio.TimeoutError, Exception) as e:
            print(f"Error reading response body from {url}: {e}")

        if 200 <= response.status_code < 300 and update_url:
            self._current_url = str(response.url)

        return response.status_code, response.headers, content

    async def get(self, url: str, read_as: READ_AS_OPTIONS = "json", **kwargs):
        """
        Performs an async HTTP GET request.
        Sends Referer, does NOT update current URL.
        """
        return await self._request("GET", url, read_as=read_as, **kwargs)

    async def post(self, url: str, read_as: READ_AS_OPTIONS = "json", **kwargs):
        """
        Performs an async HTTP POST request.
        Sends Referer, does NOT update current URL.
        """
        return await self._request("POST", url, read_as=read_as, **kwargs)

    async def put(self, url: str, read_as: READ_AS_OPTIONS = "json", **kwargs):
        """
        Performs an async HTTP PUT request.
        Sends Referer, does NOT update current URL.
        """
        return await self._request("PUT", url, read_as=read_as, **kwargs)

    async def delete(self, url: str, read_as: READ_AS_OPTIONS = "json", **kwargs):
        """
        Performs an async HTTP DELETE request.
        Sends Referer, does NOT update current URL.
        """
        return await self._request("DELETE", url, read_as=read_as, **kwargs)

    async def patch(self, url: str, read_as: READ_AS_OPTIONS = "json", **kwargs):
        """
        Performs an async HTTP PATCH request.
        Sends Referer, does NOT update current URL.
        """
        return await self._request("PATCH", url, read_as=read_as, **kwargs)

    async def navigate(self, url: str, read_as: READ_AS_OPTIONS = "json", **kwargs):
        """
        Simulates navigating to a new page (like clicking a link).
        Sends Referer, DOES update current URL on success.
        """
        return await self._request(
            "GET", url, read_as=read_as, update_url=True, **kwargs
        )

    async def open(self, url: str, read_as: READ_AS_OPTIONS = "json", **kwargs):
        """
        Simulates opening a URL directly (like in an address bar).
        Does NOT send Referer, DOES update current URL on success.
        """
        return await self._request(
            "GET", url, read_as=read_as, suppress_referer=True, update_url=True, **kwargs
        )

    async def save_data(self) -> Dict[str, Any]:
        """
        Saves the current session state to a JSON-dumpable dictionary.

        Returns:
            dict: A dictionary containing cookies and the current URL.
        """
        cookies: List[Dict[str, Any]] = []
        for cookie in self.client.cookies.jar:
            cookies.append(
                {
                    "name": cookie.name,
                    "value": cookie.value,
                    "domain": cookie.domain,
                    "path": cookie.path,
                    "expires": cookie.expires,
                    "secure": cookie.secure,
                    "httponly": cookie.has_nonstandard_attr("HttpOnly"),
                }
            )
        return {"cookies": cookies, "current_url": self._current_url}

    async def load_data(self, data: Dict[str, Any]):
        """
        Loads session state from a dictionary (e.g., from a database).

        Args:
            data (dict): A dictionary in the format provided by save_data().
        """
        self.client.cookies.clear()
        self._current_url = data.get("current_url")

        now = int(time.time())

        for cookie_dict in data.get("cookies", []):
            expires = cookie_dict.get("expires")
            if expires is not None and expires < now:
                continue

            self.client.cookies.set(
                name=cookie_dict["name"],
                value=cookie_dict["value"],
                domain=cookie_dict.get("domain", ""),
                path=cookie_dict.get("path", "/"),
            )