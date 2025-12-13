from typing import List
from datetime import datetime, timezone
import os
import sys

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

app = Quart(__name__, template_folder=os.path.join(PROJECT_ROOT, 'templates'))

# Serve static files via Quart's builtin static folder (static/ already exists)
app.static_folder = 'static'


def generate_cv_pdf(author: str, projects: List[Project]):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 10, f"{author}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('Helvetica', '', 12)
    # Avoid Unicode-only characters in the core font to keep PDF generation simple
    pdf.cell(0, 8, "CV - Python & AI / LLMs", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 8, "Udvalgte Projekter", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font('Helvetica', '', 11)
    for p in projects:
        title = (p.title or '').replace('—', '-').replace('\u2014', '-')
        techs = ' | '.join(p.technologies or [])
        pdf.multi_cell(0, 6, f"- {title} - {techs}")
        pdf.ln(1)
    buffer = io.BytesIO()
    # Get the generated PDF bytes and write them into a BytesIO buffer.
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
    # Generate a small PDF CV on the fly
    packet = generate_cv_pdf(settings.author_name, PROJECTS)
    data = packet.getvalue()
    filename = f"CV_{settings.author_name.replace(' ', '_')}.pdf"
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return Response(data, mimetype='application/pdf', headers=headers)


@app.route('/healthz')
async def healthz():
    return jsonify({'status': 'ok', 'version': settings.version})


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.app:app', host='127.0.0.1', port=8000, reload=True)