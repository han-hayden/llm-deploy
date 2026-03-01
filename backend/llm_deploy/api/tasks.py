"""Task API routes — CRUD for adaptation tasks."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from llm_deploy.api.deps import get_db
from llm_deploy.schemas.task import (
    TaskCreateRequest,
    TaskResponse,
    TaskListResponse,
    ModelMetadataResponse,
    HardwareInfoResponse,
    RecommendedPlanResponse,
)
from llm_deploy.services import task_manager
from llm_deploy.services import hardware_matcher
from llm_deploy.models.task import AdaptationTask
from llm_deploy.models.model_metadata import ModelMetadata
from llm_deploy.knowledge.loader import kb

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse)
async def create_task(req: TaskCreateRequest, db: AsyncSession = Depends(get_db)):
    """Create a new adaptation task. Triggers model parsing and hardware matching."""
    task = await task_manager.create_task(
        db=db,
        model_identifier=req.model_identifier,
        hardware_model=req.hardware_model,
        task_name=req.task_name,
    )
    return _build_task_response(task)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: str | None = Query(None),
    hardware: str | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List all tasks with optional filters."""
    tasks, total = await task_manager.list_tasks(db, status, hardware, search, skip, limit)
    return TaskListResponse(
        items=[_build_task_response(t) for t in tasks],
        total=total,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get task details including metadata and hardware info."""
    result = await db.execute(
        select(AdaptationTask)
        .options(selectinload(AdaptationTask.metadata_info))
        .where(AdaptationTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    response = _build_task_response(task)

    # Add metadata
    if task.metadata_info:
        response.metadata_info = ModelMetadataResponse.model_validate(task.metadata_info)

    # Add hardware info from knowledge base
    chip = hardware_matcher.match_hardware(task.hardware_model)
    if chip:
        response.hardware_info = HardwareInfoResponse(**hardware_matcher.get_hardware_display_info(chip))
        rec = hardware_matcher.recommend_engine(chip)
        response.recommended_plan = RecommendedPlanResponse(**rec)

    return response


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an adaptation task."""
    task = await task_manager.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    return {"message": "Task deleted"}


def _build_task_response(task: AdaptationTask) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        task_name=task.task_name,
        model_identifier=task.model_identifier,
        model_source=task.model_source,
        hardware_model=task.hardware_model,
        engine=task.engine,
        dtype=task.dtype,
        status=task.status.value if hasattr(task.status, 'value') else str(task.status),
        anomaly_flags=task.anomaly_flags,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )
