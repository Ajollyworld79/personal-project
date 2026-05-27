from typing import List
from datetime import datetime, timezone
import os
import sys
import re
import html as html_lib

# Ensure project root in path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from quart import Quart, render_template, jsonify, Response, request
from app.config import get_settings
from app.models import Project
from app.data import PROJECTS
import io
import time
import ssl
from fpdf import FPDF, XPos, YPos
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


def _clean_text_for_pdf(text: str) -> str:
    """Remove special characters that can't be encoded in latin-1"""
    if not text:
        return text
    # Replace special characters
    replacements = {
        "\u2122": "",  # ™ trademark
        "\u00ae": "",  # ® registered
        "\u00a9": "",  # © copyright
        "\u2014": "-",  # em dash
        "\u2013": "-",  # en dash
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u201c": '"',  # left double quote
        "\u201d": '"',  # right double quote
        "\xa0": " ",  # non-breaking space
        "&": "and",  # ampersand
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining non-latin-1 characters
    try:
        text.encode("latin-1")
    except UnicodeEncodeError:
        text = text.encode("latin-1", errors="ignore").decode("latin-1")
    return text


def _strip_html(text: str) -> str:
    """Strip HTML tags, comments, and entities for PDF rendering."""
    if not text:
        return ""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    # Convert block-level boundaries to spaces so adjacent words don't merge.
    text = re.sub(r"<\s*(br|/p|/div|/li|/h\d)\b[^>]*>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# Color palette — matches website accent colors
_C_PINK = (242, 132, 158)  # #F2849E
_C_BLUE = (126, 207, 244)  # #7ECFF4
_C_DARK = (45, 55, 72)  # #2D3748
_C_TEXT = (74, 85, 104)  # #4A5568
_C_MUTED = (113, 128, 150)  # #718096
_C_SIDEBAR_BG = (247, 250, 252)  # #F7FAFC
_C_BADGE_BG = (253, 235, 240)  # very light pink
_C_DIVIDER = (224, 224, 230)
_C_WHITE = (255, 255, 255)


def generate_cv_pdf(
    author: str,
    projects: List[Project],
    contact_info: dict | None = None,
    skills: list | None = None,
    languages: str | None = None,
    summary: str | None = None,
    certifications: list | None = None,
    experience: str | None = None,
    education: list | None = None,
):
    """Generate a professional CV PDF with two-column layout + dedicated projects page."""

    # Clean inputs
    author_clean = _clean_text_for_pdf(author)
    if summary:
        summary = _clean_text_for_pdf(summary)
    if languages:
        languages = _clean_text_for_pdf(languages)
    if experience:
        experience = _clean_text_for_pdf(experience)
    if certifications:
        certifications = [_clean_text_for_pdf(c) for c in certifications]
    if education:
        education = [_clean_text_for_pdf(e) for e in education]
    if skills:
        skills = [_clean_text_for_pdf(s) for s in skills]

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    PAGE_W, PAGE_H = pdf.w, pdf.h  # 210 x 297
    HERO_H = 42

    # --- Hero header ---
    pdf.set_fill_color(*_C_DARK)
    pdf.rect(0, 0, PAGE_W, HERO_H, "F")
    # Pink accent stripe
    pdf.set_fill_color(*_C_PINK)
    pdf.rect(0, HERO_H, PAGE_W, 2.5, "F")

    pdf.set_text_color(*_C_WHITE)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_xy(0, 12)
    pdf.cell(PAGE_W, 10, author_clean, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_xy(0, 24)
    pdf.cell(
        PAGE_W,
        6,
        "AI, LLM and Python Developer",
        align="C",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    # Generation date
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(200, 200, 200)
    pdf.set_xy(PAGE_W - 50, 34)
    pdf.cell(40, 4, f"Generated {datetime.now().strftime('%B %Y')}", align="R")

    # --- Two-column geometry ---
    SIDEBAR_W = 64
    SIDEBAR_PAD = 6
    SIDEBAR_CONTENT_W = SIDEBAR_W - 2 * SIDEBAR_PAD
    SIDEBAR_TOP = HERO_H + 2.5
    MAIN_X = SIDEBAR_W + 8
    MAIN_W = PAGE_W - MAIN_X - 10  # 10mm right margin
    MAIN_TOP = SIDEBAR_TOP + 5

    # Sidebar background (full page height below hero)
    pdf.set_fill_color(*_C_SIDEBAR_BG)
    pdf.rect(0, SIDEBAR_TOP, SIDEBAR_W, PAGE_H - SIDEBAR_TOP, "F")

    def sidebar_header(title: str):
        pdf.set_x(SIDEBAR_PAD)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*_C_PINK)
        pdf.cell(
            SIDEBAR_CONTENT_W, 5, title.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )
        # Tiny pink underline
        y = pdf.get_y() + 0.4
        pdf.set_fill_color(*_C_PINK)
        pdf.rect(SIDEBAR_PAD, y, 10, 0.7, "F")
        pdf.set_y(y + 2.5)

    def main_header(title: str):
        pdf.set_x(MAIN_X)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*_C_DARK)
        pdf.cell(MAIN_W, 6, title.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        y = pdf.get_y() + 0.3
        pdf.set_fill_color(*_C_PINK)
        pdf.rect(MAIN_X, y, 22, 0.9, "F")
        pdf.set_y(y + 3)

    # ================
    # SIDEBAR CONTENT
    # ================
    pdf.set_y(SIDEBAR_TOP + 6)

    if contact_info:
        sidebar_header("Contact")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*_C_TEXT)
        if contact_info.get("phone"):
            pdf.set_x(SIDEBAR_PAD)
            pdf.multi_cell(SIDEBAR_CONTENT_W, 4, contact_info["phone"])
        if contact_info.get("email"):
            email = contact_info["email"]
            pdf.set_x(SIDEBAR_PAD)
            pdf.set_text_color(*_C_BLUE)
            pdf.multi_cell(SIDEBAR_CONTENT_W, 4, email, link=f"mailto:{email}")
            pdf.set_text_color(*_C_TEXT)
        if contact_info.get("linkedin"):
            ln = contact_info["linkedin"]
            url = ln if ln.startswith("http") else f"https://linkedin.com/in/{ln}"
            pdf.set_x(SIDEBAR_PAD)
            pdf.set_text_color(*_C_BLUE)
            pdf.multi_cell(SIDEBAR_CONTENT_W, 4, ln, link=url)
            pdf.set_text_color(*_C_TEXT)
        if contact_info.get("portfolio"):
            url = contact_info["portfolio"]
            short = url.replace("https://", "").replace("http://", "").rstrip("/")
            pdf.set_x(SIDEBAR_PAD)
            pdf.set_text_color(*_C_BLUE)
            pdf.multi_cell(SIDEBAR_CONTENT_W, 4, short, link=url)
            pdf.set_text_color(*_C_TEXT)
        pdf.ln(3)

    if skills:
        sidebar_header("Core Skills")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*_C_TEXT)
        for skill in skills:
            pdf.set_x(SIDEBAR_PAD)
            # Small pink bullet
            pdf.set_fill_color(*_C_PINK)
            bullet_y = pdf.get_y() + 1.7
            pdf.rect(SIDEBAR_PAD, bullet_y, 1.4, 1.4, "F")
            pdf.set_x(SIDEBAR_PAD + 3)
            pdf.multi_cell(SIDEBAR_CONTENT_W - 3, 4, skill)
        pdf.ln(3)

    if languages:
        sidebar_header("Languages")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*_C_TEXT)
        pdf.set_x(SIDEBAR_PAD)
        pdf.multi_cell(SIDEBAR_CONTENT_W, 4, languages)
        pdf.ln(3)

    if education:
        sidebar_header("Education")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*_C_TEXT)
        for edu in education:
            pdf.set_x(SIDEBAR_PAD)
            pdf.multi_cell(SIDEBAR_CONTENT_W, 3.8, edu)
            pdf.ln(0.5)

    # ================
    # MAIN CONTENT
    # ================
    pdf.set_xy(MAIN_X, MAIN_TOP)

    if summary:
        main_header("Profile")
        pdf.set_x(MAIN_X)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*_C_TEXT)
        pdf.multi_cell(MAIN_W, 4.5, summary)
        pdf.ln(2)

    if experience:
        main_header("Experience")
        date_re = re.compile(r"^\s*\d{4}\b")
        prev_was_date = False
        for line in experience.split("\n"):
            line = line.strip()
            if not line:
                prev_was_date = False
                continue
            if date_re.match(line):
                # Date pill — small pink uppercase label
                pdf.set_x(MAIN_X)
                pdf.set_font("Helvetica", "B", 7)
                pdf.set_text_color(*_C_PINK)
                pdf.cell(0, 4, line.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                prev_was_date = True
            elif prev_was_date and len(line) < 60:
                # Role title — bold, right after a date line
                pdf.set_x(MAIN_X)
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(*_C_DARK)
                pdf.multi_cell(MAIN_W, 4.6, line)
                prev_was_date = False
            else:
                # Body / company / description
                pdf.set_x(MAIN_X)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*_C_TEXT)
                pdf.multi_cell(MAIN_W, 4, line)
                prev_was_date = False
            pdf.ln(0.2)
        pdf.ln(1.5)

    if certifications:
        main_header("Certifications")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*_C_TEXT)
        for cert in certifications:
            pdf.set_x(MAIN_X)
            pdf.set_fill_color(*_C_PINK)
            bullet_y = pdf.get_y() + 1.6
            pdf.rect(MAIN_X, bullet_y, 1.4, 1.4, "F")
            pdf.set_x(MAIN_X + 3)
            pdf.multi_cell(MAIN_W - 3, 4.4, cert)
        pdf.ln(1.5)

    # Education renders in the sidebar — no main-column section.

    # ================
    # PAGE 2+ — PROJECTS
    # ================
    if projects:
        pdf.add_page()

        # Mini hero strip
        pdf.set_fill_color(*_C_DARK)
        pdf.rect(0, 0, PAGE_W, 18, "F")
        pdf.set_fill_color(*_C_PINK)
        pdf.rect(0, 18, PAGE_W, 1.5, "F")
        pdf.set_text_color(*_C_WHITE)
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_xy(15, 5)
        pdf.cell(0, 8, "Featured Projects", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(200, 200, 200)
        pdf.set_xy(PAGE_W - 80, 8.5)
        pdf.cell(70, 5, "See live demos at the portfolio URL on page 1", align="R")

        pdf.set_y(26)
        margin_x = 15
        card_w = PAGE_W - 2 * margin_x

        for project in projects:
            # Project title
            pdf.set_x(margin_x)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*_C_DARK)
            pdf.multi_cell(card_w, 5.5, _clean_text_for_pdf(project.title))

            # Description (intro only — text before <!--more-->)
            pdf.set_x(margin_x)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*_C_TEXT)
            raw_desc = project.description.split("<!--more-->", 1)[0]
            desc = _clean_text_for_pdf(_strip_html(raw_desc))
            if len(desc) > 360:
                desc = desc[:357].rstrip() + "..."
            pdf.multi_cell(card_w, 4.2, desc)

            # Tech badges (wrap to multiple rows)
            if project.technologies:
                pdf.ln(0.5)
                pdf.set_font("Helvetica", "", 7)
                pdf.set_draw_color(*_C_PINK)
                pdf.set_line_width(0.2)
                badge_h = 4.2
                pad_x = 1.6
                badge_y = pdf.get_y()
                badge_x = margin_x
                for tech in project.technologies:
                    label = _clean_text_for_pdf(str(tech))
                    w = pdf.get_string_width(label) + 2 * pad_x
                    if badge_x + w > margin_x + card_w:
                        badge_y += badge_h + 1.4
                        badge_x = margin_x
                    pdf.set_fill_color(*_C_BADGE_BG)
                    pdf.rect(badge_x, badge_y, w, badge_h, "FD")
                    pdf.set_text_color(*_C_PINK)
                    pdf.set_xy(badge_x, badge_y + 0.4)
                    pdf.cell(w, badge_h - 0.4, label, align="C")
                    badge_x += w + 1.6
                pdf.set_y(badge_y + badge_h + 2)

            # URLs
            url_parts = []
            if project.repo_url:
                url_parts.append(("Code", str(project.repo_url)))
            if project.live_url:
                url_parts.append(("Live", str(project.live_url)))
            if url_parts:
                pdf.set_x(margin_x)
                pdf.set_font("Helvetica", "", 8)
                for label, url in url_parts:
                    short = url.replace("https://", "").replace("http://", "")
                    pdf.set_text_color(*_C_BLUE)
                    pdf.cell(
                        0,
                        3.8,
                        f"{label}: {short}",
                        new_x=XPos.LMARGIN,
                        new_y=YPos.NEXT,
                        link=url,
                    )

            # Light divider between projects
            pdf.ln(2)
            pdf.set_draw_color(*_C_DIVIDER)
            pdf.set_line_width(0.15)
            y = pdf.get_y()
            pdf.line(margin_x, y, margin_x + card_w, y)
            pdf.ln(3)

    buffer = io.BytesIO()
    raw = pdf.output()
    buffer.write(bytes(raw))
    buffer.seek(0)
    return buffer


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


