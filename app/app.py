from typing import List
from datetime import datetime, timezone
import asyncio
import json
import os
import sys
import re
import xml.etree.ElementTree as ET

# Ensure project root in path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from quart import Quart, render_template, jsonify, Response, request
from app.config import get_settings
from app.models import Project
from app.data import PROJECTS
from app.pdf_cv import extract_cv_data, generate_cv_pdf
import time
import ssl
import random
import aiohttp
import certifi

# Shared SSL context backed by certifi so aiohttp can verify TLS certs on
# Homebrew/portable Python builds that lack a system CA bundle.
_SSL_CTX = ssl.create_default_context(cafile=certifi.where())

settings = get_settings()

app = Quart(
    __name__,
    template_folder=os.path.join(PROJECT_ROOT, "templates"),
    static_folder=os.path.join(PROJECT_ROOT, "static"),
)

# Serve static files via Quart's builtin static folder (static/ already exists)
app.static_folder = os.path.join(PROJECT_ROOT, "static")




@app.route("/api/get-apology")
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

        timeout = aiohttp.ClientTimeout(total=10.0)
        async with aiohttp.ClientSession(timeout=timeout) as http_session:
            demo_url = "https://apology-as-a-service-production.up.railway.app/demo"
            params = {"severity": severity, "style": style, "context": context}
            async with http_session.get(demo_url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    apology_text = data.get("text")
                else:
                    app.logger.warning(f"Demo endpoint returned {resp.status}")
                    apology_text = None

        # Use fallback if live generation failed
        if not apology_text:
            app.logger.info("apology: using canned fallback")
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
            # Pick a random template based on severity or default
            templates = canned.get(severity, canned["TRIVIAL"])
            apology_text = random.choice(templates)

            # Add a little note that this is a fallback
            meta_suffix = " (Live connection failed - using cached response)"
        else:
            meta_suffix = ""

        return jsonify(
            {
                "apology": apology_text,
                "meta": f"Generated via MCP (Severity: {severity}, Style: {style}){meta_suffix}",
            }
        )

    except Exception as e:
        app.logger.exception("apology endpoint critical failure")
        return jsonify({"error": str(e)}), 500


# --- CV chat (mock RAG over Gustav's CV) ---
# Lightweight keyword-matched responses grounded in the live about.html content.
# Swap with a real RAG call (e.g. llm-assistant on Railway) when ready.
_CV_FACTS = {
    "llm": (
        "Gustav has hands-on production experience with LLMs — building RAG pipelines, "
        "prompt engineering, and integrating providers like Gemini, Anthropic, and OpenAI. "
        "His stack: Qdrant for vector search, FastEmbed for embeddings, and Quart/FastAPI "
        "for async serving. Currently running multiple live LLM demos on Railway."
    ),
    "rag": (
        "Multiple production RAG systems shipped. Architecture: document ingestion → "
        "chunking → FastEmbed/ONNX embeddings → Qdrant vector store → semantic retrieval → "
        "Gemini/Anthropic generation with grounded citations. See the LLM Assistant project."
    ),
    "projects": (
        "Featured projects on Railway: (1) LLM Assistant — RAG chat over uploaded docs, "
        "(2) Document Intelligence Pipeline — OCR + structured extraction, (3) Apology-as-a-Service — "
        "MCP server with style/severity dimensions, (4) Interdimensional Tales — automated horror "
        "YouTube channel powered by Claude. All Python, all async, all in production."
    ),
    "stack": (
        "Python everywhere. Web: Quart, FastAPI, Flask. Data: SQLAlchemy, MS SQL, Postgres, "
        "Pandas, NumPy. AI: Anthropic SDK, OpenAI SDK, Qdrant, FastEmbed, ONNX. Cloud: Azure, "
        "Railway, Docker. Editor: VS Code with Claude Code."
    ),
    "experience": (
        "15+ years in IT spanning support, operations, and software development. "
        "Specialized in Python automation, data engineering, and AI/LLM integration. "
        "Strong on cross-functional delivery — from planning to production."
    ),
    "contact": (
        "Email: guch79@gmail.com · Phone: +45 60 25 34 18 · "
        "LinkedIn: gustav-wind-christensen · GitHub: @Ajollyworld79"
    ),
    "certifications": (
        "PCEP™ Certified Entry-Level Python Programmer · Complete Python Developer "
        "(Zero to Mastery 2023) · Python Special Methods (Advanced Classes) · "
        "Microsoft Certified Professional (MCPS) · Windows 7 Desktop Support Technician."
    ),
    "languages": (
        "Danish — native. English — professional working proficiency. "
        "(Code: fluent in Python, conversational in TypeScript/SQL/Bash.)"
    ),
    "location": (
        "Based in Denmark. Comfortable with remote, hybrid, and on-site collaboration "
        "across European timezones."
    ),
    "default": (
        "I'm a mock CV bot for the demo — keyword-matched responses for now. "
        "Ask about LLMs, RAG, projects, stack, experience, certifications, contact, or location. "
        "(Real RAG over the full CV is one wire-up away.)"
    ),
}

_CV_KEYWORDS = [
    (("llm", "language model", "gpt", "gemini", "claude", "anthropic"), "llm"),
    (("rag", "retrieval", "vector", "qdrant", "embedding"), "rag"),
    (("project", "projekt", "build", "bygget", "lavet", "shipped", "ship"),
     "projects"),
    (("stack", "tech", "framework", "tool", "language", "sprog"), "stack"),
    (("experience", "erfaring", "years", "år", "background", "history"), "experience"),
    (("contact", "kontakt", "email", "phone", "linkedin", "reach"), "contact"),
    (("cert", "qualific", "license", "credentials"), "certifications"),
    (("language", "speak", "danish", "english", "dansk", "engelsk", "tale"), "languages"),
    (("location", "where", "based", "remote", "denmark", "danmark", "hvor"),
     "location"),
]


# URL of the llm-assistant RAG backend. Defaults to the Railway deployment which
# already has Gustav's CV indexed; override locally with LLM_ASSISTANT_URL=http://127.0.0.1:8002.
LLM_ASSISTANT_URL = os.getenv(
    "LLM_ASSISTANT_URL",
    "https://llm-assistant-production-aa36.up.railway.app",
)
# Bearer token sent to the llm-assistant. Once SEARCH_API_TOKEN is set on the
# llm-assistant side, this MUST match — otherwise the proxy falls back to mock.
LLM_ASSISTANT_API_KEY = os.getenv("LLM_ASSISTANT_API_KEY", "").strip()

# --- Rate limiting for /api/cv-chat (per-IP sliding window) ---------------------
# In-memory only; single-instance Railway is fine. For multi-instance, swap with
# Redis. Defaults: 20 requests per 60s per IP.
CV_CHAT_RATE_LIMIT = int(os.getenv("CV_CHAT_RATE_LIMIT", "20"))
CV_CHAT_RATE_WINDOW = int(os.getenv("CV_CHAT_RATE_WINDOW_SECONDS", "60"))
_rate_buckets: dict[str, list[float]] = {}


def _client_ip() -> str:
    """Pick a stable client IP — honour Railway/Cloudflare proxy headers."""
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    real = request.headers.get("X-Real-IP", "")
    if real:
        return real.strip()
    return request.remote_addr or "unknown"


def _is_rate_limited(ip: str) -> bool:
    """True if `ip` has exceeded CV_CHAT_RATE_LIMIT within the sliding window."""
    now = time.time()
    cutoff = now - CV_CHAT_RATE_WINDOW
    bucket = [t for t in _rate_buckets.get(ip, []) if t > cutoff]
    if len(bucket) >= CV_CHAT_RATE_LIMIT:
        _rate_buckets[ip] = bucket
        return True
    bucket.append(now)
    _rate_buckets[ip] = bucket
    # Opportunistic cleanup: every ~100 unique IPs, prune empties.
    if len(_rate_buckets) > 100:
        for stale_ip in [k for k, v in _rate_buckets.items() if not v]:
            del _rate_buckets[stale_ip]
    return False


def _is_useful_rag_answer(payload: dict) -> bool:
    """Decide whether the llm-assistant returned something worth showing.

    Demo-mode responses with no matched documents are worse than our mock,
    so we fall back to keyword facts in that case.
    """
    if not payload:
        return False
    answer = (payload.get("answer") or "").strip()
    if not answer:
        return False
    # Demo-mode marker: no docs matched, generic apology.
    if payload.get("demo") and not payload.get("results"):
        return False
    if "no documents matched" in answer.lower():
        return False
    if "no confident matches" in answer.lower():
        return False
    return True


async def _query_rag_backend(raw_query: str) -> dict | None:
    """Call the llm-assistant /search endpoint. Returns the payload or None."""
    try:
        timeout = aiohttp.ClientTimeout(total=45.0)
        headers = {"Content-Type": "application/json"}
        if LLM_ASSISTANT_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_ASSISTANT_API_KEY}"
        connector = aiohttp.TCPConnector(ssl=_SSL_CTX)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as http_session:
            rag_url = f"{LLM_ASSISTANT_URL.rstrip('/')}/search"
            payload = {"query": raw_query, "top_k": 10}
            async with http_session.post(rag_url, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                app.logger.info(f"cv-chat: llm-assistant returned HTTP {resp.status}; using mock")
    except (aiohttp.ClientError, OSError) as e:
        app.logger.info(f"cv-chat: llm-assistant unreachable ({e}); using mock")
    except Exception as e:
        app.logger.warning(f"cv-chat: RAG call failed ({e}); using mock")
    return None


def _mock_answer(query_lower: str) -> tuple[str, str]:
    """Keyword-matched canned fallback. Returns (answer, matched_topic)."""
    matched = "default"
    for keywords, topic in _CV_KEYWORDS:
        if any(k in query_lower for k in keywords):
            matched = topic
            break
    return _CV_FACTS.get(matched, _CV_FACTS["default"]), matched


def _public_sources(rag_data: dict) -> list[dict]:
    """Trim retrieval hits to what the RAG-trace panel needs (no full chunks)."""
    out = []
    for r in (rag_data.get("results") or [])[:6]:
        out.append({
            "filename": r.get("filename", "unknown"),
            "score": round(float(r.get("score") or 0.0), 3),
            "excerpt": (r.get("chunk_text") or "")[:180],
        })
    return out


@app.route("/api/cv-chat", methods=["POST"])
async def cv_chat():
    """Answer a question about Gustav's CV (non-streaming fallback).

    Strategy:
      1. Rate-limit per-IP to prevent abuse of the proxy itself.
      2. Forward the query to the llm-assistant RAG backend (real grounded RAG)
         with a Bearer token so /search on the backend can require auth.
      3. If the backend is unreachable, in demo mode, or returns no useful
         answer, fall back to keyword-matched canned facts.
    """
    try:
        ip = _client_ip()
        if _is_rate_limited(ip):
            return jsonify({
                "answer": "Rate limit reached — slow down a bit and try again in a moment.",
                "source": "rate_limited",
            }), 429

        body = await request.get_json(silent=True) or {}
        raw_query = str(body.get("query", "")).strip()
        query_lower = raw_query.lower()

        if not raw_query:
            return jsonify({
                "answer": _CV_FACTS["default"],
                "matched": "default",
                "source": "mock",
            })

        rag_data = await _query_rag_backend(raw_query)
        if rag_data and _is_useful_rag_answer(rag_data):
            return jsonify({
                "answer": rag_data.get("answer", ""),
                "sources": rag_data.get("results") or rag_data.get("sources") or [],
                "source": "rag",
            })

        answer, matched = _mock_answer(query_lower)
        return jsonify({"answer": answer, "matched": matched, "source": "mock"})
    except Exception as e:
        app.logger.exception("cv-chat endpoint failure")
        return jsonify({"error": str(e)}), 500


@app.route("/api/cv-chat-stream", methods=["POST"])
async def cv_chat_stream():
    """Streaming variant of /api/cv-chat (Server-Sent Events).

    Event protocol (each event is `data: <json>\\n\\n`):
      {"type": "stage", "stage": "retrieve"}   — pipeline progress, sent immediately
      {"type": "meta", ...}                    — source, retrieval hits, timings
      {"type": "token", "t": "..."}            — answer text, word by word
      {"type": "done"}

    The llm-assistant backend returns the answer in one piece, so the token
    events re-chunk it client-side-style; the meta event carries the real
    pipeline numbers (embed_ms / ai_ms / scores) from the RAG backend.
    """
    ip = _client_ip()
    if _is_rate_limited(ip):
        return jsonify({
            "answer": "Rate limit reached — slow down a bit and try again in a moment.",
            "source": "rate_limited",
        }), 429

    body = await request.get_json(silent=True) or {}
    raw_query = str(body.get("query", "")).strip()
    query_lower = raw_query.lower()

    def sse(obj: dict) -> str:
        return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

    async def event_stream():
        yield sse({"type": "stage", "stage": "retrieve"})

        meta: dict = {"type": "meta", "source": "mock"}
        answer = ""
        if raw_query:
            rag_data = await _query_rag_backend(raw_query)
            if rag_data and _is_useful_rag_answer(rag_data):
                answer = rag_data.get("answer", "")
                meta.update({
                    "source": "rag",
                    "model": "gemini-2.5-flash",
                    "embedding_provider": rag_data.get("embedding_provider"),
                    "embed_ms": rag_data.get("embed_ms"),
                    "ai_ms": rag_data.get("ai_ms"),
                    "total_ms": rag_data.get("total_ms"),
                    "sources": _public_sources(rag_data),
                })
        if not answer:
            answer, matched = _mock_answer(query_lower)
            meta["matched"] = matched
        yield sse(meta)

        # Word-level chunks; pace so long answers don't take forever.
        words = re.findall(r"\S+\s*", answer) or [answer]
        delay = min(0.028, max(0.006, 2.5 / max(len(words), 1)))
        for w in words:
            yield sse({"type": "token", "t": w})
            await asyncio.sleep(delay)
        yield sse({"type": "done"})

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # disable proxy buffering so events flush
    }
    return Response(event_stream(), mimetype="text/event-stream", headers=headers)


