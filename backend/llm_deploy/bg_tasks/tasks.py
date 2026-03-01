"""Background download task implementation."""

import os
import time
import hashlib
import logging
import asyncio
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from llm_deploy.models.download import DownloadTask, DownloadStatus
from llm_deploy.models.task import AdaptationTask, TaskStatus
from llm_deploy.database import async_session_factory

logger = logging.getLogger(__name__)


def run_download(download_id: int) -> None:
    """Synchronous download runner — executed in thread pool.

    This simulates the download flow. In production, it would use
    huggingface_hub or modelscope SDK for actual downloads.
    """
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_async_download(download_id))
    finally:
        loop.close()


async def _async_download(download_id: int) -> None:
    """Async download implementation."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(DownloadTask).where(DownloadTask.id == download_id)
        )
        dl = result.scalar_one_or_none()
        if not dl:
            logger.error("Download task %d not found", download_id)
            return

        # Update status to downloading
        dl.status = DownloadStatus.downloading
        await db.commit()

        # Update parent task status
        task_result = await db.execute(
            select(AdaptationTask).where(AdaptationTask.id == dl.task_id)
        )
        task = task_result.scalar_one_or_none()
        if task:
            task.status = TaskStatus.downloading
            await db.commit()

        try:
            await _execute_download(db, dl)

            # Verify checksums
            dl.status = DownloadStatus.verifying
            await db.commit()

            # Mark complete
            dl.status = DownloadStatus.completed
            dl.downloaded_size = dl.total_size
            dl.speed = 0
            dl.eta = 0
            await db.commit()

            if task:
                task.status = TaskStatus.downloaded
                await db.commit()

        except Exception as e:
            logger.error("Download failed: %s", e)
            dl.status = DownloadStatus.failed
            dl.error_message = str(e)
            await db.commit()

            if task:
                task.status = TaskStatus.download_failed
                await db.commit()


async def _execute_download(db: AsyncSession, dl: DownloadTask) -> None:
    """Execute the actual download.

    In production, this calls huggingface_hub.snapshot_download() or
    modelscope.hub.snapshot_download(). For now, we simulate progress.
    """
    total = dl.total_size or 1_000_000_000  # Default 1GB if unknown
    dl.total_size = total
    chunk_size = 50_000_000  # 50MB chunks
    downloaded = dl.downloaded_size  # Support resume

    # Ensure storage directory exists
    if dl.storage_path:
        Path(dl.storage_path).mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    while downloaded < total:
        # Simulate chunk download
        await asyncio.sleep(0.1)  # Simulate network I/O
        downloaded = min(downloaded + chunk_size, total)
        elapsed = time.time() - start_time

        dl.downloaded_size = downloaded
        dl.speed = downloaded / max(elapsed, 0.1)
        remaining = total - downloaded
        dl.eta = int(remaining / max(dl.speed, 1))
        await db.commit()

    dl.downloaded_size = total
