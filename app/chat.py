"""CV chat: proxies the llm-assistant RAG backend, with saved CV facts as fallback."""
import asyncio
import json
import os
import re
import time
from functools import lru_cache

import aiohttp
from quart import Blueprint, Response, current_app, jsonify, request, stream_with_context

from app import client
from app.data import PROJECTS
from app.frontend import cv_content

bp = Blueprint("chat", __name__)

# URL of the llm-assistant RAG backend. Defaults to the Railway deployment which
# already has Gustav's CV indexed; override locally with LLM_ASSISTANT_URL=http://127.0.0.1:8002.
LLM_ASSISTANT_URL = os.getenv(
    "LLM_ASSISTANT_URL",
    "https://llm-assistant-production-aa36.up.railway.app",
)
# Bearer token sent to the llm-assistant. Once SEARCH_API_TOKEN is set on the
# llm-assistant side, this MUST match — otherwise the proxy uses the fallback.
LLM_ASSISTANT_API_KEY = os.getenv("LLM_ASSISTANT_API_KEY", "").strip()

# Every question is forwarded to a paid LLM backend, so length is enforced here,
# not only by the input's maxLength in frontend/components/Chat.tsx.
MAX_QUERY_CHARS = 2000

# --- Rate limiting (per-IP sliding window) ------------------------------------
# In-memory only; single-instance Railway is fine. For multi-instance, swap with
# Redis. Defaults: 20 requests per 60s per IP.
CV_CHAT_RATE_LIMIT = int(os.getenv("CV_CHAT_RATE_LIMIT", "20"))
CV_CHAT_RATE_WINDOW = int(os.getenv("CV_CHAT_RATE_WINDOW_SECONDS", "60"))
_rate_buckets: dict[str, list[float]] = {}


def _client_ip() -> str:
    """Client IP for rate limiting.

    Railway's edge overwrites X-Real-IP with the real visitor address, so it
    cannot be spoofed in production. X-Forwarded-For is deliberately ignored:
    its first entry is whatever the caller sent.
    """
    real = request.headers.get("X-Real-IP", "").strip()
    return real or request.remote_addr or "unknown"


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
    # Drop IPs whose newest hit is outside the window, so the table only holds
    # recently active clients instead of growing forever.
    if len(_rate_buckets) > 1000:
        for stale_ip in [k for k, v in _rate_buckets.items() if v[-1] <= cutoff]:
            del _rate_buckets[stale_ip]
    return False


# --- Fallback answers -----------------------------------------------------------
# Used when the RAG backend is unreachable or has no useful answer. Every fact is
# derived from content/cv.json and app/data.py, the same sources as the site and
# the PDF, so the chat cannot drift from the published CV.
_AI_TECH_MARKERS = ("RAG", "Claude", "Gemini", "MCP", "LLM")

# (word prefixes, topic): first topic with a word starting with a prefix wins.
_FALLBACK_KEYWORDS = [
    (("llm", "gpt", "gemini", "claude", "anthropic", "openai", "rag", "retriev", "vector",
      "qdrant", "embedding", "prompt"), "ai"),
    (("project", "projekt", "built", "build", "bygget", "lavet", "shipped", "portfolio"), "projects"),
    (("stack", "tech", "framework", "tool", "skill", "kompetence", "programming", "python",
      "sql", "azure"), "stack"),
    (("experience", "erfaring", "year", "år", "background", "career", "karriere", "job",
      "work", "arbejd", "role"), "experience"),
    (("contact", "kontakt", "email", "mail", "linkedin", "github", "reach", "hire", "phone",
      "telefon"), "contact"),
    (("cert", "qualific", "education", "uddannelse", "course", "kursus", "degree"),
     "certifications"),
    (("speak", "danish", "english", "dansk", "engelsk", "languages", "sprog", "taler"),
     "languages"),
    (("location", "where", "based", "remote", "denmark", "danmark", "hvor", "bor"), "location"),
]


@lru_cache
def _fallback_facts() -> dict[str, str]:
    cv = cv_content()
    contact = cv["contact"]
    ai_projects = [p.title for p in PROJECTS
                   if any(m in tech for tech in p.technologies for m in _AI_TECH_MARKERS)]
    technologies = list(dict.fromkeys(t for p in PROJECTS for t in p.technologies))
    return {
        "ai": f"{cv['headline']} AI systems in production: {'; '.join(ai_projects)}.",
        "projects": "Projects, strongest first: " + "; ".join(p.title for p in PROJECTS)
                    + ". Details and live links are on /projects.",
        "stack": "Core skills: " + "; ".join(cv["skills"])
                 + ". Technologies used across the projects: " + ", ".join(technologies[:15]) + ".",
        "experience": cv["summary"] + " Roles: "
                      + "; ".join(f"{r['role']}, {r['company']} ({r['date']})" for r in cv["roles"]) + ".",
        "contact": f"Email: {contact['email']} · LinkedIn: linkedin.com/in/{contact['linkedin']}"
                   f" · GitHub: github.com/{contact['github']} · {contact['portfolio']}",
        "certifications": "Certifications: "
                          + "; ".join(f"{c['name']} ({c['issuer']})" for c in cv["certifications"])
                          + ". Education: " + "; ".join(cv["education"]) + ".",
        "languages": "Languages: " + ", ".join(cv["languages"]) + ".",
        "location": f"Based in {contact['location']}.",
        "default": "I can answer from saved CV facts about AI work, projects, skills, experience, "
                   "certifications, languages, contact and location.",
    }


