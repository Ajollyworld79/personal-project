# Personlig Portfolio (FastAPI)

En simpel asynkron Python webapplikation bygget med FastAPI.

## Funktioner (første version)
- Forside med kort introduktion
- "Om mig" side
- Simpel JSON API med liste af projekter
- HTML templates (Jinja2)
- Statisk CSS fil
- Klar til udvidelse med blog, kontaktformular, database mv.

## Krav
Python 3.11+ anbefales.

## Installation
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Kør lokalt
Standard (anbefalet udvikling):
```bash
uvicorn app.app:app --reload
```

Eller direkte kørsel af filen (nu understøttet):
```bash
python app/app.py
```
Åbn herefter: http://127.0.0.1:8000

Alternativ og mere "pakke-korrekt" måde (undgår relative import problemer):
```bash
python -m app.app
```
Denne metode sikrer at Python forstår `app` som en pakke.

## Test
```bash
pytest -q
```

## Struktur
```
app/
  app.py            # FastAPI instans og routes
  config.py         # Indlæsning af settings fra miljøvariabler
  models.py         # Pydantic modeller
  data.py           # Midlertidig in-memory data kilde
static/
  css/styles.css
templates/
  base.html
  index.html
  about.html
```

## Næste Mulige Trin
- SEO metadata og Open Graph tags
- Projekt data fra database (SQLite/PostgreSQL)
- Blog sektion med Markdown indlæg
- Kontaktformular med e-mail afsendelse
- CI workflow (GitHub Actions) til tests og linting
- Docker container


