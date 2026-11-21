"""One pooled HTTP client for every outbound call, created lazily inside the running event loop."""
import ssl

import aiohttp
import certifi

# certifi lets aiohttp verify TLS certificates on Homebrew/portable Python builds
# that lack a system CA bundle.
_SSL_CTX = ssl.create_default_context(cafile=certifi.where())
_session: aiohttp.ClientSession | None = None


def session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=_SSL_CTX),
            timeout=aiohttp.ClientTimeout(total=10.0),
            # The session is shared by every visitor: a cookie stored from one
            # upstream response would be replayed for all of them (llm-assistant
            # caps each session cookie at 20 questions a day).
            cookie_jar=aiohttp.DummyCookieJar(),
        )
    return _session


async def close() -> None:
    if _session is not None:
        await _session.close()