def _fallback_answer(query: str) -> tuple[str, str]:
    """Answer from saved CV facts. Returns (answer, matched_topic)."""
    words = re.findall(r"\w+", query.lower())
    matched = next((topic for prefixes, topic in _FALLBACK_KEYWORDS
                    if any(w.startswith(prefixes) for w in words)), "default")
    return _fallback_facts()[matched], matched


# --- RAG backend ------------------------------------------------------------------
def _is_useful_rag_answer(payload: dict) -> bool:
    """Decide whether the llm-assistant returned something worth showing.

    Demo-mode responses with no matched documents are worse than the saved
    facts, so those use the fallback.
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


async def _query_rag_backend(query: str) -> dict | None:
    """Call the llm-assistant /search endpoint. Returns the payload or None."""
    log = current_app.logger
    try:
        headers = {"Content-Type": "application/json"}
        if LLM_ASSISTANT_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_ASSISTANT_API_KEY}"
        rag_url = f"{LLM_ASSISTANT_URL.rstrip('/')}/search"
        payload = {"query": query, "top_k": 10}
        async with client.session().post(
            rag_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=45.0)
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            log.info("cv-chat: llm-assistant returned HTTP %s; using fallback", resp.status)
    except (aiohttp.ClientError, OSError) as e:
        log.info("cv-chat: llm-assistant unreachable (%s); using fallback", e)
    except Exception as e:
        log.warning("cv-chat: RAG call failed (%s); using fallback", e)
    return None


def _public_sources(rag_data: dict) -> list[dict]:
    """Trim retrieval hits to what the RAG-trace panel needs (no full chunks)."""
    return [
        {
            "filename": r.get("filename", "unknown"),
            "score": round(float(r.get("score") or 0.0), 3),
            "excerpt": (r.get("chunk_text") or "")[:180],
        }
        for r in (rag_data.get("results") or [])[:6]
    ]


async def _answer(query: str) -> tuple[str, dict]:
    """(answer, meta) from the RAG backend, or from saved CV facts when it has nothing useful."""
    if query:
        rag = await _query_rag_backend(query)
        if rag and _is_useful_rag_answer(rag):
            return rag["answer"], {
                "source": "rag",
                "model": rag.get("model") or "gemini",
                "embedding_provider": rag.get("embedding_provider"),
                "embed_ms": rag.get("embed_ms"),
                "ai_ms": rag.get("ai_ms"),
                "total_ms": rag.get("total_ms"),
                "sources": _public_sources(rag),
            }
    answer, matched = _fallback_answer(query)
    return answer, {"source": "mock", "matched": matched}


async def _visitor_query() -> tuple[str, None] | tuple[None, tuple[Response, int]]:
    """The visitor's question, or an error response when rate-limited or too long."""
    if _is_rate_limited(_client_ip()):
        return None, (jsonify({
            "answer": "Rate limit reached — slow down a bit and try again in a moment.",
            "source": "rate_limited",
        }), 429)
    body = await request.get_json(silent=True)
    query = str(body.get("query", "")).strip() if isinstance(body, dict) else ""
    if len(query) > MAX_QUERY_CHARS:
        return None, (jsonify({"error": f"Questions are limited to {MAX_QUERY_CHARS} characters."}), 413)
    return query, None


@bp.post("/api/cv-chat")
async def cv_chat():
    """Non-streaming variant; the frontend uses it when the stream fails before any text."""
    query, error = await _visitor_query()
    if error:
        return error
    try:
        answer, meta = await _answer(query)
    except Exception:
        current_app.logger.exception("cv-chat endpoint failure")
        return jsonify({"error": "The assistant is temporarily unavailable"}), 500
    return jsonify({"answer": answer, **meta})


@bp.post("/api/cv-chat-stream")
async def cv_chat_stream():
    """Streaming variant of /api/cv-chat (Server-Sent Events).

    Event protocol (each event is `data: <json>\\n\\n`):
      {"type": "stage", "stage": "retrieve"}   — pipeline progress, sent immediately
      {"type": "meta", ...}                    — source, retrieval hits, timings
      {"type": "token", "t": "..."}            — answer text, word by word
      {"type": "done"}

    The llm-assistant backend returns the answer in one piece, so the token
    events re-chunk it; the meta event carries the real pipeline numbers
    (embed_ms / ai_ms / scores) from the RAG backend.
    """
    query, error = await _visitor_query()
    if error:
        return error

    def sse(obj: dict) -> str:
        return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

    # The stream outlives the view; keep the request (and app) context for logging.
    @stream_with_context
    async def event_stream():
        yield sse({"type": "stage", "stage": "retrieve"})
        answer, meta = await _answer(query)
        yield sse({"type": "meta", **meta})
        # Word-level chunks; pace so long answers don't take forever.
        words = re.findall(r"\S+\s*", answer) or [answer]
        delay = min(0.028, max(0.006, 2.5 / len(words)))
        for w in words:
            yield sse({"type": "token", "t": w})
            await asyncio.sleep(delay)
        yield sse({"type": "done"})

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # disable proxy buffering so events flush
    }
    return Response(event_stream(), mimetype="text/event-stream", headers=headers)
