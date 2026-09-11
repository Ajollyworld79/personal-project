"""Export public content for React prerendering; never serialize settings or secrets."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.data import PROJECTS

print(json.dumps({
    "author": "Gustav Wind Christensen",
    "year": datetime.now(timezone.utc).year,
    "projects": [project.model_dump(mode="json") for project in PROJECTS],
    "cv": json.loads((ROOT / "content/cv.json").read_text(encoding="utf-8")),
}, ensure_ascii=False))
