"""Image build API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from llm_deploy.api.deps import get_db
from llm_deploy.schemas.image import ImageBuildRequest, ImageBuildResponse
from llm_deploy.services import image_builder

router = APIRouter(prefix="/api/v1/images", tags=["Images"])


@router.post("/build", response_model=ImageBuildResponse)
async def build_image(req: ImageBuildRequest, db: AsyncSession = Depends(get_db)):
    """Start building a Docker image for the task."""
    try:
        build = await image_builder.build_image(db, req.task_id)
        return _build_response(build)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/build/{task_id}", response_model=ImageBuildResponse)
async def get_build_status(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get image build status."""
    build = await image_builder.get_build_status(db, task_id)
    if not build:
        raise HTTPException(status_code=404, detail="No build found for this task")
    return _build_response(build)


def _build_response(build) -> ImageBuildResponse:
    return ImageBuildResponse(
        id=build.id,
        task_id=build.task_id,
        engine_name=build.engine_name,
        engine_version=build.engine_version,
        base_image=build.base_image,
        image_tag=build.image_tag,
        dockerfile_content=build.dockerfile_content,
        startup_command=build.startup_command,
        api_wrapper_injected=build.api_wrapper_injected,
        status=build.status.value if hasattr(build.status, 'value') else str(build.status),
        build_log=build.build_log,
    )