# --- Production status board -------------------------------------------------
# Pings the live Railway deployments in parallel and caches for 60s so a page
# load never fans out more than once a minute.
_STATUS_CACHE: dict = {"ts": 0.0, "data": None}
_STATUS_TTL = 60

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


async def _probe_service(http: "aiohttp.ClientSession", svc: dict) -> dict:
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
        async with http.get(svc["check"], headers={"User-Agent": "portfolio-status"}) as resp:
            result["latency_ms"] = int((time.perf_counter() - t0) * 1000)
            result["status"] = "up" if resp.status < 500 else "down"
    except Exception:
        result["latency_ms"] = None
        result["status"] = "down"
    return result


@app.route("/api/status")
async def production_status():
    """Live health of every production deployment, checked in parallel."""
    now = time.time()
    cached = _STATUS_CACHE.get("data")
    if cached and now - _STATUS_CACHE["ts"] < _STATUS_TTL:
        return jsonify(cached)

    timeout = aiohttp.ClientTimeout(total=6.0)
    connector = aiohttp.TCPConnector(ssl=_SSL_CTX)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as http:
        results = await asyncio.gather(
            *[_probe_service(http, svc) for svc in _STATUS_SERVICES]
        )
    services = list(results)

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
        app.logger.exception("status: cold-file check failed")

    payload = {
        "services": services,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    _STATUS_CACHE["data"] = payload
    _STATUS_CACHE["ts"] = now
    return jsonify(payload)


# --- The Cold File — live channel data (YouTube RSS, no API key needed) -------
_COLDFILE_CACHE: dict = {"ts": 0.0, "data": None}
_COLDFILE_TTL = 1800  # 30 min
_COLDFILE_CHANNEL_ID = os.getenv("COLDFILE_CHANNEL_ID", "UCN8k1J6MXu-ucl6anByx_oQ")
_COLDFILE_FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={_COLDFILE_CHANNEL_ID}"
_ATOM_NS = {
    "a": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


async def _get_coldfile_data() -> dict | None:
    now = time.time()
    cached = _COLDFILE_CACHE.get("data")
    if cached and now - _COLDFILE_CACHE["ts"] < _COLDFILE_TTL:
        return cached

    try:
        timeout = aiohttp.ClientTimeout(total=10.0)
        connector = aiohttp.TCPConnector(ssl=_SSL_CTX)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as http:
            async with http.get(_COLDFILE_FEED) as resp:
                if resp.status != 200:
                    return cached
                xml_body = await resp.text()
    except Exception:
        app.logger.exception("coldfile: RSS fetch failed")
        return cached

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
            return cached
        data = {
            "channel_url": "https://www.youtube.com/@The_Cold_File",
            # RSS caps at 15 entries; the frontend renders 15 as "15+".
            "episode_count": len(episodes),
            "latest": episodes[0],
            "episodes": episodes[:3],
        }
        _COLDFILE_CACHE["data"] = data
        _COLDFILE_CACHE["ts"] = now
        return data
    except Exception:
        app.logger.exception("coldfile: RSS parse failed")
        return cached


@app.route("/api/coldfile")
async def coldfile():
    """Live data for The Cold File section — latest autonomous episodes."""
    data = await _get_coldfile_data()
    if not data:
        return jsonify({"error": "channel data unavailable"}), 503
    return jsonify(data)


# --- GitHub activity (contribution heatmap) ---
# Cache structure: {"ts": epoch_seconds, "data": payload | None}
_GITHUB_CACHE: dict = {"ts": 0.0, "data": None}
_GITHUB_CACHE_TTL = 3600  # 1 hour
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


@app.route("/api/github-activity")
async def github_activity():
    """Return GitHub contribution-calendar data for the configured user.

    Cached in-memory for 1 hour to stay well under GitHub's 5000 req/hr quota
    and avoid hammering the API on every page load.
    """
    now = time.time()
    cached = _GITHUB_CACHE.get("data")
    if cached and now - _GITHUB_CACHE["ts"] < _GITHUB_CACHE_TTL:
        return jsonify(cached)

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        # Serve stale cache if available; otherwise tell the frontend to hide
        if cached:
            return jsonify({**cached, "_stale": True})
        return jsonify({"error": "GITHUB_TOKEN not configured"}), 503

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "gustavchristensen.dev-portfolio",
        "Accept": "application/json",
    }
    payload = {"query": _GITHUB_QUERY, "variables": {"username": _GITHUB_USERNAME}}

    try:
        timeout = aiohttp.ClientTimeout(total=10.0)
        async with aiohttp.ClientSession(timeout=timeout) as http:
            async with http.post(
                "https://api.github.com/graphql", headers=headers, json=payload
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    app.logger.warning("github graphql %s: %s", resp.status, body[:200])
                    if cached:
                        return jsonify({**cached, "_stale": True})
                    return jsonify({"error": f"GitHub API {resp.status}"}), 502
                body = await resp.json()

        user = (body.get("data") or {}).get("user")
        if not user:
            errors = body.get("errors") or []
            app.logger.warning("github graphql empty user: %s", errors[:2])
            if cached:
                return jsonify({**cached, "_stale": True})
            return jsonify({"error": "GitHub returned no user data"}), 502

        cal = user["contributionsCollection"]["contributionCalendar"]
        result = {
            "username": _GITHUB_USERNAME,
            "total": cal["totalContributions"],
            "weeks": cal["weeks"],
        }
        _GITHUB_CACHE["data"] = result
        _GITHUB_CACHE["ts"] = now
        return jsonify(result)

    except Exception as e:
        app.logger.exception("github-activity endpoint failed")
        if cached:
            return jsonify({**cached, "_stale": True})
        return jsonify({"error": str(e)}), 500


@app.route("/")
async def index():
    return await render_template(
        "index.html",
        projects=PROJECTS,
        author=settings.author_name,
        current_year=datetime.now(timezone.utc).year,
    )


@app.route("/about")
async def about():
    return await render_template(
        "about.html",
        author=settings.author_name,
        current_year=datetime.now(timezone.utc).year,
    )


@app.route("/projects")
async def projects():
    return await render_template(
        "projects.html",
        projects=PROJECTS,
        author=settings.author_name,
        current_year=datetime.now(timezone.utc).year,
    )


@app.route("/download_cv")
async def download_cv():
    """Generate the CV PDF — about.html stays the single source of truth."""
    tpl_path = os.path.join(PROJECT_ROOT, "templates", "about.html")
    try:
        with open(tpl_path, "r", encoding="utf-8") as fh:
            raw_tpl = fh.read()
    except Exception:
        raw_tpl = ""

    cv_data = extract_cv_data(raw_tpl)
    packet = generate_cv_pdf(author=settings.author_name, projects=PROJECTS, data=cv_data)

    data = packet.getvalue()
    filename = f"CV_{settings.author_name.replace(' ', '_')}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(data, mimetype="application/pdf", headers=headers)


@app.route("/favicon.ico")
async def favicon():
    return Response(b"", mimetype="image/x-icon", status=204)


@app.route("/apple-touch-icon.png")
async def apple_touch_icon():
    return Response(b"", mimetype="image/png", status=204)


@app.route("/apple-touch-icon-precomposed.png")
async def apple_touch_icon_precomposed():
    return Response(b"", mimetype="image/png", status=204)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.app:app", host="127.0.0.1", port=8000, reload=True)
