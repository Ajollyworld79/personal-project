"""Live data on the site: service status, The Cold File channel, GitHub activity and the apology demo."""
import asyncio
import json
import os
import random
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import aiohttp
from quart import Blueprint, current_app, jsonify

from app import client
from app.cache import TTLCache

bp = Blueprint("live", __name__)


@bp.get("/api/get-apology")
async def get_apology():
    """Fetch a live apology from the MCP server with robust parsing and fallbacks."""
    severity = random.choice(["TRIVIAL", "MINOR", "MAJOR", "CRITICAL", "NUCLEAR"])
    # Every style the server's Style enum accepts (unknown values silently become CASUAL).
    style = random.choice([
        "PROFESSIONAL", "CASUAL", "POETIC", "GROVELING", "HAIKU",
        "LEGAL_DISCLAIMER", "CORPORATE_DOUBLESPEAK", "SHAKESPEAREAN", "PIRATE",
        "PASSIVE_AGGRESSIVE", "GEN_Z", "VIKING", "ROBOT", "EXISTENTIAL", "SOAP_OPERA",
    ])
    context = "the live demo button"

    try:
        # The MCP server's /demo endpoint is a plain HTTP wrapper around
        # generate_apology — perfect for a one-shot button click.
        demo_url = "https://apology-as-a-service-production.up.railway.app/demo"
        params = {"severity": severity, "style": style, "context": context}
        async with client.session().get(demo_url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                apology_text = data.get("text")
            else:
                current_app.logger.warning("Demo endpoint returned %s", resp.status)
                apology_text = None

        # Use fallback if live generation failed
        if not apology_text:
            current_app.logger.info("apology: using canned fallback")
            canned = {
                "TRIVIAL": [
                    f"Oops, a tiny glitch with {context}. Fixed it!",
                    f"My bad on {context}. All good now.",
                ],
                "MINOR": [
                    f"Sorry about the issue with {context}. We're sorting it out.",
                    f"A small hiccup with {context}. Apologies!",
                ],
                "MAJOR": [
                    f"We deeply regret the trouble with {context}. Fixing it is our top priority.",
                    f"I really dropped the ball on {context}. Working overtime to fix it.",
                ],
                "CRITICAL": [
                    f"Critical failure regarding {context}. We are all hands on deck.",
                    f"I am on my knees. {context} is broken and it is my fault.",
                ],
                "NUCLEAR": [
                    f"We accept full responsibility for the total destruction of {context}. Goodbye.",
                    f"Resume updated. {context} is gone. I am sorry.",
                ],
            }
            apology_text = random.choice(canned[severity])
            meta_suffix = " (Live connection failed - using cached response)"
        else:
            meta_suffix = ""

        return jsonify(
            {
                "apology": apology_text,
                "meta": f"Generated via MCP (Severity: {severity}, Style: {style}){meta_suffix}",
            }
        )

    except Exception:
        current_app.logger.exception("apology endpoint critical failure")
        return jsonify({"error": "Apology service unavailable"}), 500


# --- YouTube channels run by autonomous pipelines (no API key needed) ----------
_ATOM_NS = {
    "a": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}
_INITIAL_DATA = re.compile(r"var ytInitialData = (\{.*?\});</script>", re.S)
_VIDEO_COUNT = re.compile(r"^(\d[\d,]*) videos?$")
_DURATION = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{2})$")
_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": "SOCS=CAI",  # skips the EU consent interstitial
}


