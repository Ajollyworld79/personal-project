import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from httpx import AsyncClient
from fastapi import status
from app.app import app

@pytest.mark.asyncio
async def test_root_page():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/")
    assert resp.status_code == status.HTTP_200_OK
    assert "Udvalgte Projekter" in resp.text

@pytest.mark.asyncio
async def test_projects_api():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/api/projects")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "projects" in data
    assert isinstance(data["projects"], list)
    assert len(data["projects"]) >= 1
