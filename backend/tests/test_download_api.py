"""Tests for download API and background worker."""

import pytest
from httpx import AsyncClient, ASGITransport

from llm_deploy.main import create_app
from llm_deploy.knowledge.loader import kb
from llm_deploy.database import Base, engine
from llm_deploy.bg_tasks import submit_task, cancel_task, get_task_future, is_task_running


@pytest.fixture(autouse=True)
async def setup():
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
async def test_download_api_flow(app):
    """Test download API: create task, start download, check progress."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First create a task
        resp = await client.post("/api/v1/tasks", json={
            "model_identifier": "Qwen/Qwen2-7B",
            "hardware_model": "H100_80G",
        })
        assert resp.status_code == 200
        task_id = resp.json()["id"]

        # Start download
        resp = await client.post("/api/v1/models/download", json={
            "task_id": task_id,
            "source": "huggingface",
            "target_type": "local",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert data["status"] in ["pending", "downloading"]
        download_id = data["id"]

        # Check progress
        resp = await client.get(f"/api/v1/models/download/{download_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "progress_percent" in data


@pytest.mark.asyncio
async def test_download_by_task(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/tasks", json={
            "model_identifier": "test/model",
            "hardware_model": "A100_80G",
        })
        task_id = resp.json()["id"]

        await client.post("/api/v1/models/download", json={"task_id": task_id})

        resp = await client.get(f"/api/v1/models/download/task/{task_id}")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_download_not_found(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/models/download/99999")
        assert resp.status_code == 404


def test_worker_submit_and_status():
    """Test background worker task management."""
    import time

    def sample_task():
        time.sleep(0.1)
        return "done"

    future = submit_task("test-1", sample_task)
    assert future is not None

    f = get_task_future("test-1")
    assert f is not None

    result = f.result(timeout=5)
    assert result == "done"


def test_worker_cancel():
    import time

    def long_task():
        time.sleep(10)

    future = submit_task("test-cancel", long_task)
    # Note: cancel may not work if already started
    cancel_task("test-cancel")
