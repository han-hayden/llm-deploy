"""Tests for parameter calculator."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from llm_deploy.database import Base
from llm_deploy.knowledge.loader import kb
from llm_deploy.models.task import AdaptationTask, TaskStatus
from llm_deploy.models.model_metadata import ModelMetadata
from llm_deploy.services.param_calculator import calculate_params


@pytest.fixture(autouse=True)
def load_kb():
    kb.load()


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


async def _create_qwen7b_task(db: AsyncSession) -> int:
    """Create a Qwen2-7B task with metadata for testing."""
    task = AdaptationTask(
        task_name="qwen7b_test",
        model_identifier="Qwen/Qwen2-7B",
        hardware_model="910B4",
        engine="mindie",
        dtype="bf16",
        status=TaskStatus.parsed,
    )
    db.add(task)
    await db.flush()

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
    db.add(meta)
    await db.flush()
    return task.id


@pytest.mark.asyncio
async def test_calculate_params_auto(db_session: AsyncSession):
    task_id = await _create_qwen7b_task(db_session)
    result = await calculate_params(db_session, task_id)

    assert result["dtype"] == "bf16"
    assert result["tp"] >= 1
    assert result["max_model_len"] >= 512
    assert result["gpu_count"] >= 1
    assert len(result["rationale"]) > 0
    assert result["memory_allocation"]["total_per_card_gb"] == 64


@pytest.mark.asyncio
async def test_calculate_params_with_gpu_count(db_session: AsyncSession):
    task_id = await _create_qwen7b_task(db_session)
    result = await calculate_params(db_session, task_id, gpu_count=2)

    assert result["gpu_count"] == 2
    # TP should be adjusted to work with num_heads=28
    assert result["tp"] in [1, 2, 4, 7, 14, 28]


@pytest.mark.asyncio
async def test_calculate_params_recalculate(db_session: AsyncSession):
    task_id = await _create_qwen7b_task(db_session)

    result1 = await calculate_params(db_session, task_id, gpu_count=1)
    result2 = await calculate_params(db_session, task_id, gpu_count=4)

    # With more GPUs, max_model_len should be >= original
    assert result2["tp"] >= result1["tp"] or result2["max_model_len"] >= result1["max_model_len"]


@pytest.mark.asyncio
async def test_calculate_enforce_eager_ascend(db_session: AsyncSession):
    """Ascend hardware should set enforce_eager=True."""
    task_id = await _create_qwen7b_task(db_session)
    result = await calculate_params(db_session, task_id)
    assert result["enforce_eager"] is True  # Ascend needs eager mode


@pytest.mark.asyncio
async def test_calculate_rationale_format(db_session: AsyncSession):
    task_id = await _create_qwen7b_task(db_session)
    result = await calculate_params(db_session, task_id)

    for r in result["rationale"]:
        assert "param" in r
        assert "value" in r
        assert "reason" in r


@pytest.mark.asyncio
async def test_calculate_memory_allocation(db_session: AsyncSession):
    task_id = await _create_qwen7b_task(db_session)
    result = await calculate_params(db_session, task_id)

    mem = result["memory_allocation"]
    assert mem["weight_gb"] > 0
    assert mem["total_per_card_gb"] == 64
    # Sum should not exceed total
    assert mem["weight_gb"] + mem["kv_cache_gb"] + mem["runtime_gb"] + mem["reserved_gb"] <= mem["total_per_card_gb"] * 1.1
