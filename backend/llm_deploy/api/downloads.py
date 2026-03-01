"""Download API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from llm_deploy.api.deps import get_db
from llm_deploy.schemas.download import DownloadRequest, DownloadProgressResponse
from llm_deploy.services import download_manager

router = APIRouter(prefix="/api/v1/models", tags=["Downloads"])


@router.post("/download", response_model=DownloadProgressResponse)
async def start_download(req: DownloadRequest, db: AsyncSession = Depends(get_db)):
    """Start or resume a model weight download."""
    dl = await download_manager.start_download(
        db=db,
        task_id=req.task_id,
        source=req.source,
        target_type=req.target_type,
        target_env_id=req.target_env_id,
        storage_path=req.storage_path,
    )
    return _build_response(dl)


@router.get("/download/{download_id}", response_model=DownloadProgressResponse)
async def get_download_progress(download_id: int, db: AsyncSession = Depends(get_db)):
    """Get download progress by download ID."""
    dl = await download_manager.get_download_progress(db, download_id)
    if not dl:
        raise HTTPException(status_code=404, detail="Download not found")
    return _build_response(dl)


@router.get("/download/task/{task_id}", response_model=DownloadProgressResponse)
async def get_download_by_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get download progress by parent task ID."""
    dl = await download_manager.get_download_by_task(db, task_id)
    if not dl:
        raise HTTPException(status_code=404, detail="No download found for this task")
    return _build_response(dl)


@router.post("/download/{download_id}/cancel")
async def cancel_download(download_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel a running download."""
    success = await download_manager.cancel_download(db, download_id)
    return {"cancelled": success}


def _build_response(dl) -> DownloadProgressResponse:
    total = dl.total_size or 1
    progress = (dl.downloaded_size / total * 100) if total > 0 else 0
    return DownloadProgressResponse(
        id=dl.id,
        task_id=dl.task_id,
        source=dl.source,
        target_type=dl.target_type,
        storage_path=dl.storage_path,
        total_size=dl.total_size,
        downloaded_size=dl.downloaded_size,
        status=dl.status.value if hasattr(dl.status, 'value') else str(dl.status),
        speed=dl.speed,
        eta=dl.eta,
        error_message=dl.error_message,
        progress_percent=round(progress, 1),
    )
