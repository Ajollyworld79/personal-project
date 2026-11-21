"""Serve the React build and its prerendered public content through Quart."""
import json
import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from quart import render_template
from app.data import PROJECTS

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "static/dist"

def cv_content() -> dict:
    return json.loads((ROOT / "content/cv.json").read_text(encoding="utf-8"))

PAGE_PATHS = {"home": "/", "about": "/about", "projects": "/projects"}

def base_url() -> str:
    return cv_content()["contact"]["portfolio"].rstrip("/")

def page_url(page: str) -> str:
    return base_url() + PAGE_PATHS[page]

def person_schema(cv: dict) -> dict:
    contact = cv["contact"]
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "Gustav Wind Christensen",
        "url": contact["portfolio"],
        "jobTitle": "Production AI Engineer",
        "email": "mailto:" + contact["email"],
        "address": {"@type": "PostalAddress", "addressCountry": "DK"},
        "sameAs": [f"https://www.linkedin.com/in/{contact['linkedin']}",
                   f"https://github.com/{contact['github']}"],
        "knowsAbout": cv["skills"],
    }

@lru_cache
def _built_page(page: str) -> tuple[str, list[str], str, dict]:
    """Build output is fixed for the life of the process, so read it once per page."""
    manifest = json.loads((DIST / ".vite/manifest.json").read_text(encoding="utf-8"))
    asset = manifest["frontend/main.tsx"]
    entry = "/static/dist/" + asset["file"]
    css = ["/static/dist/" + path for path in asset.get("css", [])]
    prerendered = (DIST / "prerender" / f"{page}.html").read_text(encoding="utf-8")
    content = json.loads((DIST / "prerender/content.json").read_text(encoding="utf-8"))
    return entry, css, prerendered, content

async def render_page(page: str, title: str, meta_description: str) -> str:
    dev_server = os.environ.get("VITE_DEV_SERVER", "").rstrip("/")
    if dev_server:
        dev_server += "/static/dist"
        content = {"author": "Gustav Wind Christensen", "year": datetime.now(timezone.utc).year,
                   "projects": [p.model_dump(mode="json") for p in PROJECTS], "cv": cv_content()}
        entry, css, prerendered = f"{dev_server}/frontend/main.tsx", [], ""
    else:
        entry, css, prerendered, content = _built_page(page)
    cv = cv_content()
    return await render_template("react.html", page=page, title=title, meta_description=meta_description,
                                 content=content, entry=entry, css=css, prerendered=prerendered,
                                 dev_server=dev_server, canonical=page_url(page), json_ld=person_schema(cv))
