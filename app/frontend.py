"""Serve the React build and its prerendered public content through Quart."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from quart import render_template
from app.data import PROJECTS

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "static/dist"

def cv_content() -> dict:
    return json.loads((ROOT / "content/cv.json").read_text(encoding="utf-8"))

async def render_page(page: str, title: str, meta_description: str) -> str:
    dev_server = os.environ.get("VITE_DEV_SERVER", "").rstrip("/")
    if dev_server:
        dev_server += "/static/dist"
        content = {"author": "Gustav Wind Christensen", "year": datetime.now(timezone.utc).year,
                   "projects": [p.model_dump(mode="json") for p in PROJECTS], "cv": cv_content()}
        entry, css, prerendered = f"{dev_server}/frontend/main.tsx", [], ""
    else:
        manifest = json.loads((DIST / ".vite/manifest.json").read_text(encoding="utf-8"))
        asset = manifest["frontend/main.tsx"]
        entry = "/static/dist/" + asset["file"]
        css = ["/static/dist/" + path for path in asset.get("css", [])]
        prerendered = (DIST / "prerender" / f"{page}.html").read_text(encoding="utf-8")
        content = json.loads((DIST / "prerender/content.json").read_text(encoding="utf-8"))
    return await render_template("react.html", page=page, title=title, meta_description=meta_description,
                                 content=content, entry=entry, css=css, prerendered=prerendered,
                                 dev_server=dev_server)
