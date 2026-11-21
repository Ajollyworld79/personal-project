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
    style = random.choice([
        "PROFESSIONAL", "CASUAL", "POETIC", "GROVELING", "HAIKU",
        "LEGAL_DISCLAIMER", "CORPORATE_DOUBLESPEAK", "SHAKESPEAREAN", "PIRATE",
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
        "desc": "live MCP server (SSE) for AI agents",
        "kind": "mcp",
        "url": "https://github.com/Ajollyworld79/Apology-as-a-Service",
        "check": "https://apology-as-a-service-production.up.railway.app/health",
    },
    {
        "id": "cold-file",
        "name": "the-cold-file",
        "desc": "autonomous podcast pipeline — hourly on Railway",
        "kind": "pipeline",
        "url": "https://www.youtube.com/@The_Cold_File",
        "check": None,  # status derived from latest YouTube upload instead
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
    if not svc.get("check"):
        return result
    t0 = time.perf_counter()
    try:
        async with http.get(svc["check"], headers={"User-Agent": "portfolio-status"}, timeout=timeout) as resp:
            result["latency_ms"] = int((time.perf_counter() - t0) * 1000)
            result["status"] = "up" if resp.status < 500 else "down"
    except Exception:
        result["latency_ms"] = None
        result["status"] = "down"
    return result


async def _check_services() -> dict:
    http = client.session()
    timeout = aiohttp.ClientTimeout(total=6.0)
    services = list(await asyncio.gather(
        *[_probe_service(http, svc, timeout) for svc in _STATUS_SERVICES]
    ))

    # The Cold File is a scheduled pipeline, not an HTTP service — it is "up"
    # if the channel got a new autonomous upload within the weekly cadence (+ slack).
    try:
        cold = await _get_coldfile_data()
        latest = (cold or {}).get("latest")
        for svc in services:
            if svc["id"] == "cold-file" and latest:
                published = datetime.fromisoformat(latest["published"])
                age_days = (datetime.now(timezone.utc) - published).days
                svc["status"] = "up" if age_days <= 9 else "idle"
                svc["detail"] = f"last episode {age_days}d ago"
    except Exception:
        current_app.logger.exception("status: cold-file check failed")

    return {
        "services": services,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@bp.get("/api/status")
async def production_status():
    """Live health of every production deployment, checked in parallel."""
    return jsonify(await _status_cache.get(_check_services))


# --- The Cold File — live channel data (YouTube RSS, no API key needed) -------
_coldfile_cache: TTLCache[dict] = TTLCache(1800)  # 30 min
_COLDFILE_CHANNEL_ID = os.getenv("COLDFILE_CHANNEL_ID", "UCN8k1J6MXu-ucl6anByx_oQ")
_COLDFILE_FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={_COLDFILE_CHANNEL_ID}"
_ATOM_NS = {
    "a": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


async def _fetch_coldfile() -> dict | None:
    try:
        async with client.session().get(_COLDFILE_FEED) as resp:
            if resp.status != 200:
                return None
            xml_body = await resp.text()
    except Exception:
        current_app.logger.exception("coldfile: RSS fetch failed")
        return None

    try:
        root = ET.fromstring(xml_body)
        episodes = []
        for entry in root.findall("a:entry", _ATOM_NS):
            vid = entry.find("yt:videoId", _ATOM_NS)
            title = entry.find("a:title", _ATOM_NS)
            published = entry.find("a:published", _ATOM_NS)
            if vid is None or title is None or published is None:
                continue
            episodes.append({
                "video_id": vid.text,
                "title": title.text,
                "published": published.text,
                "thumbnail": f"https://i.ytimg.com/vi/{vid.text}/hqdefault.jpg",
            })
        if not episodes:
            return None
        return {
            "channel_url": "https://www.youtube.com/@The_Cold_File",
            # RSS caps at 15 entries; the uploads playlist below supplies the real count.
            "episode_count": len(episodes),
            "latest": episodes[0],
            "episodes": episodes[:3],
        }
    except Exception:
        current_app.logger.exception("coldfile: RSS parse failed")
        return None


async def _get_coldfile_data() -> dict | None:
    """Fresh channel data, else the last good copy, else None."""
    return await _coldfile_cache.get(_fetch_coldfile) or _coldfile_cache.value


# The real episode count and runtimes come from the channel's long-form uploads
# playlist (UULF…, Shorts excluded), recounted every 6 hours. YouTube offers no
# key-free API for this, so the page's embedded ytInitialData is parsed; when
# that fails the section falls back to the RSS count ("15+").
_stats_cache: TTLCache[dict] = TTLCache(6 * 3600)
_UPLOADS_PAGE = f"https://www.youtube.com/playlist?list=UULF{_COLDFILE_CHANNEL_ID[2:]}"
_INITIAL_DATA = re.compile(r"var ytInitialData = (\{.*?\});</script>", re.S)
_VIDEO_COUNT = re.compile(r"^(\d[\d,]*) videos?$")
_DURATION = re.compile(r"^(?:(\d+):)?(\d{1,2}):(\d{2})$")


def _parse_uploads_page(html: str) -> dict | None:
    """{"episode_count", "runtime_minutes": [shortest, longest] | None} or None if the count is missing."""
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
    return {"episode_count": count, "runtime_minutes": runtime}


async def _fetch_channel_stats() -> dict | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": "SOCS=CAI",  # skips the EU consent interstitial
    }
    try:
        async with client.session().get(_UPLOADS_PAGE, headers=headers) as resp:
            if resp.status != 200:
                current_app.logger.warning("coldfile: uploads page returned %s", resp.status)
                return None
            html = await resp.text()
        stats = _parse_uploads_page(html)
    except Exception:
        current_app.logger.exception("coldfile: uploads page failed")
        return None
    if stats is None:
        current_app.logger.warning("coldfile: uploads page had no video count")
    return stats


@bp.get("/api/coldfile")
async def coldfile():
    """Live data for The Cold File section — latest autonomous episodes."""
    data = await _get_coldfile_data()
    if not data:
        return jsonify({"error": "channel data unavailable"}), 503
    stats = await _stats_cache.get(_fetch_channel_stats) or _stats_cache.value
    if stats:
        return jsonify({**data, **stats, "episode_count_exact": True})
    return jsonify({**data, "episode_count_exact": False, "runtime_minutes": None})


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
