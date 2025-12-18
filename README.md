# Personal Portfolio (Quart + Uvicorn)

A modern asynchronous Python web application built with Quart and Uvicorn.

## Features (first version)
- Home page with a short introduction
- "About me" page
- Simple JSON API listing projects
- HTML templates (Jinja2)
- Static CSS file
- Ready for expansion with a blog, contact form, database, etc.

## Requirements
Python 3.11+ is recommended.

## Installation
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run locally
1. Create and activate a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Run locally (development):
```bash
uvicorn app.app:app --reload
```

3. Or run directly (for development):
```bash
python app/app.py
```

Then open: http://127.0.0.1:8000

Alternative and more "package-correct" approach (avoids relative import issues):
```bash
python -m app.app
```
This ensures Python treats `app` as a package.

## Test
```bash
pytest -q
```

## Docker (Optional)
Build and run the container locally:
```bash
docker build -t gustav-portfolio .
docker run -p 8000:8000 gustav-portfolio
```

## Structure
```
app/
  app.py            # Quart instance and routes
  config.py         # Load settings from environment variables
  models.py         # Pydantic models
  data.py           # Temporary in-memory data source
static/
  css/styles.css
templates/
  base.html
  index.html
  about.html
```

## Theme
The current UI uses the **HTML5UP Phantom** theme (CC BY 3.0) with a local-first strategy:

1. Locally trimmed CSS (`static/phantom/css/main.css`) containing the core layout and typography rules for fast display without network dependency.
2. Local `noscript.css` to ensure the site doesn't remain stuck in preload state if JS is disabled.
3. External (remote) assets in `<head>` for full experience:
   - Google Fonts (Source Sans Pro)
   - Font Awesome (icons)
   - Phantom's original JS (jquery, browser, breakpoints, util, main) currently loaded from HTML5UP’s demo sources.

Attribution (required by CC BY 3.0): keep a footer link to HTML5UP if you keep the theme.

## Offline / Air‑gapped usage
If you want a fully offline setup:
```
static/phantom/vendor/
  fonts/... (extract from Font Awesome + local Google Font files)
  js/jquery.min.js
  js/browser.min.js
  js/breakpoints.min.js
  js/util.js
  js/main.js
```
Then update `templates/base.html` to point to the local files. Note that Google Fonts requires local hosting of WOFF/WOFF2 to avoid network calls.

## Switch back to an older custom theme
If you want to replace Phantom, swap CSS references in `templates/base.html` with your own files (e.g., a new `custom.css` in `static/`).

## Licenses
- Phantom: CC BY 3.0 (requires clear attribution)
- Font Awesome (free subset): check their license (SIL OFL / MIT / CC BY 4.0 combinations depending on parts used)
- Google Fonts: Open Font License (Source Sans Pro)
- water.css (if reused): MIT
- Other personal files: MIT (unless changed)


Copyright (c) 2025 Gustav Christensen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.