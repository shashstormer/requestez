from curl_cffi import requests
from typing import Any, Optional, Dict, List
import time
from ..base import BaseSession, BaseAsyncSession

class Session(BaseSession):
    """
    Synchronous Session using curl_cffi for browser impersonation.
    """
    def __init__(self, human_browsing=False, impersonate="chrome124"):
        super().__init__(human_browsing=human_browsing)
        self.session = requests.Session(impersonate=impersonate)

    def _perform_request(self, method: str, url: str, **kwargs) -> Any:
        # curl_cffi supports requests-like API
        return self.session.request(method, url, **kwargs)


class AsyncSession(BaseAsyncSession):
    """
    Asynchronous Session using curl_cffi for browser impersonation.
    """
    def __init__(self, impersonate="chrome124"):
        super().__init__()
        self.impersonate = impersonate
        self._client: Optional[requests.AsyncSession] = None

    async def __aenter__(self):
        self._client = requests.AsyncSession(impersonate=self.impersonate)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client:
            await self._client.close()

    @property
    def client(self) -> requests.AsyncSession:
        if self._client is None:
            raise RuntimeError("Session is not active. Use 'async with AsyncSession() as session:' syntax.")
        return self._client

    async def _perform_request(self, method: str, url: str, **kwargs) -> Any:
        return await self.client.request(method, url, **kwargs)

    async def save_data(self) -> Dict[str, Any]:
        """
        Saves the current session state to a JSON-dumpable dictionary.
        """
        cookies: List[Dict[str, Any]] = []
        for cookie in self.client.cookies.jar:
            cookies.append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "expires": cookie.expires,
                "secure": cookie.secure,
                # httponly handling might vary by cookiejar version
                "httponly": getattr(cookie, "httpOnly", False) if hasattr(cookie, "httpOnly") else False,
            })
        return {"cookies": cookies, "current_url": self._current_url}

    async def load_data(self, data: Dict[str, Any]):
        """
        Loads session state from a dictionary.
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
