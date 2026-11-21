import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest

from app import chat, live
from app.app import app
from app.cache import TTLCache
from app.data import PROJECTS
from app.frontend import cv_content

pytestmark = pytest.mark.asyncio

RAG_URL = chat.LLM_ASSISTANT_URL.rstrip("/") + "/search"


def ask(path="/api/cv-chat", query="What projects has Gustav built?", ip="203.0.113.1"):
    return app.test_client().post(path, json={"query": query}, headers={"X-Real-IP": ip})


def sse_events(body: str) -> list[dict]:
    return [json.loads(frame.removeprefix("data: ")) for frame in body.split("\n\n") if frame]


def rss(*published: datetime) -> str:
    entries = "".join(
        f"<entry><yt:videoId>vid{i:08d}</yt:videoId><title>Episode {i}</title>"
        f"<published>{p.isoformat()}</published></entry>"
        for i, p in enumerate(published)
    )
    return ('<feed xmlns="http://www.w3.org/2005/Atom" '
            f'xmlns:yt="http://www.youtube.com/xml/schemas/2015">{entries}</feed>')


# --- CV chat ----------------------------------------------------------------------

async def test_rate_limit_is_per_ip_and_shared_by_both_chat_endpoints(monkeypatch, http):
    monkeypatch.setattr(chat, "CV_CHAT_RATE_LIMIT", 2)
    assert (await ask()).status_code == 200
    assert (await ask(path="/api/cv-chat-stream")).status_code == 200
    limited = await ask()
    assert limited.status_code == 429
    assert (await limited.get_json())["source"] == "rate_limited"
    assert (await ask(path="/api/cv-chat-stream")).status_code == 429
    assert (await ask(ip="203.0.113.2")).status_code == 200


@pytest.mark.parametrize("path", ["/api/cv-chat", "/api/cv-chat-stream"])
async def test_overlong_question_never_reaches_the_paid_backend(http, path):
    response = await ask(path=path, query="x" * (chat.MAX_QUERY_CHARS + 1))
    assert response.status_code == 413
    assert http.calls == []
    assert (await ask(path=path, query="x" * chat.MAX_QUERY_CHARS)).status_code == 200
    assert [url for _, url, _ in http.calls] == [RAG_URL]


async def test_rag_answer_exposes_only_trimmed_sources(http):
    http.respond(RAG_URL, json={
        "answer": "Gustav runs RAG in production.",
        "model": "gemini-3.6-flash",
        "results": [{"filename": "cv.pdf", "score": 0.91234, "chunk_text": "c" * 500}] * 8,
    })
    data = await (await ask()).get_json()
    assert data["source"] == "rag"
    assert data["answer"] == "Gustav runs RAG in production."
    assert len(data["sources"]) == 6
    assert data["sources"][0] == {"filename": "cv.pdf", "score": 0.912, "excerpt": "c" * 180}


@pytest.mark.parametrize("rag_reply", [
    None,  # backend unreachable
    {"answer": "No documents matched your question."},
    {"answer": "Here is a generic reply.", "demo": True, "results": []},
    {"answer": "   "},
])
async def test_unhelpful_rag_reply_falls_back_to_published_projects(http, rag_reply):
    if rag_reply is not None:
        http.respond(RAG_URL, json=rag_reply)
    data = await (await ask(query="Hvilke projekter har Gustav bygget?")).get_json()
    assert data["source"] == "mock"
    assert data["matched"] == "projects"
    assert all(p.title in data["answer"] for p in PROJECTS)


@pytest.mark.parametrize("question,topic", [
    ("What languages does Gustav speak?", "languages"),
    ("Which programming languages and tools does he use?", "stack"),
    ("Where is he based?", "location"),
    ("Does he have any certifications?", "certifications"),
    ("How many years of experience?", "experience"),
    ("Tell me about his RAG work", "ai"),
    ("hello", "default"),
])
async def test_fallback_routes_questions_to_the_right_topic(http, question, topic):
    data = await (await ask(query=question)).get_json()
    assert data["matched"] == topic


