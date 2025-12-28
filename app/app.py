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
from mcp.client.sse import sse_client
from mcp import ClientSession

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


def _clean_text_for_pdf(text: str) -> str:
    """Remove special characters that can't be encoded in latin-1"""
    if not text:
        return text
    # Replace special characters
    replacements = {
        '\u2122': '',  # ™ trademark
        '\u00ae': '',  # ® registered
        '\u00a9': '',  # © copyright
        '\u2014': '-',  # em dash
        '\u2013': '-',  # en dash
        '\u2018': "'",  # left single quote
        '\u2019': "'",  # right single quote
        '\u201c': '"',  # left double quote
        '\u201d': '"',  # right double quote
        '\xa0': ' ',    # non-breaking space
        '&': 'and',     # ampersand
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining non-latin-1 characters
    try:
        text.encode('latin-1')
    except UnicodeEncodeError:
        text = text.encode('latin-1', errors='ignore').decode('latin-1')
    return text

def generate_cv_pdf(author: str, projects: List[Project], contact_info: dict | None = None, skills: list | None = None, 
                      languages: str | None = None, summary: str | None = None, certifications: list | None = None, 
                      experience: str | None = None, education: list | None = None):
    """Generate a professional CV PDF with clean formatting"""
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    
    # Clean all text inputs
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

    # Header
    pdf.set_fill_color(45, 55, 72)
    pdf.rect(0, 0, pdf.w, 35, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_y(10)
    pdf.cell(0, 8, author, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 6, "AI, LLM & Python Developer", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Add generation date in bottom right of header
    from datetime import datetime
    gen_date = datetime.now().strftime("%B %Y")
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(200, 200, 200)  # Light gray
    pdf.set_xy(pdf.w - 50, 28)  # Position in bottom right
    pdf.cell(40, 4, f"Generated: {gen_date}", align='R')
    
    pdf.set_text_color(50, 50, 50)
    pdf.ln(12)

    def add_section_header(title):
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(45, 55, 72)
        pdf.cell(0, 6, title.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_draw_color(180, 180, 180)
        pdf.set_line_width(0.3)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)

    # Get max width for multi_cell - use effective page width
    max_w = pdf.epw  # effective page width (excludes margins)

    # Contact
    if contact_info:
        add_section_header("Contact")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(60, 60, 60)
        
        label_width = 25  # Fixed width for all labels
        
        if contact_info.get('phone'):
            pdf.cell(label_width, 4, "Phone:", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.cell(0, 4, contact_info['phone'], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        if contact_info.get('email'):
            email = contact_info['email']
            pdf.cell(label_width, 4, "Email:", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_text_color(0, 0, 255)  # Blue for link
            pdf.cell(0, 4, email, new_x=XPos.LMARGIN, new_y=YPos.NEXT, link=f"mailto:{email}")
            pdf.set_text_color(60, 60, 60)  # Reset color
        
        if contact_info.get('linkedin'):
            linkedin_username = contact_info['linkedin']
            linkedin_url = f"https://www.linkedin.com/in/{linkedin_username}" if not linkedin_username.startswith('http') else linkedin_username
            pdf.cell(label_width, 4, "LinkedIn:", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_text_color(0, 0, 255)  # Blue for link
            pdf.cell(0, 4, linkedin_username, new_x=XPos.LMARGIN, new_y=YPos.NEXT, link=linkedin_url)
            pdf.set_text_color(60, 60, 60)  # Reset color
        
        pdf.ln(3)

    # Summary
    if summary:
        add_section_header("Professional Summary")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(max_w, 5, summary)
        pdf.ln(3)

    # Skills
    if skills:
        add_section_header("Core Skills")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 5, ", ".join(skills), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

    # Experience
    if experience:
        add_section_header("Professional Experience")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(50, 50, 50)
        
        # Parse experience into structured format
        exp_lines = experience.split('\n')
        for line in exp_lines:
            line = line.strip()
            if not line:
                continue
            # Check if it's a company/role line (contains dates or em dashes)
            if any(x in line for x in ['–', '-', '20', '(']):
                # Split into parts
                parts = line.split('–')
                if len(parts) >= 2:
                    pdf.set_font('Helvetica', 'B', 9)
                    pdf.set_text_color(45, 55, 72)
                    pdf.cell(0, 5, parts[0].strip(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    pdf.set_font('Helvetica', '', 8)
                    pdf.set_text_color(80, 80, 80)
                    pdf.multi_cell(max_w, 4, ' – '.join(parts[1:]).strip())
                else:
                    pdf.set_font('Helvetica', '', 9)
                    pdf.set_text_color(60, 60, 60)
                    pdf.multi_cell(max_w, 5, line)
            else:
                pdf.set_font('Helvetica', '', 8)
                pdf.set_text_color(70, 70, 70)
                pdf.multi_cell(max_w, 4, line)
            pdf.ln(1)
        pdf.ln(2)

    # Certifications
    if certifications:
        add_section_header("Certifications")
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(60, 60, 60)
        bullet_width = 5
        text_width = max_w - bullet_width
        for cert in certifications:
            x_start = pdf.get_x()
            # Simple dash bullet
            pdf.cell(bullet_width, 5, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
            # Text next to bullet
            pdf.multi_cell(text_width, 5, cert)
            # Reset x for next item
            pdf.set_x(x_start)
        pdf.ln(2)

    # Education
    if education:
        add_section_header("Education")
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(60, 60, 60)
        bullet_width = 5
        text_width = max_w - bullet_width
        for edu in education:
            x_start = pdf.get_x()
            pdf.cell(bullet_width, 5, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.multi_cell(text_width, 5, edu)
            pdf.set_x(x_start)
        pdf.ln(2)

    # Languages
    if languages:
        add_section_header("Languages")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(max_w, 5, languages)
        pdf.ln(3)

    # Projects section removed from PDF - available on website instead

    buffer = io.BytesIO()
    raw = pdf.output()
    buffer.write(bytes(raw))
    buffer.seek(0)
    return buffer


@app.route('/api/get-apology')
async def get_apology():
    """Fetch a live apology from the MCP server"""
    try:
        # Use a random context and style
        import random
        severity = random.choice(["TRIVIAL", "MINOR", "MAJOR", "CRITICAL", "NUCLEAR"])
        style = random.choice(["PROFESSIONAL", "CASUAL", "POETIC", "GROVELING", "HAIKU"])
        context = "the live demo button"
        
        # Connect to the MCP server
        async with sse_client("https://apology-as-a-service-production.up.railway.app/sse") as streams:
            async with ClientSession(streams.read, streams.write) as session:
                await session.initialize()
                
                # Call the tool
                result = await session.call_tool(
                    "generate_apology", 
                    arguments={
                        "severity": severity,
                        "style": style,
                        "context": context,
                        "recipient": "Visitor"
                    }
                )
                
                # Return the result text
                apology_text = result.content[0].text
                return jsonify({
                    "apology": apology_text,
                    "meta": f"Generated via MCP (Severity: {severity}, Style: {style})"
                })
                
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
async def index():
    return await render_template('index.html', projects=PROJECTS, author=settings.author_name, current_year=datetime.now(timezone.utc).year)


@app.route('/about')
async def about():
    return await render_template('about.html', author=settings.author_name, current_year=datetime.utcnow().year)


@app.route('/projects')
async def projects():
    return await render_template('projects.html', projects=PROJECTS, author=settings.author_name, current_year=datetime.now(timezone.utc).year)


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
        skills = [html_lib.unescape(s) for s in skills]
    # Languages
    lang_block = re.search(r"<h3>Languages</h3>.*?<p>(.*?)</p>", cleaned, flags=re.S)
    langs = lang_block.group(1).strip() if lang_block else ''
    langs = re.sub(r"<br\s*/?>|<BR\s*/?>|&nbsp;", " ", langs).strip()
    langs = html_lib.unescape(langs)
    # Certifications
    cert_block = re.search(r"<h2>Certifications</h2>.*?<ul>(.*?)</ul>", cleaned, flags=re.S)
    certs = []
    if cert_block:
        certs = re.findall(r"<li>(.*?)</li>", cert_block.group(1), flags=re.S)
        certs = [re.sub(r"<[^>]+>", "", c).strip() for c in certs]
        # Remove HTML entities and special characters
        certs = [re.sub(r"<br\s*/?>|<BR\s*/?>|&nbsp;", " ", c).strip() for c in certs]
        certs = [html_lib.unescape(c) for c in certs]
    # Summary (changed from Resume)
    summary_block = re.search(r"<h2>Summary</h2>.*?<p>(.*?)</p>", cleaned, flags=re.S)
    summary = summary_block.group(1).strip() if summary_block else ''
    summary = re.sub(r"<br\s*/?>|<BR\s*/?>|&nbsp;", " ", summary).strip()
    summary = html_lib.unescape(summary)
    # Experience
    exp_block = re.search(r"<h2>Experience</h2>(.*?)<div class=\"separator\"></div>", cleaned, flags=re.S)
    exp = exp_block.group(1).strip() if exp_block else ''
    exp = re.sub(r"<[^>]+>", "", exp).strip()
    exp = re.sub(r"<br\s*/?>|<BR\s*/?>|&nbsp;", " ", exp).strip()
    exp = html_lib.unescape(exp)
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
        contact_info['phone'] = phone_m.group(0).strip()
    if email_m:
        contact_info['email'] = email_m.group(0).strip()
    if linkedin_m:
        linkedin_url = linkedin_m.group(0).strip()
        if 'linkedin.com/in/' in linkedin_url:
            contact_info['linkedin'] = linkedin_url.split('linkedin.com/in/')[-1].rstrip('/')
        else:
            contact_info['linkedin'] = linkedin_url

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
        education=edus if edus else None
    )
    
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