def _parse_uploads_page(html: str) -> dict | None:
    """{"upload_count", "runtime_minutes": [shortest, longest] | None} or None if the count is missing."""
    match = _INITIAL_DATA.search(html)
    if not match:
        return None

    def dicts(node):
        """Every dict in the tree, depth-first in document order."""
        if isinstance(node, dict):
            yield node
            for value in node.values():
                yield from dicts(value)
        elif isinstance(node, list):
            for value in node:
                yield from dicts(value)

    def first_duration(tile: dict) -> int | None:
        for node in dicts(tile):
            text = node.get("text")
            if isinstance(text, str) and (found := _DURATION.match(text)):
                return int(found.group(1) or 0) * 3600 + int(found.group(2)) * 60 + int(found.group(3))
        return None

    count: int | None = None
    seconds: list[int] = []
    for node in dicts(json.loads(match.group(1))):
        runs = node.get("runs")
        if count is None and isinstance(runs, list):
            label = "".join(r.get("text", "") for r in runs if isinstance(r, dict)).strip()
            if found := _VIDEO_COUNT.match(label):
                count = int(found.group(1).replace(",", ""))
        if "lockupViewModel" in node and (length := first_duration(node["lockupViewModel"])):
            seconds.append(length)
    if count is None:
        return None
    runtime = [min(seconds) // 60, -(-max(seconds) // 60)] if seconds else None
    return {"upload_count": count, "runtime_minutes": runtime}


class Channel:
    """A YouTube channel published by one of the pipelines.

    Latest uploads come from the RSS feed (capped at 15 entries, refreshed every
    30 min). The real upload count and runtimes come from the long-form uploads
    playlist (UULF…, Shorts excluded), recounted every 6 hours; YouTube offers
    no key-free API for this, so the page's embedded ytInitialData is parsed and
    the feed count is the fallback.
    """

    def __init__(self, slug: str, handle: str, channel_id: str, noun: str, max_age_days: int) -> None:
        self.slug = slug
        self.url = f"https://www.youtube.com/@{handle}"
        self.feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        self.uploads_url = f"https://www.youtube.com/playlist?list=UULF{channel_id[2:]}"
        self.noun = noun
        # The pipeline counts as running while uploads keep within its cadence (+ slack).
        self.max_age_days = max_age_days
        self.feed_cache: TTLCache[dict] = TTLCache(1800)
        self.stats_cache: TTLCache[dict] = TTLCache(6 * 3600)

    async def feed(self) -> dict | None:
        """Fresh feed data, else the last good copy, else None."""
        return await self.feed_cache.get(self._fetch_feed) or self.feed_cache.value

    async def payload(self) -> dict | None:
        feed = await self.feed()
        if not feed:
            return None
        stats = await self.stats_cache.get(self._fetch_stats) or self.stats_cache.value
        if stats:
            return {**feed, **stats, "upload_count_exact": True}
        return {**feed, "upload_count_exact": False, "runtime_minutes": None}

    async def _fetch_feed(self) -> dict | None:
        log = current_app.logger
        try:
            async with client.session().get(self.feed_url) as resp:
                if resp.status != 200:
                    return None
                xml_body = await resp.text()
        except Exception:
            log.exception("%s: RSS fetch failed", self.slug)
            return None
        try:
            uploads = []
            for entry in ET.fromstring(xml_body).findall("a:entry", _ATOM_NS):
                vid = entry.find("yt:videoId", _ATOM_NS)
                title = entry.find("a:title", _ATOM_NS)
                published = entry.find("a:published", _ATOM_NS)
                if vid is None or title is None or published is None:
                    continue
                uploads.append({
                    "video_id": vid.text,
                    "title": title.text,
                    "published": published.text,
                    "thumbnail": f"https://i.ytimg.com/vi/{vid.text}/hqdefault.jpg",
                })
        except Exception:
            log.exception("%s: RSS parse failed", self.slug)
            return None
        if not uploads:
            return None
        return {
            "channel_url": self.url,
            "upload_count": len(uploads),
            "latest": uploads[0],
            "uploads": uploads[:3],
        }

    async def _fetch_stats(self) -> dict | None:
        log = current_app.logger
        try:
            async with client.session().get(self.uploads_url, headers=_BROWSER_HEADERS) as resp:
                if resp.status != 200:
                    log.warning("%s: uploads page returned %s", self.slug, resp.status)
                    return None
                html = await resp.text()
            stats = _parse_uploads_page(html)
        except Exception:
            log.exception("%s: uploads page failed", self.slug)
            return None
        if stats is None:
            log.warning("%s: uploads page had no video count", self.slug)
        return stats


CHANNELS = {channel.slug: channel for channel in [
    # Releases every 5–8 days.
    Channel("cold-file", "The_Cold_File", os.getenv("COLDFILE_CHANNEL_ID", "UCN8k1J6MXu-ucl6anByx_oQ"),
            noun="episode", max_age_days=9),
]}


@bp.get("/api/channel/<slug>")
async def channel(slug: str):
    """Live data for a pipeline's YouTube channel: latest uploads, real count, runtimes."""
    chan = CHANNELS.get(slug)
    if chan is None:
        return jsonify({"error": "unknown channel"}), 404
    data = await chan.payload()
    if not data:
        return jsonify({"error": "channel data unavailable"}), 503
    return jsonify(data)


# --- Production status board -------------------------------------------------
# Pings the live Railway deployments in parallel and caches for 60s so a page
# load never fans out more than once a minute.
_status_cache: TTLCache[dict] = TTLCache(60)

_STATUS_SERVICES = [
    {
        "id": "portfolio",
        "name": "gustavchristensen.dev",
        "desc": "this site — async Quart + RAG chat proxy",
        "kind": "web",
        "url": "https://gustavchristensen.dev/",
        "check": "https://gustavchristensen.dev/",
    },
    {
        "id": "llm-assistant",
        "name": "llm-assistant",
        "desc": "RAG backend — answers the CV chat on this page",
        "kind": "web",
        "url": "https://llm-assistant-production-aa36.up.railway.app/",
        "check": "https://llm-assistant-production-aa36.up.railway.app/health",
    },
    {
        "id": "doc-intel",
        "name": "document-intelligence",
        "desc": "OCR + structured document extraction demo",
        "kind": "web",
        "url": "https://document-intelligence-pipeline-production.up.railway.app/",
        "check": "https://document-intelligence-pipeline-production.up.railway.app/health",
    },
    {
        "id": "apology",
        "name": "apology-as-a-service",
        "desc": "public MCP server (Streamable HTTP + SSE) for AI agents",
        "kind": "mcp",
        "url": "https://github.com/Ajollyworld79/Apology-as-a-Service",
        "check": "https://apology-as-a-service-production.up.railway.app/health",
    },
    # A scheduled pipeline, not an HTTP service: status comes from the latest upload.
    {
        "id": "cold-file",
        "name": "the-cold-file",
        "desc": "autonomous true-crime podcast pipeline on Railway",
        "kind": "pipeline",
        "url": CHANNELS["cold-file"].url,
        "channel": "cold-file",
    },
]


async def _probe_service(http: aiohttp.ClientSession, svc: dict, timeout: aiohttp.ClientTimeout) -> dict:
    result = {
        "id": svc["id"],
        "name": svc["name"],
        "desc": svc["desc"],
        "kind": svc["kind"],
        "url": svc["url"],
        "status": "down",
        "latency_ms": None,
    }
    if svc.get("channel"):
        return await _pipeline_status(result, CHANNELS[svc["channel"]])
    t0 = time.perf_counter()
    try:
        async with http.get(svc["check"], headers={"User-Agent": "portfolio-status"}, timeout=timeout) as resp:
            result["latency_ms"] = int((time.perf_counter() - t0) * 1000)
            result["status"] = "up" if resp.status < 500 else "down"
    except Exception:
        result["latency_ms"] = None
        result["status"] = "down"
    return result


async def _pipeline_status(result: dict, chan: Channel) -> dict:
    """Up while uploads keep within the pipeline's cadence, idle after that."""
    try:
        latest = ((await chan.feed()) or {}).get("latest")
        if latest:
            age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(latest["published"])).days
            result["status"] = "up" if age_days <= chan.max_age_days else "idle"
            result["detail"] = f"last {chan.noun} {age_days}d ago"
    except Exception:
        current_app.logger.exception("status: %s check failed", chan.slug)
    return result


