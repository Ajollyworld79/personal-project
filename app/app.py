from typing import List
from datetime import datetime, timezone
import os
import sys
import re
import html as html_lib

# Ensure project root in path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from quart import Quart, render_template, jsonify, Response, request
import json
from app.config import get_settings
from app.models import Project, ProjectsResponse
from app.data import PROJECTS
import io
from fpdf import FPDF, XPos, YPos

settings = get_settings()

app = Quart(__name__, template_folder=os.path.join(PROJECT_ROOT, 'templates'), static_folder=os.path.join(PROJECT_ROOT, 'static'))

# Serve static files via Quart's builtin static folder (static/ already exists)
app.static_folder = os.path.join(PROJECT_ROOT, 'static')


def _html_to_plaintext(html: str) -> str:
    if not html:
        return ''
    # Replace common block-level tags with newlines
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</?(p|div|h[1-6]|section|article|li|ul|ol|header|footer|tr|td)[^>]*>", "\n", html)
    # Remove remaining tags
    text = re.sub(r"<[^>]+>", "", html)
    # Unescape HTML entities
    text = html_lib.unescape(text)
    # Normalize common unicode punctuation to ASCII equivalents
    text = text.replace('\u2014', '-').replace('\u2013', '-').replace('\u2015', '-')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\xa0', ' ')
    # Collapse multiple newlines and trim
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def _break_long_words(text: str, maxlen: int = 60) -> str:
    # Insert spaces into very long tokens so PDF can wrap them
    def repl(match):
        s = match.group(0)
        parts = [s[i:i+maxlen] for i in range(0, len(s), maxlen)]
        return ' '.join(parts)
    return re.sub(r"\S{%(n)d,}" % {'n': maxlen}, repl, text)


def generate_cv_pdf(author: str, projects: List[Project], about_html: str | None = None):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 10, f"{author}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 8, "CV - Python & AI / LLMs", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # If about_html provided, include it (rendered and cleaned)
    if about_html:
        text = _html_to_plaintext(about_html)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 8, "Profil", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)
        pdf.set_font('Helvetica', '', 11)
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                pdf.ln(3)
                continue
            line = _break_long_words(line, maxlen=70)
            # Limit line length for readability in PDF
            max_w = max(20, pdf.w - pdf.l_margin - pdf.r_margin)
            try:
                pdf.multi_cell(max_w, 6, line)
            except Exception:
                safe_line = line.encode('utf-8', errors='replace').decode('utf-8')
                pdf.multi_cell(max_w, 6, safe_line)
        pdf.ln(4)

    # Projects section
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 8, "Udvalgte Projekter", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font('Helvetica', '', 11)
    for p in projects:
        title = (p.title or '').replace('—', '-').replace('\u2014', '-')
        techs = ' | '.join(p.technologies or [])
        max_w = max(20, pdf.w - pdf.l_margin - pdf.r_margin)
        try:
            # Title on one line
            pdf.multi_cell(max_w, 6, title)
            # Techs on next line, indented
            if techs:
                pdf.cell(10, 6, "", new_x=XPos.LMARGIN, new_y=YPos.NEXT)  # indent
                pdf.multi_cell(max_w - 10, 5, f"Teknologier: {techs}")
        except Exception:
            safe_title = title.encode('utf-8', errors='replace').decode('utf-8')
            safe_techs = techs.encode('utf-8', errors='replace').decode('utf-8')
            pdf.multi_cell(max_w, 6, safe_title)
            if safe_techs:
                pdf.cell(10, 6, "", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.multi_cell(max_w - 10, 5, f"Teknologier: {safe_techs}")
        pdf.ln(2)

    buffer = io.BytesIO()
    raw = pdf.output()  # returns a bytearray
    buffer.write(bytes(raw))
    buffer.seek(0)
    return buffer


@app.route('/')
async def index():
    return await render_template('index.html', projects=PROJECTS, author=settings.author_name, current_year=datetime.now(timezone.utc).year)


@app.route('/om')
async def about():
    return await render_template('about.html', author=settings.author_name, current_year=datetime.utcnow().year)


@app.route('/api/projects')
async def api_projects():
    # Return JSON-serializable data using Pydantic model_dump_json
    return jsonify({'projects': [json.loads(p.model_dump_json()) for p in PROJECTS]})


@app.route('/download_cv')
async def download_cv():
    # Read the about template source and strip Jinja tags to avoid pulling full page CSS/JS
    tpl_path = os.path.join(PROJECT_ROOT, 'templates', 'about.html')
    try:
        with open(tpl_path, 'r', encoding='utf-8') as fh:
            raw_tpl = fh.read()
    except Exception:
        raw_tpl = ''
    # Remove Jinja control structures and variable tags
    cleaned = re.sub(r"\{[%#].*?[%#]\}", "", raw_tpl, flags=re.S)
    cleaned = re.sub(r"\{\{.*?\}\}", "", cleaned, flags=re.S)
    # Extract concise contact and section summaries to include in the PDF
    email_m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", cleaned)
    phone_m = re.search(r"\+?\d[\d\s\-()]{6,}\d", cleaned)
    linkedin_m = re.search(r"https?://[^\s'\"]*linkedin[^\s'\"]*", cleaned)
    # Top Skills
    skills_block = re.search(r"<h3>Top Skills</h3>.*?<ul>(.*?)</ul>", cleaned, flags=re.S)
    skills = []
    if skills_block:
        skills = re.findall(r"<li>(.*?)</li>", skills_block.group(1), flags=re.S)
        skills = [re.sub(r"<[^>]+>", "", s).strip() for s in skills]
    # Certifications
    cert_block = re.search(r"<h2>Certificeringer</h2>.*?<ul>(.*?)</ul>", cleaned, flags=re.S)
    certs = []
    if cert_block:
        certs = re.findall(r"<li>(.*?)</li>", cert_block.group(1), flags=re.S)
        certs = [re.sub(r"<[^>]+>", "", c).strip() for c in certs]
    # Languages
    lang_block = re.search(r"<h3>Sprog</h3>.*?<p>(.*?)</p>", cleaned, flags=re.S)
    langs = lang_block.group(1).strip() if lang_block else ''

    about_lines = []
    contact_line = []
    if phone_m:
        contact_line.append(phone_m.group(0).strip())
    if email_m:
        contact_line.append(email_m.group(0).strip())
    if linkedin_m:
        contact_line.append(linkedin_m.group(0).strip())
    if contact_line:
        about_lines.append('Kontakt: ' + ' • '.join(contact_line))
    if skills:
        about_lines.append('Top Skills: ' + ', '.join(skills))
    if langs:
        about_lines.append('Sprog: ' + langs)
    if certs:
        about_lines.append('Certificeringer: ' + '; '.join(certs))

    about_plain = '\n'.join(about_lines)

    packet = generate_cv_pdf(settings.author_name, PROJECTS, about_html=about_plain)
    data = packet.getvalue()
    filename = f"CV_{settings.author_name.replace(' ', '_')}.pdf"
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return Response(data, mimetype='application/pdf', headers=headers)


@app.route('/static/<path:filename>')
async def static_files(filename):
    return await app.send_static_file(filename)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.app:app', host='127.0.0.1', port=8000, reload=True)