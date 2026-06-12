"""Polished CV PDF — mirrors the site's terminal/LLM identity in print.

Layout: full-height dark sidebar (photo, contact, skills, QR) + white main
column (name, profile, experience timeline, certifications). Page 2+ renders
featured projects as cards. Typography: JetBrains Mono for headings/accents,
Inter for body — same pairing as the website.
"""

from datetime import datetime
import html as html_lib
import io
import os
import re
from typing import Optional

from fpdf import FPDF

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_FONTS_DIR = os.path.join(PROJECT_ROOT, "static", "fonts")
_AVATAR = os.path.join(PROJECT_ROOT, "static", "assets", "images", "me-circle.png")
_QR = os.path.join(PROJECT_ROOT, "static", "assets", "images", "cv-qr.png")

# --- Palette: print-friendly tints of the site's colors ----------------------
INK = (30, 33, 42)
MUTED = (90, 97, 110)
FAINT = (152, 158, 168)
PINK = (216, 86, 120)          # accent text on white
PINK_BRIGHT = (242, 132, 158)  # graphic elements (site pink)
BLUE = (40, 118, 158)
SIDEBAR_BG = (19, 19, 28)
SIDE_INK = (233, 237, 243)
SIDE_MUTE = (146, 153, 166)
DIVIDER = (226, 228, 233)
CARD_BG = (246, 247, 249)
CARD_BORDER = (228, 230, 235)

SIDEBAR_W = 68
SIDE_PAD = 9
MAIN_X = SIDEBAR_W + 11
PAGE_W, PAGE_H = 210, 297
MAIN_W = PAGE_W - MAIN_X - 13

SANS = "Inter"
SANS_SB = "InterSB"
MONO = "JBMono"
MONO_SB = "JBMonoSB"