async def test_fallback_contact_uses_published_contact_details_only(http):
    answer = (await (await ask(query="What is his phone number?")).get_json())["answer"]
    contact = cv_content()["contact"]
    assert contact["email"] in answer
    assert contact["linkedin"] in answer
    assert "+45" not in answer


async def test_stream_emits_stage_meta_tokens_done_in_order(http):
    http.respond(RAG_URL, json={"answer": "Gustav ships **production** systems.", "ai_ms": 812,
                                "results": [{"filename": "cv.pdf", "score": 0.8, "chunk_text": "x"}]})
    response = await ask(path="/api/cv-chat-stream")
    assert response.mimetype == "text/event-stream"
    events = sse_events(await response.get_data(as_text=True))
    types = [e["type"] for e in events]
    assert types[:2] == ["stage", "meta"] and types[-1] == "done"
    assert set(types[2:-1]) == {"token"}
    assert "".join(e["t"] for e in events[2:-1]) == "Gustav ships **production** systems."
    assert events[1]["source"] == "rag" and events[1]["ai_ms"] == 812


async def test_stream_falls_back_when_backend_is_down(http):
    events = sse_events(await (await ask(path="/api/cv-chat-stream")).get_data(as_text=True))
    assert events[1] == {"type": "meta", "source": "mock", "matched": "projects"}
    assert events[-1] == {"type": "done"}


# --- Status board -------------------------------------------------------------------

def route_health(http, status=200):
    for svc in live._STATUS_SERVICES:
        if svc["check"]:
            http.respond(svc["check"], status=status)


@pytest.mark.parametrize("days_ago,status", [(3, "up"), (20, "idle")])
async def test_status_derives_cold_file_health_from_last_upload(http, days_ago, status):
    route_health(http)
    http.respond(live._COLDFILE_FEED, text=rss(datetime.now(timezone.utc) - timedelta(days=days_ago, hours=1)))
    data = await (await app.test_client().get("/api/status")).get_json()
    services = {s["id"]: s for s in data["services"]}
    assert services["cold-file"]["status"] == status
    assert services["cold-file"]["detail"] == f"last episode {days_ago}d ago"
    assert services["portfolio"]["status"] == "up"


async def test_status_reports_failing_services_as_down(http):
    route_health(http, status=503)
    http.routes[live._STATUS_SERVICES[1]["check"]] = asyncio.TimeoutError()
    data = await (await app.test_client().get("/api/status")).get_json()
    checked = [s for s in data["services"] if s["id"] != "cold-file"]
    assert {s["status"] for s in checked} == {"down"}


async def test_concurrent_status_requests_probe_each_service_once(http):
    route_health(http)
    test_client = app.test_client()
    await asyncio.gather(*[test_client.get("/api/status") for _ in range(5)])
    probes = [url for _, url, _ in http.calls if url != live._COLDFILE_FEED]
    assert sorted(probes) == sorted(s["check"] for s in live._STATUS_SERVICES if s["check"])


# --- The Cold File feed ---------------------------------------------------------------

async def test_coldfile_serves_last_good_copy_when_feed_breaks(monkeypatch, http):
    monkeypatch.setattr(live, "_coldfile_cache", TTLCache(0))  # every request refetches
    now = datetime.now(timezone.utc)
    http.respond(live._COLDFILE_FEED, text=rss(now, now - timedelta(days=7)))
    first = await (await app.test_client().get("/api/coldfile")).get_json()
    assert first["episode_count"] == 2 and first["latest"]["video_id"] == "vid00000000"

    http.respond(live._COLDFILE_FEED, text="<feed>not closed")
    stale = await app.test_client().get("/api/coldfile")
    assert stale.status_code == 200
    assert await stale.get_json() == first


