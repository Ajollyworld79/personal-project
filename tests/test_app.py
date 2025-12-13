import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from httpx import AsyncClient, ASGITransport
from app.app import app

@pytest.mark.asyncio
async def test_root_page():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/")
    assert resp.status_code == 200
    assert "Udvalgte Projekter" in resp.text

@pytest.mark.asyncio
async def test_projects_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert "projects" in data
    assert isinstance(data["projects"], list)
    assert len(data["projects"]) >= 1

@pytest.mark.asyncio
async def test_cv_download_and_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/download_cv")
        health = await ac.get('/healthz')
    assert resp.status_code == 200
    assert 'application/pdf' in resp.headers.get('content-type')
    assert health.status_code == 200
    assert health.json().get('status') == 'ok'
