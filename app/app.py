import os, sys
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Sikrer at roden er på sys.path når filen køres direkte (python app/app.py)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.config import get_settings  # type: ignore
from app.models import ProjectsResponse  # type: ignore
from app.data import PROJECTS  # type: ignore
from datetime import datetime
import orjson

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
)

# Mount static
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# JSON response override with orjson for speed
class ORJSONResponse(HTMLResponse):
    media_type = "application/json"

    def render(self, content: dict) -> bytes:
        return orjson.dumps(content)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    context = {
        "projects": PROJECTS,
        "author": settings.author_name,
        "current_year": datetime.utcnow().year,
    }
    # Ny signatur: TemplateResponse(request, name, context)
    return templates.TemplateResponse(request, "index.html", context)

@app.get("/om", response_class=HTMLResponse)
async def about(request: Request):
    context = {
        "author": settings.author_name,
        "current_year": datetime.utcnow().year,
    }
    return templates.TemplateResponse(request, "about.html", context)

@app.get("/api/projects", response_model=ProjectsResponse)
async def list_projects():
    return ProjectsResponse(projects=PROJECTS)

@app.get("/healthz")
async def healthz():
    return {"status": "ok", "version": settings.version}

if __name__ == "__main__":
    # Muliggør: python app/app.py
    import uvicorn
    uvicorn.run(
        "app.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        factory=False,
    )
