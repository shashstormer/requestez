import httpx
import time
import asyncio
from typing import Optional, Any, Dict, List, Tuple
from ..base import BaseAsyncSession

class Session(BaseAsyncSession):
    """
    Standard Asynchronous Session using httpx.
    """
    def __init__(self):
        super().__init__()
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(follow_redirects=True)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            raise RuntimeError("Session is not active. Use 'async with Session() as session:' syntax.")
        return self._client

    async def _perform_request(self, method: str, url: str, **kwargs) -> Any:
        if "follow_redirects" not in kwargs:
            kwargs["follow_redirects"] = True
        return await self.client.request(method, url, **kwargs)

    async def save_data(self) -> Dict[str, Any]:
        cookies: List[Dict[str, Any]] = []
        for cookie in self.client.cookies.jar:
            cookies.append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "expires": cookie.expires,
                "secure": cookie.secure,
                "httponly": cookie.has_nonstandard_attr("HttpOnly"),
            })
        return {"cookies": cookies, "current_url": self._current_url}

    async def load_data(self, data: Dict[str, Any]):
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