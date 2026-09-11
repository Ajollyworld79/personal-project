# Gustav Christensen — portfolio

React 19.3 + TypeScript 7.0.2 frontend, built with Vite 8.3. Quart serves the prerendered pages and the existing Python APIs. There is no Node server in production.

## Requirements

- Node.js 22.12+ (Node 24 LTS is used in Docker and CI)
- Python 3.11+ (Python 3.14 is used in Docker and CI)

## Install and run

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm ci
npm run build
python run.py
```

Open http://127.0.0.1:8000. The build checks types with the native TypeScript 7 compiler, builds the client and prerender renderer, and generates HTML for all three pages.

Rebuild after editing frontend code or public content. The export includes only selected public fields, never settings, API keys or environment variables.

### Hot reload

Run two terminals from the project root:

```sh
# Terminal 1
npm run dev

# Terminal 2 (virtualenv activated)
VITE_DEV_SERVER=http://127.0.0.1:5173 python -m uvicorn app.app:app --reload
```

Visit http://127.0.0.1:8000, not the Vite URL. API calls remain on the same origin. Development uses client rendering; production prerenders content and hydrates it with React. Do not set VITE_DEV_SERVER in production.

## Content and architecture

| Location | Responsibility |
| --- | --- |
| frontend/pages/ | Home, about and projects |
| frontend/components/ | Streaming chat, dialogs, video, projects and live data |
| frontend/types.ts | TypeScript types and runtime API validation with Zod |
| static/assets/css/site.css, portfolio.css | Original production stylesheets, retained for visual fidelity |
| frontend/styles.css | Interaction adapters, video dialog and keyboard support |
| frontend/original-navigation.css, original-projects.css | Original template styles; project rules retain their page-only scope and specificity |
| content/cv.json | Shared source for the about page and PDF CV |
| app/data.py | Ordered project descriptions, technologies and links |
| app/frontend.py | Vite manifest, prerendered HTML and matching bootstrap data |
| app/app.py | Existing APIs, service checks, YouTube RSS and GitHub activity |
| app/pdf_cv.py | PDF renderer using structured CV content |
| scripts/ | Content export and React prerender build |
| static/fonts/ | Font assets for the PDF; the website uses the original Google Fonts weights |

Project descriptions contain **trusted, repository-authored HTML**. Do not pass user-generated or external HTML into these fields without adding sanitization. Chat markdown is rendered separately with raw HTML disabled.

Normal document navigation preserves direct URLs, fragment links, browser history and no-JavaScript reading. Video and diagram dialogs use native dialog elements; closing a video removes the iframe. Markdown code loads only when the assistant displays an answer.

## Validation

```sh
npm run typecheck
npm run build
python -m pytest -q
npx playwright install chromium
npm test
```

On a Mac with Chrome installed, use PLAYWRIGHT_CHANNEL=chrome npm test. Browser tests start a server on port 8010 and mock external APIs/YouTube. They cover four screen widths, hydration, no-JavaScript content, dialogs, streaming chat, rate limits, safe markdown, the actual GitHub calendar response format and offline states. Backend tests cover routes, assets, PDF generation and the opt-in public GitHub preview. Screenshots and failed traces are written to ignored test-results/.

For a local preview without a GitHub token, start the server with:

```bash
GITHUB_ACTIVITY_PREVIEW=1 python -m uvicorn app.app:app --host 127.0.0.1 --port 8000
```

This opt-in setting reads the already-public calendar from gustavchristensen.dev and caches it for an hour. It sends no credentials. Keep it unset in production, which uses GITHUB_TOKEN. If calendar data is unavailable, the page shows a message and a GitHub profile link instead of silently hiding the section.

## Production

```sh
docker build -t gustav-portfolio .
docker run --rm -p 8000:8000 gustav-portfolio
```

Docker exports public content in a Python stage, builds React in a Node stage, and copies the built assets into the Python runtime. PORT is respected by run.py. Existing API environment variables remain supported: LLM_ASSISTANT_URL, LLM_ASSISTANT_API_KEY, CV_CHAT_RATE_LIMIT, CV_CHAT_RATE_WINDOW_SECONDS, COLDFILE_CHANNEL_ID, and GITHUB_TOKEN. Supply secrets only to the Python runtime.

Generated assets are ignored by Git and rebuilt in Docker/CI. A local build does not deploy the site.

## Design

This is a framework migration with the production design as its visual contract. React replaces the Jinja page markup and imperative browser scripts; original CSS, font weights, classes, content order and dimensions are retained. Do not redesign or simplify sections as part of a framework change. See DESIGN-REVIEW.md for comparison evidence and the explicitly retained video-dialog improvement.

## License

Copyright (c) 2025–2026 Gustav Christensen

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Existing image and font assets retain their original licenses.
