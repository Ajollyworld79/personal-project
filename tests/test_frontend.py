import json
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
