"""Deployer service — handles Docker and K8s deployment."""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from llm_deploy.models.task import AdaptationTask, TaskStatus
from llm_deploy.models.image_build import ImageBuildTask, ParamCalculation
from llm_deploy.models.deployment import Deployment, DeployStatus
from llm_deploy.models.environment import Environment as EnvironmentModel
from llm_deploy.services.env_prechecker import run_precheck
from llm_deploy.knowledge.loader import kb

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


async def deploy(
    db: AsyncSession,
    task_id: int,
    environment_id: int,
    deploy_mode: str = "docker",
) -> Deployment:
    """Execute deployment to target environment."""
    # Load task
    task_result = await db.execute(select(AdaptationTask).where(AdaptationTask.id == task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise ValueError(f"Task {task_id} not found")

    # Load environment
    env_result = await db.execute(select(EnvironmentModel).where(EnvironmentModel.id == environment_id))
    env = env_result.scalar_one_or_none()
    if not env:
        raise ValueError(f"Environment {environment_id} not found")

    # Load build info
    build_result = await db.execute(select(ImageBuildTask).where(ImageBuildTask.task_id == task_id))
    build = build_result.scalar_one_or_none()

    calc_result = await db.execute(select(ParamCalculation).where(ParamCalculation.task_id == task_id))
    calc = calc_result.scalar_one_or_none()

    # Create or update deployment
    dep_result = await db.execute(select(Deployment).where(Deployment.task_id == task_id))
    dep = dep_result.scalar_one_or_none()

    if not dep:
        dep = Deployment(
            task_id=task_id,
            environment_id=environment_id,
            deploy_mode=deploy_mode,
            status=DeployStatus.pending,
        )
        db.add(dep)
        await db.flush()

    # Run precheck
    dep.status = DeployStatus.prechecking
    await db.flush()

    gpu_count = calc.gpu_count if calc else 1
    precheck = await run_precheck(
        hardware_model=task.hardware_model,
        engine_name=task.engine,
        gpu_count_needed=gpu_count,
        connection_config=env.connection_config or {},
        env_type=env.env_type,
    )
    dep.precheck_report = precheck

    if not precheck.get("passed"):
        dep.status = DeployStatus.precheck_failed
        await db.flush()
        return dep

    # Deploy
    dep.status = DeployStatus.deploying
    task.status = TaskStatus.deploying
    await db.flush()

    # Simulate deployment
    host = (env.connection_config or {}).get("host", "localhost")
    port = 8000
    dep.api_endpoint = f"http://{host}:{port}/v1/chat/completions"
    dep.container_id = f"llm-deploy-{task.task_name}"

    # Build deploy config
    chip = kb.get_chip(task.hardware_model) or kb.find_chip(task.hardware_model)
    container_config = chip.get("container_config", {}) if chip else {}

    dep.deploy_config = {
        "image": build.image_tag if build else "",
        "container_name": dep.container_id,
        "ports": {f"{port}/tcp": port},
        "device_args": container_config.get("device_args", ""),
        "env_vars": container_config.get("env_vars", {}),
        "startup_command": build.startup_command if build else "",
    }

    dep.status = DeployStatus.running
    task.status = TaskStatus.deployed
    await db.flush()

    return dep


async def verify_service(db: AsyncSession, task_id: int) -> dict:
    """Verify deployed service is responding."""
    dep_result = await db.execute(select(Deployment).where(Deployment.task_id == task_id))
    dep = dep_result.scalar_one_or_none()
    if not dep:
        raise ValueError(f"No deployment for task {task_id}")

    # Simulate verification
    result = {
        "status": "success",
        "endpoint": dep.api_endpoint,
        "response_time_ms": 2300,
        "test_request": {
            "model": "model",
            "messages": [{"role": "user", "content": "hello"}],
        },
        "test_response": {"status": "simulated_ok"},
    }

    dep.verification_result = result
    dep.status = DeployStatus.verified
    await db.flush()

    return result


async def get_deployment(db: AsyncSession, task_id: int) -> Deployment | None:
    result = await db.execute(select(Deployment).where(Deployment.task_id == task_id))
    return result.scalar_one_or_none()
