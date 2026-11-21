import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest
from app.app import app
from app.frontend import cv_content

ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.asyncio
async def test_opt_in_github_preview_uses_public_calendar(monkeypatch, http):
    data = {'username': 'Ajollyworld79', 'total': 871, 'weeks': [{'contributionDays': [
        {'date': '2026-09-10', 'contributionCount': 3, 'weekday': 4}]}]}
    url = 'https://gustavchristensen.dev/api/github-activity'
    http.respond(url, json=data)
    monkeypatch.delenv('GITHUB_TOKEN', raising=False)
    monkeypatch.setenv('GITHUB_ACTIVITY_PREVIEW', '1')
    response = await app.test_client().get('/api/github-activity')
    assert response.status_code == 200
    assert await response.get_json() == data
    await app.test_client().get('/api/github-activity')
    assert [(method, called) for method, called, _ in http.calls] == [('GET', url)]
    assert 'headers' not in http.calls[0][2]

@pytest.mark.asyncio
@pytest.mark.parametrize('path,title', [('/', 'Production AI Engineer'), ('/about', 'About Gustav'), ('/projects', 'Production AI Projects')])
async def test_prerendered_routes(path, title):
    response = await app.test_client().get(path)
    html = await response.get_data(as_text=True)
    assert response.status_code == 200
    assert title in html
    assert 'data-prerendered="true"' in html
    assert '<h1' in html
    assert '/static/dist/assets/' in html
    assert 'assets/js/portfolio.js' not in html

@pytest.mark.asyncio
async def test_cv_download_and_shared_source():
    content = json.loads((ROOT / 'static/dist/prerender/content.json').read_text())
    assert content['cv'] == cv_content()
    assert len(content['cv']['skills']) == 5
    assert len(content['cv']['languages']) == 2
    assert len(content['cv']['roles']) == 3
    response = await app.test_client().get('/download_cv')
    assert response.status_code == 200
    assert response.content_type == 'application/pdf'
    assert (await response.get_data()).startswith(b'%PDF')
    assert 'attachment' in response.headers['Content-Disposition']

@pytest.mark.asyncio
async def test_built_assets_are_served():
    manifest = json.loads((ROOT / 'static/dist/.vite/manifest.json').read_text())
    entry = manifest['frontend/main.tsx']
    for asset in [entry['file'], *entry['css']]:
        response = await app.test_client().get('/static/dist/' + asset)
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_dev_urls_include_vite_base(monkeypatch):
    monkeypatch.setenv('VITE_DEV_SERVER', 'http://127.0.0.1:5173')
    response = await app.test_client().get('/')
    html = await response.get_data(as_text=True)
    assert 'http://127.0.0.1:5173/static/dist/frontend/main.tsx' in html
    assert 'http://127.0.0.1:5173/static/dist/@react-refresh' in html
    assert 'data-prerendered="false"' in html

BASE = 'https://gustavchristensen.dev'
PAGES = [('/', BASE + '/'), ('/about', BASE + '/about'), ('/projects', BASE + '/projects')]

@pytest.mark.asyncio
async def test_robots_txt_names_sitemap():
    response = await app.test_client().get('/robots.txt')
    assert response.status_code == 200
    assert response.content_type.startswith('text/plain')
    body = await response.get_data(as_text=True)
    assert 'Allow: /' in body
    assert f'Sitemap: {BASE}/sitemap.xml' in body

@pytest.mark.asyncio
async def test_sitemap_lists_canonical_pages():
    response = await app.test_client().get('/sitemap.xml')
    assert response.status_code == 200
    assert 'xml' in response.content_type
    root = ET.fromstring(await response.get_data(as_text=True))
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    assert [loc.text for loc in root.findall('s:url/s:loc', ns)] == [url for _, url in PAGES]

@pytest.mark.asyncio
@pytest.mark.parametrize('path,url', PAGES)
async def test_page_canonical_and_person_json_ld(path, url):
    html = await (await app.test_client().get(path)).get_data(as_text=True)
    assert f'<link rel="canonical" href="{url}">' in html
    assert f'<meta property="og:url" content="{url}">' in html
    block = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    data = json.loads(block.group(1))
    assert data['@type'] == 'Person'
    assert data['url'] == BASE
    assert data['jobTitle'] == 'Production AI Engineer'
    assert data['sameAs'] == [
        'https://www.linkedin.com/in/gustav-wind-christensen-b61a0330',
        'https://github.com/Ajollyworld79',
    ]
    assert data['knowsAbout'] == cv_content()['skills']
