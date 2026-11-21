import aiohttp
import pytest

from app import chat, client, live
from app.cache import TTLCache


class FakeResponse:
    def __init__(self, status=200, json=None, text=""):
        self.status = status
        self._json = json
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def json(self):
        return self._json

    async def text(self):
        return self._text

    def raise_for_status(self):
        if self.status >= 400:
            raise aiohttp.ClientResponseError(None, (), status=self.status)


class FakeHttp:
    """Outbound HTTP double: exact-URL routes; unrouted URLs fail like an unreachable host."""

    def __init__(self):
        self.routes = {}
        self.calls = []

    def respond(self, url, status=200, json=None, text=""):
        self.routes[url] = FakeResponse(status, json, text)

    def _request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        result = self.routes.get(url)
        if result is None:
            raise aiohttp.ClientConnectionError(url)
        if isinstance(result, Exception):
            raise result
        return result

    def get(self, url, **kwargs):
        return self._request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._request("POST", url, **kwargs)


@pytest.fixture
def http(monkeypatch):
    fake = FakeHttp()
    monkeypatch.setattr(client, "session", lambda: fake)
    monkeypatch.setattr(chat, "_rate_buckets", {})
    monkeypatch.setattr(live, "_status_cache", TTLCache(60))
    monkeypatch.setattr(live, "_coldfile_cache", TTLCache(1800))
    monkeypatch.setattr(live, "_github_cache", TTLCache(3600))
    return fake