@app.route("/api/cv-chat", methods=["POST"])
async def cv_chat():
    """Answer a question about Gustav's CV.

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

        # --- 1. Try real RAG via llm-assistant ----------------------------------
        try:
            timeout = aiohttp.ClientTimeout(total=15.0)
            headers = {"Content-Type": "application/json"}
            if LLM_ASSISTANT_API_KEY:
                headers["Authorization"] = f"Bearer {LLM_ASSISTANT_API_KEY}"
            connector = aiohttp.TCPConnector(ssl=_SSL_CTX)
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as http_session:
                rag_url = f"{LLM_ASSISTANT_URL.rstrip('/')}/search"
                payload = {"query": raw_query, "top_k": 4}
                async with http_session.post(rag_url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        rag_data = await resp.json()
                        if _is_useful_rag_answer(rag_data):
                            return jsonify({
                                "answer": rag_data.get("answer", ""),
                                "sources": rag_data.get("results") or rag_data.get("sources") or [],
                                "source": "rag",
                            })
                    else:
                        app.logger.info(f"cv-chat: llm-assistant returned HTTP {resp.status}; using mock")
        except (aiohttp.ClientError, OSError) as e:
            app.logger.info(f"cv-chat: llm-assistant unreachable ({e}); using mock")
        except Exception as e:
            app.logger.warning(f"cv-chat: RAG call failed ({e}); using mock")

        # --- 2. Fall back to keyword-matched mock --------------------------------
        matched = "default"
        for keywords, topic in _CV_KEYWORDS:
            if any(k in query_lower for k in keywords):
                matched = topic
                break

        answer = _CV_FACTS.get(matched, _CV_FACTS["default"])
        return jsonify({"answer": answer, "matched": matched, "source": "mock"})
    except Exception as e:
        app.logger.exception("cv-chat endpoint failure")
        return jsonify({"error": str(e)}), 500


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
    # Read the about template source and strip Jinja tags to avoid pulling full page CSS/JS
    tpl_path = os.path.join(PROJECT_ROOT, "templates", "about.html")
    try:
        with open(tpl_path, "r", encoding="utf-8") as fh:
            raw_tpl = fh.read()
    except Exception:
        raw_tpl = ""
    # Remove Jinja control structures and variable tags
    cleaned = re.sub(r"\{[%#].*?[%#]\}", "", raw_tpl, flags=re.S)
    cleaned = re.sub(r"\{\{.*?\}\}", "", cleaned, flags=re.S)
    # Extract concise contact and section summaries to include in the PDF
    email_m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", cleaned)
    phone_m = re.search(r"\+?\d[\d\s\-()]{6,}\d", cleaned)
    linkedin_m = re.search(r"https?://[^\s'\"]*linkedin[^\s'\"]*", cleaned)
    # Top Skills
    skills_block = re.search(
        r"<h3>Top Skills</h3>.*?<ul>(.*?)</ul>", cleaned, flags=re.S
    )
    skills = []
    if skills_block:
        skills = re.findall(r"<li>(.*?)</li>", skills_block.group(1), flags=re.S)
        skills = [re.sub(r"<[^>]+>", "", s).strip() for s in skills]
        skills = [html_lib.unescape(s) for s in skills]
    # Languages
    lang_block = re.search(r"<h3>Languages</h3>.*?<p>(.*?)</p>", cleaned, flags=re.S)
    langs = lang_block.group(1).strip() if lang_block else ""
    langs = re.sub(r"<br\s*/?>|<BR\s*/?>|&nbsp;", " ", langs).strip()
    langs = html_lib.unescape(langs)
    # Certifications
    cert_block = re.search(
        r"<h2>Certifications</h2>.*?<ul>(.*?)</ul>", cleaned, flags=re.S
    )
    certs = []
    if cert_block:
        certs = re.findall(r"<li>(.*?)</li>", cert_block.group(1), flags=re.S)
        certs = [re.sub(r"<[^>]+>", "", c).strip() for c in certs]
        # Remove HTML entities and special characters
        certs = [re.sub(r"<br\s*/?>|<BR\s*/?>|&nbsp;", " ", c).strip() for c in certs]
        certs = [html_lib.unescape(c) for c in certs]
    # Summary (changed from Resume)
    summary_block = re.search(r"<h2>Summary</h2>.*?<p>(.*?)</p>", cleaned, flags=re.S)
    summary = summary_block.group(1).strip() if summary_block else ""
    summary = re.sub(r"<br\s*/?>|<BR\s*/?>|&nbsp;", " ", summary).strip()
    summary = html_lib.unescape(summary)
    # Experience — capture main timeline + previous roles (up to Education heading)
    exp_block = re.search(
        r"<h2>Experience</h2>(.*?)<h2>Education</h2>", cleaned, flags=re.S
    )
    exp = ""
    if exp_block:
        raw = exp_block.group(1)
        # Add spaces between adjacent span elements (prevents tech badge concatenation)
        raw = re.sub(r"</span>\s*<span", "</span> <span", raw)
        raw = re.sub(r"<[^>]+>", "", raw)
        raw = re.sub(r"&nbsp;", " ", raw)
        raw = html_lib.unescape(raw)
        # Clean up excessive whitespace while preserving paragraph breaks
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n\s*\n\s*\n", "\n\n", raw)
        exp = raw.strip()
    # Education
    edu_block = re.search(r"<h2>Education</h2>.*?<ul>(.*?)</ul>", cleaned, flags=re.S)
    edus = []
    if edu_block:
        edus = re.findall(r"<li>(.*?)</li>", edu_block.group(1), flags=re.S)
        edus = [re.sub(r"<[^>]+>", "", e).strip() for e in edus]
        edus = [re.sub(r"<br\s*/?>|<BR\s*/?>|&nbsp;", " ", e).strip() for e in edus]
        edus = [html_lib.unescape(e) for e in edus]

    # Prepare contact info
    contact_info = {}
    if phone_m:
        contact_info["phone"] = phone_m.group(0).strip()
    if email_m:
        contact_info["email"] = email_m.group(0).strip()
    if linkedin_m:
        linkedin_url = linkedin_m.group(0).strip()
        if "linkedin.com/in/" in linkedin_url:
            contact_info["linkedin"] = linkedin_url.split("linkedin.com/in/")[
                -1
            ].rstrip("/")
        else:
            contact_info["linkedin"] = linkedin_url

    # Portfolio URL — prefer settings, else use the canonical custom domain
    contact_info["portfolio"] = (
        getattr(settings, "portfolio_url", "") or "https://gustavchristensen.dev"
    )

    # Generate PDF with structured data
    packet = generate_cv_pdf(
        author=settings.author_name,
        projects=PROJECTS,
        contact_info=contact_info if contact_info else None,
        skills=skills if skills else None,
        languages=langs if langs else None,
        summary=summary if summary else None,
        certifications=certs if certs else None,
        experience=exp if exp else None,
        education=edus if edus else None,
    )

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
