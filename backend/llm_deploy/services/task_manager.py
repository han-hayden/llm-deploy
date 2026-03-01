"""Task manager service — create tasks and manage status transitions."""

import logging
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from llm_deploy.models.task import AdaptationTask, TaskStatus
from llm_deploy.models.model_metadata import ModelMetadata
from llm_deploy.services import model_parser
from llm_deploy.services import hardware_matcher

logger = logging.getLogger(__name__)

# Valid status transitions
STATUS_TRANSITIONS: dict[TaskStatus, list[TaskStatus]] = {
    TaskStatus.created: [TaskStatus.parsing, TaskStatus.failed],
    TaskStatus.parsing: [TaskStatus.parsed, TaskStatus.failed],
    TaskStatus.parsed: [TaskStatus.downloading, TaskStatus.building, TaskStatus.failed],
    TaskStatus.downloading: [TaskStatus.downloaded, TaskStatus.download_failed],
    TaskStatus.downloaded: [TaskStatus.building, TaskStatus.failed],
    TaskStatus.download_failed: [TaskStatus.downloading, TaskStatus.failed],
    TaskStatus.building: [TaskStatus.built, TaskStatus.build_failed],
    TaskStatus.built: [TaskStatus.deploying, TaskStatus.failed],
    TaskStatus.build_failed: [TaskStatus.building, TaskStatus.failed],
    TaskStatus.deploying: [TaskStatus.deployed, TaskStatus.deploy_failed],
    TaskStatus.deployed: [TaskStatus.failed],
    TaskStatus.deploy_failed: [TaskStatus.deploying, TaskStatus.failed],
}


def _generate_task_name(model_identifier: str, hardware_model: str) -> str:
    """Auto-generate a task name from model and hardware."""
    model_short = model_identifier.split("/")[-1] if "/" in model_identifier else model_identifier
    date_str = datetime.now().strftime("%m%d")
    return f"{model_short}_{hardware_model}_{date_str}"


async def create_task(
    db: AsyncSession,
    model_identifier: str,
    hardware_model: str,
    task_name: str | None = None,
) -> AdaptationTask:
    """Create a new adaptation task and start model parsing."""
    if not task_name:
        task_name = _generate_task_name(model_identifier, hardware_model)

    # Check uniqueness
    existing = await db.execute(
        select(AdaptationTask).where(AdaptationTask.task_name == task_name)
    )
    if existing.scalar_one_or_none():
        # Append counter
        count = await db.execute(
            select(func.count()).select_from(AdaptationTask).where(
                AdaptationTask.task_name.like(f"{task_name}%")
            )
        )
        task_name = f"{task_name}_{count.scalar()}"

    task = AdaptationTask(
        task_name=task_name,
        model_identifier=model_identifier,
        hardware_model=hardware_model,
        status=TaskStatus.created,
    )
    db.add(task)
    await db.flush()

    # Parse model (async)
    task.status = TaskStatus.parsing
    try:
        parsed = await model_parser.parse_model(model_identifier)
        task.model_source = parsed["model_source"]

        # Save metadata
        meta = ModelMetadata(
            task_id=task.id,
            model_name=parsed["model_name"],
            architectures=",".join(parsed.get("architectures", [])),
            param_count=parsed.get("param_count", 0),
            hidden_size=parsed.get("hidden_size", 0),
            num_layers=parsed.get("num_layers", 0),
            num_heads=parsed.get("num_heads", 0),
            num_kv_heads=parsed.get("num_kv_heads", 0),
            vocab_size=parsed.get("vocab_size", 0),
            max_position_embeddings=parsed.get("max_position_embeddings", 0),
            torch_dtype=parsed.get("torch_dtype", ""),
            quantization_config=parsed.get("quantization_config"),
            model_card_parsed=parsed.get("model_card_info"),
            weight_files=parsed.get("weight_files"),
            weight_total_size=parsed.get("weight_total_size", 0),
            license=parsed.get("license", ""),
        )
        db.add(meta)

        # Match hardware
        chip = hardware_matcher.match_hardware(hardware_model)
        if chip:
            rec = hardware_matcher.recommend_engine(chip)
            task.engine = rec["engine"]
            task.dtype = rec["dtype"]

            anomalies = hardware_matcher.detect_anomalies(parsed, chip, rec)
            rec_anomalies = rec.get("anomaly_flags", [])
            all_anomalies = rec_anomalies + anomalies
            task.anomaly_flags = {"flags": all_anomalies} if all_anomalies else None
        else:
            task.anomaly_flags = {"flags": [{
                "type": "warning",
                "message": f"未在知识库中找到硬件型号: {hardware_model}，请确认型号或手动配置",
            }]}

        task.status = TaskStatus.parsed
    except Exception as e:
        logger.error("Model parsing failed: %s", e)
        task.status = TaskStatus.failed
        task.anomaly_flags = {"flags": [{"type": "error", "message": f"模型解析失败: {str(e)}"}]}

    return task


def transition_status(task: AdaptationTask, new_status: TaskStatus) -> bool:
    """Attempt to transition task to a new status. Returns True if valid."""
    allowed = STATUS_TRANSITIONS.get(task.status, [])
    if new_status in allowed:
        task.status = new_status
        return True
    logger.warning(
        "Invalid status transition: %s -> %s (allowed: %s)",
        task.status, new_status, allowed,
    )
    return False


async def get_task(db: AsyncSession, task_id: int) -> AdaptationTask | None:
    """Get a task by ID with all relationships loaded."""
    result = await db.execute(
        select(AdaptationTask).where(AdaptationTask.id == task_id)
    )
    return result.scalar_one_or_none()


async def list_tasks(
    db: AsyncSession,
    status: str | None = None,
    hardware: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[AdaptationTask], int]:
    """List tasks with optional filters."""
    query = select(AdaptationTask)
    count_query = select(func.count()).select_from(AdaptationTask)

    if status:
        query = query.where(AdaptationTask.status == status)
        count_query = count_query.where(AdaptationTask.status == status)
    if hardware:
        query = query.where(AdaptationTask.hardware_model == hardware)
        count_query = count_query.where(AdaptationTask.hardware_model == hardware)
    if search:
        query = query.where(AdaptationTask.task_name.contains(search))
        count_query = count_query.where(AdaptationTask.task_name.contains(search))

    query = query.order_by(AdaptationTask.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    tasks = list(result.scalars().all())
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return tasks, total
