# Personlig Portfolio (FastAPI)

En simpel asynkron Python webapplikation bygget med FastAPI som viser din professionelle profil som Python udvikler.

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

## Theme
Aktuelt UI benytter **HTML5UP Phantom** tema (CC BY 3.0) med en lokal-first strategi:

1. Lokal trimmed CSS (`static/phantom/css/main.css`) der indeholder de centrale layout- og typografi‑regler for hurtig visning uden netværksafhængighed.
2. Lokal `noscript.css` der sikrer at siden ikke sidder fast i preload‑tilstand hvis JS er slået fra.
3. Eksterne (remote) assets i `<head>` for fuld oplevelse:
   - Google Fonts (Source Sans Pro)
   - Font Awesome (ikoner)
   - Phantom's originale JS (jquery, browser, breakpoints, util, main) hentes pt. fra HTML5UP’s demo-kilder.

Struktur (aktuel):
```
static/phantom/css/main.css        # Trimmet lokal version (ingen @import)
static/phantom/css/noscript.css    # Minimal fallback
static/phantom/LICENSE_html5up.txt # Licens + attribution krav
```

Attribution (krævet af CC BY 3.0): Footer indeholder link til HTML5UP. Fjern den ikke hvis du beholder temaet.

### Offline / Air‑gapped brug
Hvis du ønsker fuldt offline setup:
```
static/phantom/vendor/
  fonts/... (udtræk fra Font Awesome + evt. Google Font host selv)
  js/jquery.min.js
  js/browser.min.js
  js/breakpoints.min.js
  js/util.js
  js/main.js
```
Opdater derefter `templates/base.html` til at pege på de lokale filer. Husk at Google Fonts kræver lokal hosting af WOFF/WOFF2 hvis du vil undgå netværkskald.

### Skift tilbage til tidligere custom tema
I `base.html` kan du erstatte Phantom link tags med dine egne, fx:
```html
<link rel="stylesheet" href="/static/css/theme.css">
<link rel="stylesheet" href="/static/css/styles.css">
```
De ældre filer ligger stadig i `static/css/` (ubrugt pt.). Du kan også slette dem hvis de ikke skal bruges.

### Licenser
- Phantom: CC BY 3.0 (kræver tydelig kredit)
- Font Awesome (free subset): Se deres licens (SIL OFL / MIT / CC BY 4.0 kombination afhængig af del)
- Google Fonts: Open Font License (for Source Sans Pro)
- water.css (hvis genbrugt): MIT
- Øvrige egne filer: MIT (som angivet nedenfor) med mindre du ændrer det.

```

## Næste Mulige Trin
- SEO metadata og Open Graph tags
- Projekt data fra database (SQLite/PostgreSQL)
- Blog sektion med Markdown indlæg
- Kontaktformular med e-mail afsendelse
- CI workflow (GitHub Actions) til tests og linting
- Docker container

## Licens
MIT (eller hvad du foretrækker).
