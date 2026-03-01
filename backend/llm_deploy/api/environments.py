"""Environment management API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from llm_deploy.api.deps import get_db
from llm_deploy.schemas.environment import (
    EnvironmentCreateRequest,
    EnvironmentResponse,
    EnvironmentListResponse,
)
from llm_deploy.models.environment import Environment

router = APIRouter(prefix="/api/v1/environments", tags=["Environments"])


@router.post("", response_model=EnvironmentResponse)
async def create_environment(req: EnvironmentCreateRequest, db: AsyncSession = Depends(get_db)):
    env = Environment(
        name=req.name,
        env_type=req.env_type,
        connection_type=req.connection_type,
        connection_config=req.connection_config,
        hardware_info=req.hardware_info,
    )
    db.add(env)
    await db.flush()
    return EnvironmentResponse.model_validate(env)


@router.get("", response_model=EnvironmentListResponse)
async def list_environments(
    env_type: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Environment)
    count_query = select(func.count()).select_from(Environment)

    if env_type:
        query = query.where(Environment.env_type == env_type)
        count_query = count_query.where(Environment.env_type == env_type)
    if search:
        query = query.where(Environment.name.contains(search))
        count_query = count_query.where(Environment.name.contains(search))

    result = await db.execute(query.order_by(Environment.id.desc()))
    envs = list(result.scalars().all())
    total = (await db.execute(count_query)).scalar()

    return EnvironmentListResponse(
        items=[EnvironmentResponse.model_validate(e) for e in envs],
        total=total,
    )


@router.get("/{env_id}", response_model=EnvironmentResponse)
async def get_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Environment).where(Environment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return EnvironmentResponse.model_validate(env)


@router.put("/{env_id}", response_model=EnvironmentResponse)
async def update_environment(env_id: int, req: EnvironmentCreateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Environment).where(Environment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    env.name = req.name
    env.env_type = req.env_type
    env.connection_type = req.connection_type
    env.connection_config = req.connection_config
    env.hardware_info = req.hardware_info
    await db.flush()
    return EnvironmentResponse.model_validate(env)


@router.delete("/{env_id}")
async def delete_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Environment).where(Environment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    await db.delete(env)
    return {"message": "Environment deleted"}


@router.post("/{env_id}/test")
async def test_connection(env_id: int, db: AsyncSession = Depends(get_db)):
    """Test SSH connection to environment."""
    result = await db.execute(select(Environment).where(Environment.id == env_id))
    env = result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    from llm_deploy.adapters.ssh_executor import test_connection
    success, message = test_connection(env.connection_config or {})
    return {"success": success, "message": message}