async def test_coldfile_without_any_data_is_503(http):
    http.respond(live._COLDFILE_FEED, text=rss())
    assert (await app.test_client().get("/api/coldfile")).status_code == 503


def uploads_page(count_label: str, *durations: str) -> str:
    """Minimal playlist page in YouTube's current shape: header stats plus one lockup per video."""
    tiles = [{"lockupViewModel": {"contentImage": {"thumbnailViewModel": {"overlays": [
        {"thumbnailBottomOverlayViewModel": {"badges": [{"thumbnailBadgeViewModel": {"text": d}}]}}]}}}}
        for d in durations]
    data = {"header": {"stats": [{"runs": [{"text": count_label.split()[0]}, {"text": " videos"}]},
                                 {"simpleText": "No views"}]},
            "contents": tiles}
    return f"<script>var ytInitialData = {json.dumps(data)};</script>"


async def test_coldfile_reports_the_real_episode_count_and_runtime(http):
    now = datetime.now(timezone.utc)
    http.respond(live._COLDFILE_FEED, text=rss(*[now - timedelta(days=i) for i in range(15)]))
    http.respond(live._UPLOADS_PAGE, text=uploads_page("1,029 videos", "38:17", "1:14:37", "45:29"))
    data = await (await app.test_client().get("/api/coldfile")).get_json()
    assert data["episode_count"] == 1029 and data["episode_count_exact"] is True
    assert data["runtime_minutes"] == [38, 75]


@pytest.mark.parametrize("page", [None, "<html>consent wall</html>", uploads_page("no videos")])
async def test_coldfile_falls_back_to_rss_count_when_uploads_page_fails(http, page):
    now = datetime.now(timezone.utc)
    http.respond(live._COLDFILE_FEED, text=rss(*[now - timedelta(days=i) for i in range(15)]))
    if page is not None:
        http.respond(live._UPLOADS_PAGE, text=page)
    data = await (await app.test_client().get("/api/coldfile")).get_json()
    assert data["episode_count"] == 15 and data["episode_count_exact"] is False
    assert data["runtime_minutes"] is None


# --- GitHub activity ------------------------------------------------------------------

GRAPHQL_URL = "https://api.github.com/graphql"


def calendar(total):
    return {"data": {"user": {"contributionsCollection": {"contributionCalendar": {
        "totalContributions": total,
        "weeks": [{"contributionDays": [{"date": "2026-11-20", "contributionCount": 2, "weekday": 5}]}],
    }}}}}


async def test_github_failure_serves_stale_calendar_then_errors_without_one(monkeypatch, http):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr(live, "_github_cache", TTLCache(0))
    http.respond(GRAPHQL_URL, json=calendar(42))
    fresh = await (await app.test_client().get("/api/github-activity")).get_json()
    assert fresh["total"] == 42 and "_stale" not in fresh
    assert http.calls[0][2]["headers"]["Authorization"] == "Bearer test-token"

    http.respond(GRAPHQL_URL, status=502, text="bad gateway")
    stale = await (await app.test_client().get("/api/github-activity")).get_json()
    assert stale == {**fresh, "_stale": True}

    monkeypatch.setattr(live, "_github_cache", TTLCache(0))
    failed = await app.test_client().get("/api/github-activity")
    assert failed.status_code == 502


async def test_github_without_token_or_preview_is_503(monkeypatch, http):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_ACTIVITY_PREVIEW", raising=False)
    response = await app.test_client().get("/api/github-activity")
    assert response.status_code == 503
    assert http.calls == []


# --- Icons ----------------------------------------------------------------------------

@pytest.mark.parametrize("path", ["/favicon.ico", "/apple-touch-icon.png", "/apple-touch-icon-precomposed.png"])
async def test_conventional_icon_paths_resolve_to_real_images(path):
    response = await app.test_client().get(path, follow_redirects=True)
    assert response.status_code == 200
    assert response.mimetype in {"image/svg+xml", "image/png"}
    assert len(await response.get_data()) > 100
