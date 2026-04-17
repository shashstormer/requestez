import requests
from typing import Any
from .base import BaseSession

class Session(BaseSession):
    """
    Standard Synchronous Session using requests.
    """
    def __init__(self, human_browsing=False):
        super().__init__(human_browsing=human_browsing)
        self.session = requests.Session()

    def _perform_request(self, method: str, url: str, **kwargs) -> Any:
        return self.session.request(method, url, **kwargs)