async def _check_services() -> dict:
    http = client.session()
    timeout = aiohttp.ClientTimeout(total=6.0)
    services = await asyncio.gather(*[_probe_service(http, svc, timeout) for svc in _STATUS_SERVICES])
    return {
        "services": list(services),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@bp.get("/api/status")
async def production_status():
    """Live health of every production deployment, checked in parallel."""
    return jsonify(await _status_cache.get(_check_services))


# --- GitHub activity (contribution heatmap) ---
# Cached for 1 hour to stay well under GitHub's 5000 req/hr quota.
_github_cache: TTLCache[dict] = TTLCache(3600)
_GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "Ajollyworld79")

_GITHUB_QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount weekday }
        }
      }
    }
  }
}
"""


class _GitHubUnavailable(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


async def _fetch_public_preview() -> dict | None:
    """Local preview: the site's already-public calendar, fetched without credentials."""
    try:
        async with client.session().get("https://gustavchristensen.dev/api/github-activity") as resp:
            resp.raise_for_status()
            public_data = await resp.json()
        if public_data.get("username") != _GITHUB_USERNAME:
            raise ValueError("Preview calendar belongs to another user")
        if not isinstance(public_data.get("weeks"), list) or not isinstance(public_data.get("total"), int):
            raise ValueError("Invalid preview calendar")
        return public_data
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
        current_app.logger.warning("Public GitHub preview calendar unavailable")
        return None


async def _fetch_github() -> dict:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        # Opt-in for local preview; production uses its own GitHub token.
        if os.getenv("GITHUB_ACTIVITY_PREVIEW") == "1" and (preview := await _fetch_public_preview()):
            return preview
        raise _GitHubUnavailable(503, "GITHUB_TOKEN not configured")

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "gustavchristensen.dev-portfolio",
        "Accept": "application/json",
    }
    payload = {"query": _GITHUB_QUERY, "variables": {"username": _GITHUB_USERNAME}}
    async with client.session().post("https://api.github.com/graphql", headers=headers, json=payload) as resp:
        if resp.status != 200:
            current_app.logger.warning("github graphql %s: %s", resp.status, (await resp.text())[:200])
            raise _GitHubUnavailable(502, f"GitHub API {resp.status}")
        body = await resp.json()

    user = (body.get("data") or {}).get("user")
    if not user:
        current_app.logger.warning("github graphql empty user: %s", (body.get("errors") or [])[:2])
        raise _GitHubUnavailable(502, "GitHub returned no user data")

    cal = user["contributionsCollection"]["contributionCalendar"]
    return {
        "username": _GITHUB_USERNAME,
        "total": cal["totalContributions"],
        "weeks": cal["weeks"],
    }


@bp.get("/api/github-activity")
async def github_activity():
    """GitHub contribution-calendar data; the last good copy is served as `_stale` on failure."""
    try:
        return jsonify(await _github_cache.get(_fetch_github))
    except _GitHubUnavailable as exc:
        status, message = exc.status, exc.message
    except Exception:
        current_app.logger.exception("github-activity endpoint failed")
        status, message = 500, "GitHub activity unavailable"
    if _github_cache.value:
        return jsonify({**_github_cache.value, "_stale": True})
    return jsonify({"error": message}), status
