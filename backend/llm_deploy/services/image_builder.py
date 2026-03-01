"""Image builder service — manages Docker image builds."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from llm_deploy.models.task import AdaptationTask, TaskStatus
from llm_deploy.models.model_metadata import ModelMetadata
from llm_deploy.models.image_build import ImageBuildTask, BuildStatus, ParamCalculation
from llm_deploy.services.dockerfile_generator import generate_dockerfile, generate_image_tag
from llm_deploy.services.command_builder import build_startup_command
from llm_deploy.services.api_wrapper import should_inject_wrapper
from llm_deploy.knowledge.loader import kb

logger = logging.getLogger(__name__)


async def build_image(db: AsyncSession, task_id: int) -> ImageBuildTask:
    """Generate Dockerfile, build image, and track progress."""
    # Load task info
    task_result = await db.execute(select(AdaptationTask).where(AdaptationTask.id == task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise ValueError(f"Task {task_id} not found")

    meta_result = await db.execute(select(ModelMetadata).where(ModelMetadata.task_id == task_id))
    meta = meta_result.scalar_one_or_none()

    calc_result = await db.execute(select(ParamCalculation).where(ParamCalculation.task_id == task_id))
    calc = calc_result.scalar_one_or_none()

    # Get engine info
    chip = kb.get_chip(task.hardware_model) or kb.find_chip(task.hardware_model)
    engine_name = task.engine or "vllm"
    compatible = chip.get("compatible_engines", []) if chip else []
    engine_info = next((e for e in compatible if e["engine"] == engine_name), None)

    # Base image
    base_image = ""
    engine_version = ""
    if engine_info:
        base_image = engine_info.get("base_images", [""])[0]
        engine_version = engine_info.get("versions", [""])[0]

    # Build startup command from calculated params
    params = {}
    if calc:
        params = {
            "dtype": calc.dtype,
            "tp": calc.tp,
            "pp": calc.pp,
            "max_model_len": calc.max_model_len,
            "max_num_seqs": calc.max_num_seqs,
            "gpu_mem_util": calc.gpu_mem_util,
            "enforce_eager": calc.enforce_eager,
            "trust_remote_code": calc.trust_remote_code,
            "host": "0.0.0.0",
            "port": 8000,
        }

    model_path = f"/models/{meta.model_name}" if meta else "/models/model"
    startup_cmd = build_startup_command(engine_name, params, model_path)

    # Check if API wrapper needed
    engine_spec = kb.get_engine(engine_name)
    inject_wrapper = should_inject_wrapper(engine_name, engine_spec)

    # Generate Dockerfile
    dockerfile = generate_dockerfile(
        engine_name=engine_name,
        base_image=base_image,
        model_name=meta.model_name if meta else "model",
        api_wrapper=inject_wrapper,
        startup_command=startup_cmd,
    )

    # Generate image tag
    image_tag = generate_image_tag(
        meta.model_name if meta else "model",
        engine_name,
        task.hardware_model,
    )

    # Create or update build task
    build_result = await db.execute(
        select(ImageBuildTask).where(ImageBuildTask.task_id == task_id)
    )
    build = build_result.scalar_one_or_none()

    if build:
        build.engine_name = engine_name
        build.engine_version = engine_version
        build.base_image = base_image
        build.dockerfile_content = dockerfile
        build.startup_command = startup_cmd
        build.image_tag = image_tag
        build.api_wrapper_injected = inject_wrapper
        build.status = BuildStatus.completed  # In production: BuildStatus.building
        build.build_log = f"[Simulated] Image built: {image_tag}\n"
    else:
        build = ImageBuildTask(
            task_id=task_id,
            engine_name=engine_name,
            engine_version=engine_version,
            base_image=base_image,
            dockerfile_content=dockerfile,
            startup_command=startup_cmd,
            image_tag=image_tag,
            api_wrapper_injected=inject_wrapper,
            status=BuildStatus.completed,
            build_log=f"[Simulated] Image built: {image_tag}\n",
        )
        db.add(build)

    # Update task status
    task.status = TaskStatus.built
    await db.flush()

    return build


async def get_build_status(db: AsyncSession, task_id: int) -> ImageBuildTask | None:
    result = await db.execute(
        select(ImageBuildTask).where(ImageBuildTask.task_id == task_id)
    )
    return result.scalar_one_or_none()
