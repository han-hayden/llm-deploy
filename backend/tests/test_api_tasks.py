"""Tests for task API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport

from llm_deploy.main import create_app
from llm_deploy.knowledge.loader import kb
from llm_deploy.database import Base, engine


@pytest.fixture(autouse=True)
async def setup():
    """Set up: load KB and create tables."""
    kb.load()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_health_check(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_task(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/tasks", json={
            "model_identifier": "Qwen/Qwen2-7B",
            "hardware_model": "910B4",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["model_identifier"] == "Qwen/Qwen2-7B"
        assert data["hardware_model"] == "910B4"
        assert data["status"] in ["parsed", "created", "parsing", "failed"]
        assert data["task_name"]


@pytest.mark.asyncio
async def test_create_task_with_custom_name(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/tasks", json={
            "model_identifier": "Qwen/Qwen2-7B",
            "hardware_model": "H100_80G",
            "task_name": "my-custom-task",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "my-custom-task" in data["task_name"]


@pytest.mark.asyncio
async def test_list_tasks(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_task_not_found(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/tasks/99999")
        assert resp.status_code == 404
