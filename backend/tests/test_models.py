"""Tests for ORM models — basic CRUD operations."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from llm_deploy.database import Base
from llm_deploy.models.task import AdaptationTask, TaskStatus
from llm_deploy.models.model_metadata import ModelMetadata
from llm_deploy.models.download import DownloadTask, DownloadStatus
from llm_deploy.models.image_build import ImageBuildTask, ParamCalculation
from llm_deploy.models.deployment import Deployment, DeployStatus
from llm_deploy.models.environment import Environment


@pytest.fixture
async def db_session():
    """Create an in-memory SQLite database and yield a session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_adaptation_task(db_session: AsyncSession):
    task = AdaptationTask(
        task_name="Qwen2-7B_910B4_0301",
        model_identifier="Qwen/Qwen2-7B",
        model_source="huggingface",
        hardware_model="910B4",
        status=TaskStatus.created,
    )
    db_session.add(task)
    await db_session.commit()

    result = await db_session.execute(
        select(AdaptationTask).where(AdaptationTask.task_name == "Qwen2-7B_910B4_0301")
    )
    fetched = result.scalar_one()
    assert fetched.model_identifier == "Qwen/Qwen2-7B"
    assert fetched.status == TaskStatus.created
    assert fetched.hardware_model == "910B4"


@pytest.mark.asyncio
async def test_task_with_metadata(db_session: AsyncSession):
    task = AdaptationTask(
        task_name="test_meta",
        model_identifier="Qwen/Qwen2-7B",
        hardware_model="A100_80G",
    )
    db_session.add(task)
    await db_session.flush()

    meta = ModelMetadata(
        task_id=task.id,
        model_name="Qwen2-7B",
        architectures="Qwen2ForCausalLM",
        param_count=7_000_000_000,
        hidden_size=3584,
        num_layers=28,
        num_heads=28,
        num_kv_heads=4,
        vocab_size=151936,
        max_position_embeddings=131072,
        torch_dtype="bfloat16",
    )
    db_session.add(meta)
    await db_session.commit()

    result = await db_session.execute(
        select(ModelMetadata).where(ModelMetadata.task_id == task.id)
    )
    fetched = result.scalar_one()
    assert fetched.param_count == 7_000_000_000
    assert fetched.architectures == "Qwen2ForCausalLM"


@pytest.mark.asyncio
async def test_create_download_task(db_session: AsyncSession):
    task = AdaptationTask(task_name="dl_test", model_identifier="test", hardware_model="H100_80G")
    db_session.add(task)
    await db_session.flush()

    dl = DownloadTask(
        task_id=task.id,
        source="huggingface",
        target_type="local",
        storage_path="/data/models/test",
        total_size=10_000_000_000,
        status=DownloadStatus.pending,
    )
    db_session.add(dl)
    await db_session.commit()

    result = await db_session.execute(select(DownloadTask).where(DownloadTask.task_id == task.id))
    fetched = result.scalar_one()
    assert fetched.total_size == 10_000_000_000
    assert fetched.status == DownloadStatus.pending


@pytest.mark.asyncio
async def test_create_environment(db_session: AsyncSession):
    env = Environment(
        name="prod-ascend-01",
        env_type="docker",
        connection_type="ssh",
        connection_config={"host": "10.0.1.100", "port": 22, "username": "root"},
        hardware_info={"gpu_count": 8, "gpu_model": "910B4", "gpu_memory_gb": 64},
    )
    db_session.add(env)
    await db_session.commit()

    result = await db_session.execute(
        select(Environment).where(Environment.name == "prod-ascend-01")
    )
    fetched = result.scalar_one()
    assert fetched.env_type == "docker"
    assert fetched.hardware_info["gpu_count"] == 8


@pytest.mark.asyncio
async def test_param_calculation(db_session: AsyncSession):
    task = AdaptationTask(task_name="param_test", model_identifier="test", hardware_model="910B4")
    db_session.add(task)
    await db_session.flush()

    calc = ParamCalculation(
        task_id=task.id,
        gpu_count=4,
        dtype="bf16",
        tp=4,
        pp=1,
        max_model_len=32768,
        max_num_seqs=32,
        gpu_mem_util=0.9,
        rationale={"tp": "144GB / 64GB = 2.25, 对齐到4 (num_heads=28 可整除)"},
        memory_allocation={"weight": 36, "kv_cache": 21.6, "runtime": 3.2, "reserved": 3.2},
    )
    db_session.add(calc)
    await db_session.commit()

    result = await db_session.execute(select(ParamCalculation).where(ParamCalculation.task_id == task.id))
    fetched = result.scalar_one()
    assert fetched.tp == 4
    assert fetched.rationale is not None


@pytest.mark.asyncio
async def test_deployment_with_environment(db_session: AsyncSession):
    env = Environment(
        name="test-env", env_type="docker", connection_type="ssh",
        connection_config={"host": "10.0.1.100"},
    )
    task = AdaptationTask(task_name="deploy_test", model_identifier="test", hardware_model="910B4")
    db_session.add_all([env, task])
    await db_session.flush()

    dep = Deployment(
        task_id=task.id,
        environment_id=env.id,
        deploy_mode="docker",
        status=DeployStatus.pending,
    )
    db_session.add(dep)
    await db_session.commit()

    result = await db_session.execute(select(Deployment).where(Deployment.task_id == task.id))
    fetched = result.scalar_one()
    assert fetched.deploy_mode == "docker"
    assert fetched.environment_id == env.id
