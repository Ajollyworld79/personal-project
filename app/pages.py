"""Prerendered React pages, the PDF CV and icon paths browsers request by convention."""
import asyncio

from quart import Blueprint, Response, redirect

from app.config import get_settings
from app.data import PROJECTS
from app.frontend import PAGE_PATHS, base_url, cv_content, page_url, render_page
from app.pdf_cv import generate_cv_pdf

bp = Blueprint("pages", __name__)
settings = get_settings()


@bp.get("/")
async def index():
    return await render_page(
        "home",
        title="Gustav Christensen — Production AI Engineer",
        meta_description=(
            "Production AI engineer building autonomous LLM workflows, RAG systems, "
            "and data pipelines in Python. Explore live systems or ask the CV assistant."
        ),
    )


@bp.get("/about")
async def about():
    return await render_page(
        "about",
        title="About Gustav Christensen — Production AI Engineer",
        meta_description=(
            "Gustav Wind Christensen is a production AI engineer with 20+ years in IT, "
            "spanning data engineering, automation, operations, RAG, and LLM systems."
        ),
    )


@bp.get("/projects")
async def projects():
    return await render_page(
        "projects",
        title="Production AI Projects — Gustav Christensen",
        meta_description=(
            "Production AI systems built by Gustav Christensen: autonomous LLM workflows, "
            "RAG support, document intelligence, MCP, and data pipelines."
        ),
    )


@bp.get("/robots.txt")
async def robots():
    body = f"User-agent: *\nAllow: /\nSitemap: {base_url()}/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@bp.get("/sitemap.xml")
async def sitemap():
    urls = "".join(f"  <url><loc>{page_url(page)}</loc></url>\n" for page in PAGE_PATHS)
    body = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    return Response(body, mimetype="application/xml")


@bp.get("/download_cv")
async def download_cv():
    """The React about page and PDF share content/cv.json.

    Generated fresh on every download (the PDF is dated), in a worker thread so
    fpdf's CPU work never blocks the event loop.
    """
    packet = await asyncio.to_thread(
        generate_cv_pdf, author=settings.author_name, projects=PROJECTS, data=cv_content()
    )
    data = packet.getvalue()
    filename = f"CV_{settings.author_name.replace(' ', '_')}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(data, mimetype="application/pdf", headers=headers)


# Crawlers and older clients request these root paths without reading <link rel="icon">.
@bp.get("/favicon.ico")
async def favicon():
    return redirect("/static/assets/images/favicon.svg", 301)


@bp.get("/apple-touch-icon.png")
@bp.get("/apple-touch-icon-precomposed.png")
async def apple_touch_icon():
    return redirect("/static/assets/images/apple-touch-icon.png", 301)
