"""Deployment API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from llm_deploy.api.deps import get_db
from llm_deploy.schemas.deployment import (
    DeployRequest,
    PrecheckRequest,
    PrecheckResponse,
    PrecheckItem,
    VerifyRequest,
    DeploymentResponse,
)
from llm_deploy.services import deployer
from llm_deploy.services.env_prechecker import run_precheck
from llm_deploy.models.task import AdaptationTask
from llm_deploy.models.environment import Environment
from llm_deploy.models.image_build import ParamCalculation
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/deployments", tags=["Deployments"])


@router.post("", response_model=DeploymentResponse)
async def create_deployment(req: DeployRequest, db: AsyncSession = Depends(get_db)):
    """Deploy model to target environment."""
    try:
        dep = await deployer.deploy(db, req.task_id, req.environment_id, req.deploy_mode)
        return _build_response(dep)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/precheck", response_model=PrecheckResponse)
async def precheck(req: PrecheckRequest, db: AsyncSession = Depends(get_db)):
    """Run environment pre-deployment checks."""
    task_result = await db.execute(select(AdaptationTask).where(AdaptationTask.id == req.task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    env_result = await db.execute(select(Environment).where(Environment.id == req.environment_id))
    env = env_result.scalar_one_or_none()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    calc_result = await db.execute(select(ParamCalculation).where(ParamCalculation.task_id == req.task_id))
    calc = calc_result.scalar_one_or_none()

    result = await run_precheck(
        hardware_model=task.hardware_model,
        engine_name=task.engine,
        gpu_count_needed=calc.gpu_count if calc else 1,
        connection_config=env.connection_config or {},
        env_type=env.env_type,
    )

    return PrecheckResponse(
        passed=result["passed"],
        items=[PrecheckItem(**item) for item in result["items"]],
    )


@router.get("/{task_id}", response_model=DeploymentResponse)
async def get_deployment(task_id: int, db: AsyncSession = Depends(get_db)):
    dep = await deployer.get_deployment(db, task_id)
    if not dep:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return _build_response(dep)


@router.post("/verify")
async def verify_deployment(req: VerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify deployed service with test inference request."""
    try:
        result = await deployer.verify_service(db, req.task_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def _build_response(dep) -> DeploymentResponse:
    return DeploymentResponse(
        id=dep.id,
        task_id=dep.task_id,
        environment_id=dep.environment_id,
        deploy_mode=dep.deploy_mode,
        status=dep.status.value if hasattr(dep.status, 'value') else str(dep.status),
        precheck_report=dep.precheck_report,
        api_endpoint=dep.api_endpoint,
        deploy_config=dep.deploy_config,
        verification_result=dep.verification_result,
        container_id=dep.container_id,
    )
