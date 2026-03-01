"""Download manager service."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from llm_deploy.models.download import DownloadTask, DownloadStatus
from llm_deploy.models.task import AdaptationTask
from llm_deploy.models.model_metadata import ModelMetadata
from llm_deploy.bg_tasks import submit_task
from llm_deploy.bg_tasks.tasks import run_download
from llm_deploy.config import settings

logger = logging.getLogger(__name__)


async def start_download(
    db: AsyncSession,
    task_id: int,
    source: str = "huggingface",
    target_type: str = "local",
    target_env_id: int | None = None,
    storage_path: str = "",
) -> DownloadTask:
    """Create or resume a download task and start background execution."""
    # Get task and metadata
    result = await db.execute(
        select(AdaptationTask).where(AdaptationTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise ValueError(f"Task {task_id} not found")

    # Get metadata for weight size info
    meta_result = await db.execute(
        select(ModelMetadata).where(ModelMetadata.task_id == task_id)
    )
    meta = meta_result.scalar_one_or_none()

    # Auto-generate storage path
    if not storage_path:
        model_name = task.model_identifier.split("/")[-1] if "/" in task.model_identifier else task.model_identifier
        storage_path = f"{settings.MODELS_CACHE_DIR}/{source}/{model_name}"

    # Check for existing download
    dl_result = await db.execute(
        select(DownloadTask).where(DownloadTask.task_id == task_id)
    )
    dl = dl_result.scalar_one_or_none()

    if dl and dl.status == DownloadStatus.completed:
        return dl

    if dl is None:
        dl = DownloadTask(
            task_id=task_id,
            source=source,
            target_type=target_type,
            target_env_id=target_env_id,
            storage_path=storage_path,
            total_size=meta.weight_total_size if meta else 0,
            status=DownloadStatus.pending,
        )
        db.add(dl)
        await db.flush()
    else:
        # Resume: keep downloaded_size for resume
        dl.status = DownloadStatus.pending
        dl.error_message = ""

    await db.commit()

    # Submit to background worker
    submit_task(f"download-{dl.id}", run_download, dl.id)

    return dl


async def get_download_progress(db: AsyncSession, download_id: int) -> DownloadTask | None:
    """Get current download progress."""
    result = await db.execute(
        select(DownloadTask).where(DownloadTask.id == download_id)
    )
    return result.scalar_one_or_none()


async def get_download_by_task(db: AsyncSession, task_id: int) -> DownloadTask | None:
    """Get download task by parent task ID."""
    result = await db.execute(
        select(DownloadTask).where(DownloadTask.task_id == task_id)
    )
    return result.scalar_one_or_none()


async def cancel_download(db: AsyncSession, download_id: int) -> bool:
    """Cancel a running download."""
    from llm_deploy.bg_tasks import cancel_task
    result = await db.execute(
        select(DownloadTask).where(DownloadTask.id == download_id)
    )
    dl = result.scalar_one_or_none()
    if not dl:
        return False

    cancelled = cancel_task(f"download-{dl.id}")
    dl.status = DownloadStatus.paused
    await db.commit()
    return cancelled
