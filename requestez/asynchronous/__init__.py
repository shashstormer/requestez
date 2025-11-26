import asyncio
import datetime
from http.cookies import Morsel

import aiohttp
import time
from typing import Optional, Any, Dict, List, Tuple


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
        self._client: Optional[aiohttp.ClientSession] = None
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
        """Asynchronously initializes the ClientSession."""
        self._client = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar())
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Asynchronously closes the ClientSession."""
        if self._client:
            await self._client.close()

    @property
    def client(self) -> aiohttp.ClientSession:
        """Provides access to the underlying aiohttp.ClientSession."""
        if self._client is None or self._client.closed:
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
            read_as: Optional[str] = "json",
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
        # Prepare headers, adding Referer if not manually overridden
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

        async with self.client.request(method, url, **kwargs) as response:
            content = None
            try:
                if read_as == "json":
                    content = await response.json()
                elif read_as == "text":
                    content = await response.text()
                elif read_as == "bytes":
                    content = await response.read()
                else:
                    response.release()
            except (aiohttp.ContentTypeError, asyncio.TimeoutError, Exception) as e:
                print(f"Error reading response body from {url}: {e}")
                response.release()

            # Update current URL if navigation was successful
            if 200 <= response.status < 300 and update_url:
                self._current_url = str(response.url)

            return response.status, response.headers, content

    async def get(self, url: str, read_as: Optional[str] = "json", **kwargs):
        """
        Performs an async HTTP GET request.
        Sends Referer, does NOT update current URL.
        """
        return await self._request("GET", url, read_as=read_as, **kwargs)

    async def post(self, url: str, read_as: Optional[str] = "json", **kwargs):
        """
        Performs an async HTTP POST request.
        Sends Referer, does NOT update current URL.
        """
        return await self._request("POST", url, read_as=read_as, **kwargs)

    async def put(self, url: str, read_as: Optional[str] = "json", **kwargs):
        """
        Performs an async HTTP PUT request.
        Sends Referer, does NOT update current URL.
        """
        return await self._request("PUT", url, read_as=read_as, **kwargs)

    async def delete(self, url: str, read_as: Optional[str] = "json", **kwargs):
        """
        Performs an async HTTP DELETE request.
        Sends Referer, does NOT update current URL.
        """
        return await self._request("DELETE", url, read_as=read_as, **kwargs)

    async def patch(self, url: str, read_as: Optional[str] = "json", **kwargs):
        """
        Performs an async HTTP PATCH request.
        Sends Referer, does NOT update current URL.
        """
        return await self._request("PATCH", url, read_as=read_as, **kwargs)

    async def navigate(self, url: str, read_as: Optional[str] = "json", **kwargs):
        """
        Simulates navigating to a new page (like clicking a link).
        Sends Referer, DOES update current URL on success.
        """
        return await self._request(
            "GET", url, read_as=read_as, update_url=True, **kwargs
        )

    async def open(self, url: str, read_as: Optional[str] = "json", **kwargs):
        """
        Simulates opening a URL directly (like in an address bar).
        Does NOT send Referer, DOES update current URL on success.
        """
        return await self._request(
            "GET", url, read_as=read_as, suppress_referer=True, update_url=True, **kwargs
        )

    def _create_cookie_from_dict(
            self, d: Dict[str, Any]
    ) -> Morsel:
        """Helper to create a Morsel object from a dictionary."""
        name = d.get("name")
        value = d.get("value")

        m = Morsel()
        m.set(name, value, value)

        if d.get("domain"):
            m["domain"] = d.get("domain")
        if d.get("path"):
            m["path"] = d.get("path")

        epoch_seconds = d.get("expires")
        if epoch_seconds:
            try:
                dt = datetime.datetime.fromtimestamp(epoch_seconds, tz=datetime.timezone.utc)
                m["expires"] = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
            except (TypeError, ValueError, OSError):
                pass

        if d.get("secure"):
            m["secure"] = True
        if d.get("httponly"):
            m["httponly"] = True

        return m

    async def save_data(self) -> Dict[str, Any]:
        """
        Saves the current session state to a JSON-dumpable dictionary.

        Returns:
            dict: A dictionary containing cookies and the current URL.
        """
        cookies: List[Dict[str, Any]] = []
        for cookie in self.client.cookie_jar:
            httponly = False
            if hasattr(cookie, "rest"):
                httponly = cookie.rest.get("HttpOnly", cookie.rest.get("httponly"))

            cookies.append(
                {
                    "name": cookie.key,
                    "value": cookie.value,
                    "domain": getattr(cookie, "domain", ""),
                    "path": getattr(cookie, "path", "/"),
                    "expires": getattr(cookie, "expires", None),
                    "secure": getattr(cookie, "secure", False),
                    "httponly": bool(httponly),
                }
            )
        return {"cookies": cookies, "current_url": self._current_url}

    async def load_data(self, data: Dict[str, Any]):
        """
        Loads session state from a dictionary (e.g., from a database).

        Args:
            data (dict): A dictionary in the format provided by save_data().
        """
        jar = self.client.cookie_jar
        jar.clear()
        self._current_url = data.get("current_url")

        now = int(time.time())

        for cookie_dict in data.get("cookies", []):
            expires = cookie_dict.get("expires")
            if expires is not None and expires < now:
                continue  # Skip expired cookie

            morsel = self._create_cookie_from_dict(cookie_dict)
            if morsel.key:
                jar.update_cookies({morsel.key: morsel})
            else:
                print('Failed to load cookie due to missing name')