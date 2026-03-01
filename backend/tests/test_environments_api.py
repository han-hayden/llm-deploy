"""Tests for environment precheck, deployer, and environment API."""

import pytest
from httpx import AsyncClient, ASGITransport

from llm_deploy.main import create_app
from llm_deploy.knowledge.loader import kb
from llm_deploy.database import Base, engine
from llm_deploy.services.env_prechecker import run_precheck


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
async def test_precheck_nvidia():
    result = await run_precheck(
        hardware_model="H100_80G",
        engine_name="vllm",
        gpu_count_needed=4,
        connection_config={"host": "10.0.1.100"},
        env_type="docker",
    )
    assert result["passed"] is True
    assert len(result["items"]) >= 4


@pytest.mark.asyncio
async def test_precheck_ascend():
    result = await run_precheck(
        hardware_model="910B4",
        engine_name="mindie",
        gpu_count_needed=4,
        connection_config={"host": "10.0.1.100"},
        env_type="docker",
    )
    assert result["passed"] is True
    items_names = [i["name"] for i in result["items"]]
    assert "NPU 设备检测" in items_names
    assert "Ascend Runtime" in items_names


@pytest.mark.asyncio
async def test_environment_crud(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create
        resp = await client.post("/api/v1/environments", json={
            "name": "test-env-1",
            "env_type": "docker",
            "connection_type": "ssh",
            "connection_config": {"host": "10.0.1.100", "port": 22, "username": "root"},
            "hardware_info": {"gpu_count": 8, "gpu_model": "910B4"},
        })
        assert resp.status_code == 200
        env_id = resp.json()["id"]

        # List
        resp = await client.get("/api/v1/environments")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        # Get
        resp = await client.get(f"/api/v1/environments/{env_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "test-env-1"

        # Update
        resp = await client.put(f"/api/v1/environments/{env_id}", json={
            "name": "test-env-updated",
            "env_type": "docker",
            "connection_type": "ssh",
            "connection_config": {"host": "10.0.1.200"},
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "test-env-updated"

        # Delete
        resp = await client.delete(f"/api/v1/environments/{env_id}")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_hardware_compatibility(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/hardware/compatibility")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["vendors"]) >= 2
        assert len(data["all_chips"]) >= 5


@pytest.mark.asyncio
async def test_hardware_chip_detail(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/hardware/chips/H100_80G")
        assert resp.status_code == 200
        data = resp.json()
        assert data["model"] == "H100_80G"
        assert len(data["compatible_engines"]) >= 2


@pytest.mark.asyncio
async def test_deployment_flow(app):
    """Test full deployment flow: create task, env, deploy."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create task
        resp = await client.post("/api/v1/tasks", json={
            "model_identifier": "Qwen/Qwen2-7B",
            "hardware_model": "H100_80G",
        })
        task_id = resp.json()["id"]

        # Calculate params
        resp = await client.post("/api/v1/params/calculate", json={"task_id": task_id})
        assert resp.status_code == 200

        # Build image
        resp = await client.post("/api/v1/images/build", json={"task_id": task_id})
        assert resp.status_code == 200

        # Create environment
        resp = await client.post("/api/v1/environments", json={
            "name": "deploy-test-env",
            "env_type": "docker",
            "connection_type": "ssh",
            "connection_config": {"host": "10.0.1.100"},
        })
        env_id = resp.json()["id"]

        # Precheck
        resp = await client.post("/api/v1/deployments/precheck", json={
            "task_id": task_id,
            "environment_id": env_id,
        })
        assert resp.status_code == 200
        assert resp.json()["passed"] is True

        # Deploy
        resp = await client.post("/api/v1/deployments", json={
            "task_id": task_id,
            "environment_id": env_id,
            "deploy_mode": "docker",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ["running", "deploying", "verified"]
        assert data["api_endpoint"]

        # Verify
        resp = await client.post("/api/v1/deployments/verify", json={"task_id": task_id})
        assert resp.status_code == 200