def _unescape(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _strip_html_block(text: str) -> str:
    """Strip tags/comments but keep block boundaries as spaces."""
    if not text:
        return ""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<\s*(br|/p|/div|/li|/h\d)\b[^>]*>", " ", text, flags=re.I)
    return _unescape(text)


def _latin1(text: str) -> str:
    """Fallback cleaning when the unicode fonts are unavailable."""
    replacements = {"—": "-", "–": "-", "‘": "'", "’": "'",
                    "“": '"', "”": '"', "\xa0": " ", "·": "-"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="ignore").decode("latin-1")


# =============================================================================
# Extraction — structured CV data out of the about.html template source
# =============================================================================

def extract_cv_data(raw_template: str) -> dict:
    """Parse the about page template into structured CV data.

    The about page stays the single source of truth; this reads its timeline,
    cards, and lists into dicts the renderer can lay out properly.
    """
    cleaned = re.sub(r"\{[%#].*?[%#]\}", "", raw_template, flags=re.S)
    cleaned = re.sub(r"\{\{.*?\}\}", "", cleaned, flags=re.S)

    data: dict = {}

    email_m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", cleaned)
    linkedin_m = re.search(r'https?://[^\s\'"]*linkedin\.com/in/([^\s\'"<]+)', cleaned)
    github_m = re.search(r'https?://github\.com/([\w-]+)', cleaned)
    location_m = re.search(r"Location:\s*([^<]+)<", cleaned)
    data["contact"] = {
        "email": email_m.group(0) if email_m else None,
        "linkedin": linkedin_m.group(1).rstrip("/") if linkedin_m else None,
        "github": github_m.group(1) if github_m else None,
        "location": location_m.group(1).strip() if location_m else None,
        "portfolio": "https://gustavchristensen.dev",
    }

    skills_block = re.search(r"<h3>Top Skills</h3>.*?<ul>(.*?)</ul>", cleaned, flags=re.S)
    data["skills"] = [
        _unescape(s) for s in re.findall(r"<li>(.*?)</li>", skills_block.group(1), flags=re.S)
    ] if skills_block else []

    lang_block = re.search(r"<h3>Languages</h3>.*?<ul>(.*?)</ul>", cleaned, flags=re.S)
    data["languages"] = [
        _unescape(s) for s in re.findall(r"<li>(.*?)</li>", lang_block.group(1), flags=re.S)
    ] if lang_block else []

    summary_block = re.search(r"<h2>Summary</h2>\s*<p>(.*?)</p>", cleaned, flags=re.S)
    data["summary"] = _unescape(summary_block.group(1)) if summary_block else ""

    headline = re.search(r'<p class="cv__lede">(.*?)</p>', cleaned, flags=re.S)
    data["headline"] = _unescape(headline.group(1)) if headline else ""

    # Experience — main timeline items (skip the compact "previous roles" list)
    main_part, _, compact_part = cleaned.partition("timeline-compact")
    roles = []
    for chunk in main_part.split('<li class="timeline-item">')[1:]:
        date_m = re.search(r'<p class="timeline-date">(.*?)</p>', chunk, flags=re.S)
        role_m = re.search(r'<h3 class="timeline-role">(.*?)</h3>', chunk, flags=re.S)
        comp_m = re.search(r'<p class="timeline-company">(.*?)</p>', chunk, flags=re.S)
        if not role_m:
            continue
        summary_m = re.search(
            r'<p class="timeline-company">.*?</p>\s*<p>(.*?)</p>', chunk, flags=re.S
        )
        points_block = re.search(r'<ul class="timeline-points">(.*?)</ul>', chunk, flags=re.S)
        points = [
            _unescape(p) for p in re.findall(r"<li>(.*?)</li>", points_block.group(1), flags=re.S)
        ] if points_block else []
        roles.append({
            "date": _unescape(date_m.group(1)) if date_m else "",
            "role": _unescape(role_m.group(1)),
            "company": _unescape(comp_m.group(1)) if comp_m else "",
            "summary": _unescape(summary_m.group(1)) if summary_m else "",
            "points": points,
        })
    data["roles"] = roles

    prev = []
    for chunk in compact_part.split('<li class="timeline-item">')[1:]:
        date_m = re.search(r'<p class="timeline-date">(.*?)</p>', chunk, flags=re.S)
        content_m = re.search(r'<div class="timeline-content">(.*?)</div>', chunk, flags=re.S)
        if not content_m:
            continue
        prev.append({
            "date": _unescape(date_m.group(1)) if date_m else "",
            "text": _unescape(content_m.group(1)),
        })
    data["previous_roles"] = prev

    certs = []
    cert_block = re.search(r"<h2>Certifications</h2>(.*?)<hr", cleaned, flags=re.S)
    if cert_block:
        for chunk in re.findall(r'<p class="cert-name">(.*?)</p>', cert_block.group(1), flags=re.S):
            issuer_m = re.search(r'<span class="cert-issuer">(.*?)</span>', chunk, flags=re.S)
            name = re.sub(r'<span class="cert-issuer">.*?</span>', "", chunk, flags=re.S)
            certs.append({
                "name": _unescape(name),
                "issuer": _unescape(issuer_m.group(1)) if issuer_m else "",
            })
    data["certifications"] = certs

    edu_block = re.search(r"<h2>Education[^<]*</h2>.*?<ul[^>]*>(.*?)</ul>", cleaned, flags=re.S)
    data["education"] = [
        _unescape(e) for e in re.findall(r"<li>(.*?)</li>", edu_block.group(1), flags=re.S)
    ] if edu_block else []

    return data


# =============================================================================
# Rendering
# =============================================================================

class _CVPDF(FPDF):
    """A4 CV with a footer strip on every page."""

    fonts_ok = False

    def footer(self):
        x0 = MAIN_X if self.page_no() == 1 else 14
        self.set_y(-13)
        self.set_draw_color(*DIVIDER)
        self.set_line_width(0.25)
        self.line(x0, self.get_y(), PAGE_W - 13, self.get_y())
        self.set_y(-10.5)
        self.set_x(x0)
        font = MONO if self.fonts_ok else "Helvetica"
        self.set_font(font, "", 6.4)
        self.set_text_color(*FAINT)
        generated = datetime.now().strftime("%B %Y")
        self.cell(
            0, 4,
            f"async def build_portfolio()  ·  gustavchristensen.dev  ·  generated {generated}",
        )


def _register_fonts(pdf: FPDF) -> bool:
    try:
        pdf.add_font(SANS, "", os.path.join(_FONTS_DIR, "Inter-Regular.ttf"))
        pdf.add_font(SANS, "B", os.path.join(_FONTS_DIR, "Inter-Bold.ttf"))
        pdf.add_font(SANS_SB, "", os.path.join(_FONTS_DIR, "Inter-SemiBold.ttf"))
        pdf.add_font(MONO, "", os.path.join(_FONTS_DIR, "JetBrainsMono-Regular.ttf"))
        pdf.add_font(MONO, "B", os.path.join(_FONTS_DIR, "JetBrainsMono-Bold.ttf"))
        pdf.add_font(MONO_SB, "", os.path.join(_FONTS_DIR, "JetBrainsMono-SemiBold.ttf"))
        return True
    except Exception:
        return False


def _side_header(pdf: FPDF, title: str, y: float) -> float:
    pdf.set_xy(SIDE_PAD, y)
    pdf.set_font(MONO_SB, "", 7.6)
    pdf.set_text_color(*PINK_BRIGHT)
    pdf.cell(SIDEBAR_W - 2 * SIDE_PAD, 4, title.lower())
    y += 5.2
    pdf.set_draw_color(*PINK_BRIGHT)
    pdf.set_line_width(0.5)
    pdf.line(SIDE_PAD, y, SIDE_PAD + 9, y)
    return y + 3.4


def _chip_row(pdf: FPDF, items, x0, y, max_w, *, font_size=6.6, on_dark=True) -> float:
    """Wrap pill chips across lines; returns the y below the last row."""
    chip_h = 5.4
    gap = 1.8
    x = x0
    pdf.set_font(MONO, "", font_size)
    for label in items:
        w = pdf.get_string_width(label) + 4.6
        if x + w > x0 + max_w and x > x0:
            x = x0
            y += chip_h + gap
        if on_dark:
            pdf.set_draw_color(120, 70, 88)
            pdf.set_fill_color(31, 31, 43)
            pdf.set_text_color(*SIDE_INK)
        else:
            pdf.set_draw_color(231, 180, 195)
            pdf.set_fill_color(252, 243, 246)
            pdf.set_text_color(*PINK)
        pdf.set_line_width(0.25)
        pdf.rect(x, y, w, chip_h, "FD", round_corners=True, corner_radius=1.6)
        pdf.set_xy(x, y + 0.35)
        pdf.cell(w, chip_h - 0.7, label, align="C")
        x += w + gap
    return y + chip_h


def _main_header(pdf: FPDF, title: str) -> None:
    y = pdf.get_y()
    pdf.set_xy(MAIN_X, y)
    pdf.set_font(MONO_SB, "", 9.8)
    pdf.set_text_color(*PINK)
    pdf.cell(5, 5.2, "▸")  # ▸ — same section marker as the site
    pdf.set_text_color(*INK)
    pdf.cell(0, 5.2, title.lower())
    y += 6.4
    pdf.set_draw_color(*DIVIDER)
    pdf.set_line_width(0.25)
    pdf.line(MAIN_X, y, PAGE_W - 13, y)
    pdf.set_y(y + 3.2)


def _sidebar(pdf: FPDF, data: dict) -> None:
    pdf.set_fill_color(*SIDEBAR_BG)
    pdf.rect(0, 0, SIDEBAR_W, PAGE_H, "F")
    # thin pink seam between sidebar and main — ties to the site accent
    pdf.set_fill_color(*PINK_BRIGHT)
    pdf.rect(SIDEBAR_W - 0.8, 0, 0.8, PAGE_H, "F")

    y = 13.0
    if os.path.exists(_AVATAR):
        size = 36
        pdf.image(_AVATAR, x=(SIDEBAR_W - size) / 2, y=y, w=size)
        y += size + 4
        pdf.set_xy(0, y)
        pdf.set_font(MONO, "", 6.8)
        pdf.set_text_color(*SIDE_MUTE)
        pdf.cell(SIDEBAR_W, 4, "gustav.about()", align="C")
        y += 9

    contact = data.get("contact") or {}
    y = _side_header(pdf, "contact", y)
    rows = []
    if contact.get("email"):
        rows.append(("email", contact["email"], f"mailto:{contact['email']}"))
    if contact.get("linkedin"):
        rows.append(("linkedin", contact["linkedin"],
                     f"https://www.linkedin.com/in/{contact['linkedin']}"))
    if contact.get("github"):
        rows.append(("github", f"@{contact['github']}",
                     f"https://github.com/{contact['github']}"))
    if contact.get("location"):
        rows.append(("location", contact["location"], None))
    for label, value, link in rows:
        pdf.set_xy(SIDE_PAD, y)
        pdf.set_font(MONO, "", 5.8)
        pdf.set_text_color(*SIDE_MUTE)
        pdf.cell(SIDEBAR_W - 2 * SIDE_PAD, 3.2, label)
        y += 3.4
        pdf.set_xy(SIDE_PAD, y)
        pdf.set_font(SANS, "", 8.2)
        pdf.set_text_color(*SIDE_INK)
        pdf.cell(SIDEBAR_W - 2 * SIDE_PAD, 4.2, value, link=link or "")
        y += 6.2
    y += 2.5

    skills = data.get("skills") or []
    if skills:
        y = _side_header(pdf, "core_skills", y)
        # plain rows, not chips — several skill labels are too wide for chips
        for skill in skills:
            pdf.set_fill_color(*PINK_BRIGHT)
            pdf.rect(SIDE_PAD + 0.3, y + 1.5, 1.1, 1.1, "F")
            pdf.set_xy(SIDE_PAD + 3.4, y)
            pdf.set_font(SANS, "", 7.8)
            pdf.set_text_color(*SIDE_INK)
            pdf.multi_cell(SIDEBAR_W - 2 * SIDE_PAD - 3.4, 4.0, skill, align="L")
            y = pdf.get_y() + 1.3
        y += 4.5

    languages = data.get("languages") or []
    if languages:
        y = _side_header(pdf, "languages", y)
        for lang in languages:
            pdf.set_xy(SIDE_PAD, y)
            pdf.set_font(SANS, "", 8.2)
            pdf.set_text_color(*SIDE_INK)
            pdf.cell(SIDEBAR_W - 2 * SIDE_PAD, 4.4, lang)
            y += 5.0
        y += 4

    education = data.get("education") or []
    if education:
        y = _side_header(pdf, "education", y)
        pdf.set_text_color(*SIDE_INK)
        for edu in education[:4]:
            pdf.set_xy(SIDE_PAD, y)
            pdf.set_font(SANS, "", 7.2)
            pdf.multi_cell(SIDEBAR_W - 2 * SIDE_PAD, 3.6, edu, align="L")
            y = pdf.get_y() + 1.6
        y += 3

    # QR card pinned near the bottom
    if os.path.exists(_QR):
        qr_size = 22
        card = qr_size + 5
        qy = PAGE_H - card - 12
        qx = (SIDEBAR_W - card) / 2
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(qx, qy, card, card, "F", round_corners=True, corner_radius=2)
        pdf.image(_QR, x=qx + 2.5, y=qy + 2.5, w=qr_size,
                  link="https://gustavchristensen.dev")
        pdf.set_xy(0, qy + card + 1.6)
        pdf.set_font(MONO, "", 6.4)
        pdf.set_text_color(126, 207, 244)
        pdf.cell(SIDEBAR_W, 4, "gustavchristensen.dev", align="C",
                 link="https://gustavchristensen.dev")


def _main_column(pdf: FPDF, author: str, data: dict) -> None:
    pdf.set_xy(MAIN_X, 15)
    pdf.set_font(MONO, "B", 21)
    pdf.set_text_color(*INK)
    pdf.cell(pdf.get_string_width(author), 9.5, author)
    pdf.set_text_color(*PINK_BRIGHT)
    pdf.cell(4, 9.5, ".")
    pdf.set_xy(MAIN_X, 26)
    pdf.set_font(MONO_SB, "", 10)
    pdf.set_text_color(*PINK)
    pdf.cell(pdf.get_string_width(">>> ") + 1, 5.4, ">>>")
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 5.4, "Python & LLM Engineer")
    pdf.set_y(36)

    if data.get("summary"):
        _main_header(pdf, "profile")
        pdf.set_x(MAIN_X)
        pdf.set_font(SANS, "", 8.6)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(MAIN_W, 4.4, data["summary"], align="L")
        pdf.ln(4)

    roles = data.get("roles") or []
    if roles:
        _main_header(pdf, "experience")
        dot_x = MAIN_X + 1.6
        text_x = MAIN_X + 7
        text_w = PAGE_W - 13 - text_x
        prev_dot_y = None
        for role in roles:
            y = pdf.get_y() + 1
            # connecting line from the previous entry's dot
            if prev_dot_y is not None:
                pdf.set_draw_color(*DIVIDER)
                pdf.set_line_width(0.4)
                pdf.line(dot_x, prev_dot_y + 2.4, dot_x, y + 0.6)
            pdf.set_fill_color(*PINK_BRIGHT)
            pdf.set_draw_color(*PINK_BRIGHT)
            pdf.ellipse(dot_x - 1.4, y + 0.6, 2.8, 2.8, "F")
            prev_dot_y = y + 0.6

            pdf.set_xy(text_x, y)
            pdf.set_font(MONO, "", 6.8)
            pdf.set_text_color(*PINK)
            pdf.cell(0, 3.6, role.get("date", "").upper())
            pdf.set_xy(text_x, y + 4.2)
            pdf.set_font(SANS_SB, "", 10.4)
            pdf.set_text_color(*INK)
            pdf.cell(0, 5, role.get("role", ""))
            pdf.set_xy(text_x, y + 9.4)
            pdf.set_font(SANS, "", 7.8)
            pdf.set_text_color(*FAINT)
            pdf.cell(0, 3.8, role.get("company", ""))
            yy = y + 14
            if role.get("summary"):
                pdf.set_xy(text_x, yy)
                pdf.set_font(SANS, "", 8.2)
                pdf.set_text_color(*MUTED)
                pdf.multi_cell(text_w, 4.1, role["summary"], align="L")
                yy = pdf.get_y() + 0.6
            for point in role.get("points") or []:
                pdf.set_fill_color(*PINK_BRIGHT)
                pdf.rect(text_x + 0.4, yy + 1.5, 1.1, 1.1, "F")
                pdf.set_xy(text_x + 3.6, yy)
                pdf.set_font(SANS, "", 8.0)
                pdf.set_text_color(*MUTED)
                pdf.multi_cell(text_w - 3.6, 4.0, point, align="L")
                yy = pdf.get_y() + 0.7
            pdf.set_y(yy + 3.4)

    prev_roles = data.get("previous_roles") or []
    if prev_roles:
        pdf.set_x(MAIN_X)
        pdf.set_font(MONO, "", 7.2)
        pdf.set_text_color(*FAINT)
        pdf.cell(0, 4, "# previous_roles")
        pdf.ln(5)
        for pr in prev_roles:
            pdf.set_x(MAIN_X + 1)
            pdf.set_font(MONO, "", 6.8)
            pdf.set_text_color(*PINK)
            pdf.cell(20, 3.9, pr.get("date", ""))
            pdf.set_font(SANS, "", 7.8)
            pdf.set_text_color(*MUTED)
            pdf.cell(0, 3.9, pr.get("text", ""), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(0.6)
        pdf.ln(3)

    certs = data.get("certifications") or []
    if certs:
        _main_header(pdf, "certifications")
        for cert in certs:
            y = pdf.get_y()
            pdf.set_fill_color(*PINK_BRIGHT)
            pdf.rect(MAIN_X + 0.4, y + 1.6, 1.1, 1.1, "F")
            pdf.set_xy(MAIN_X + 4, y)
            pdf.set_font(SANS_SB, "", 8.4)
            pdf.set_text_color(*INK)
            pdf.cell(pdf.get_string_width(cert["name"]) + 2, 4.4, cert["name"])
            if cert.get("issuer"):
                pdf.set_font(SANS, "", 7.4)
                pdf.set_text_color(*FAINT)
                pdf.cell(0, 4.4, cert["issuer"])
            pdf.ln(5.4)


def _projects_pages(pdf: FPDF, projects) -> None:
    pdf.add_page()
    # header band
    pdf.set_fill_color(*SIDEBAR_BG)
    pdf.rect(0, 0, PAGE_W, 22, "F")
    pdf.set_fill_color(*PINK_BRIGHT)
    pdf.rect(0, 22, PAGE_W, 1.0, "F")
    pdf.set_xy(14, 6.5)
    pdf.set_font(MONO, "B", 13)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(pdf.get_string_width("featured_projects") + 2, 8, "featured_projects")
    pdf.set_font(MONO, "", 8)
    pdf.set_text_color(126, 207, 244)
    pdf.cell(0, 8, "= [")
    pdf.set_xy(PAGE_W - 90, 8)
    pdf.set_font(MONO, "", 6.6)
    pdf.set_text_color(*SIDE_MUTE)
    pdf.cell(76, 5, "live demos: gustavchristensen.dev/projects", align="R")
    pdf.set_y(30)

    margin_x = 14
    card_w = PAGE_W - 2 * margin_x
    pad = 5.5
    inner_w = card_w - 2 * pad - 2.5

    for project in projects:
        title = project.title
        raw_desc = project.description.split("<!--more-->", 1)[0]
        desc = _strip_html_block(raw_desc)
        if len(desc) > 330:
            desc = desc[:327].rstrip() + "…"
        techs = [str(t) for t in (project.technologies or [])]

        # measure description + chips to know the card height up front
        pdf.set_font(SANS, "", 8.2)
        desc_lines = pdf.multi_cell(inner_w, 4.1, desc, dry_run=True, output="LINES")
        pdf.set_font(MONO, "", 6.2)
        chip_rows, x = 1, 0.0
        for t in techs:
            w = pdf.get_string_width(t) + 4.6
            if x + w > inner_w and x > 0:
                chip_rows += 1
                x = 0.0
            x += w + 1.8
        n_links = int(bool(project.repo_url)) + int(bool(project.live_url))
        card_h = (pad + 5.6 + 1.6 + len(desc_lines) * 4.1 + 2.6
                  + chip_rows * 7.2 + (n_links * 3.9 + 1.2 if n_links else 0) + pad - 1)

        if pdf.get_y() + card_h > PAGE_H - 18:
            pdf.add_page()
            pdf.set_y(16)

        x0, y0 = margin_x, pdf.get_y()
        pdf.set_fill_color(*CARD_BG)
        pdf.set_draw_color(*CARD_BORDER)
        pdf.set_line_width(0.3)
        pdf.rect(x0, y0, card_w, card_h, "FD", round_corners=True, corner_radius=2.4)
        # pink accent bar on the left edge
        pdf.set_fill_color(*PINK_BRIGHT)
        pdf.rect(x0, y0 + 3, 1.1, card_h - 6, "F", round_corners=True, corner_radius=0.5)

        tx = x0 + pad + 2.5
        ty = y0 + pad
        pdf.set_xy(tx, ty)
        pdf.set_font(MONO_SB, "", 9.6)
        pdf.set_text_color(*INK)
        pdf.cell(inner_w, 5.6, title)
        ty += 5.6 + 1.6

        pdf.set_xy(tx, ty)
        pdf.set_font(SANS, "", 8.2)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(inner_w, 4.1, desc, align="L")
        ty = pdf.get_y() + 2.6

        ty = _chip_row(pdf, techs, tx, ty, inner_w, font_size=6.2, on_dark=False) + 2.4

        links = []
        if project.live_url:
            links.append(("live", str(project.live_url)))
        if project.repo_url:
            links.append(("code", str(project.repo_url)))
        for label, url in links:
            short = url.replace("https://", "").replace("http://", "").rstrip("/")
            pdf.set_xy(tx, ty)
            pdf.set_font(MONO, "", 7)
            pdf.set_text_color(*PINK)
            pdf.cell(pdf.get_string_width(label + ":") + 1.5, 3.9, f"{label}:")
            pdf.set_text_color(*BLUE)
            pdf.cell(0, 3.9, short, link=url)
            ty += 3.9

        pdf.set_y(y0 + card_h + 4.5)


def generate_cv_pdf(author: str, projects, data: dict) -> io.BytesIO:
    """Render the CV. `data` comes from extract_cv_data()."""
    pdf = _CVPDF(orientation="P", unit="mm", format="A4")
    fonts_ok = _register_fonts(pdf)
    pdf.fonts_ok = fonts_ok
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(MAIN_X, 15, 13)
    pdf.add_page()

    if not fonts_ok:
        # Unicode fonts missing — degrade to the basics rather than failing.
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(*INK)
        pdf.set_xy(14, 15)
        pdf.cell(0, 10, _latin1(author))
        pdf.set_font("Helvetica", "", 9)
        pdf.set_xy(14, 28)
        summary = _latin1(data.get("summary") or "")
        pdf.multi_cell(PAGE_W - 28, 4.6, summary)
    else:
        # The sidebar draws near the bottom edge (QR caption) — auto page
        # break would otherwise fire mid-sidebar and push the main column
        # onto page 2.
        pdf.set_auto_page_break(auto=False)
        _sidebar(pdf, data)
        pdf.set_auto_page_break(auto=True, margin=18)
        _main_column(pdf, author, data)
        if projects:
            pdf.set_margins(14, 15, 13)
            _projects_pages(pdf, projects)

    buffer = io.BytesIO()
    buffer.write(bytes(pdf.output()))
    buffer.seek(0)
    return buffer
