"""ImageBuildTask + ParamCalculation models."""

import enum
from datetime import datetime

from sqlalchemy import (
    String, Integer, Float, Boolean, Text, Enum, DateTime, JSON, ForeignKey, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from llm_deploy.database import Base


class BuildStatus(str, enum.Enum):
    pending = "pending"
    building = "building"
    completed = "completed"
    failed = "failed"


class ImageBuildTask(Base):
    __tablename__ = "image_build_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("adaptation_tasks.id"), unique=True)
    engine_name: Mapped[str] = mapped_column(String(100), default="")
    engine_version: Mapped[str] = mapped_column(String(50), default="")
    base_image: Mapped[str] = mapped_column(String(500), default="")
    dockerfile_content: Mapped[str] = mapped_column(Text, default="")
    startup_command: Mapped[str] = mapped_column(Text, default="")
    image_tag: Mapped[str] = mapped_column(String(500), default="")
    api_wrapper_injected: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[BuildStatus] = mapped_column(
        Enum(BuildStatus), default=BuildStatus.pending
    )
    build_log: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    task: Mapped["AdaptationTask"] = relationship("AdaptationTask", back_populates="image_build_task")


class ParamCalculation(Base):
    __tablename__ = "param_calculations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("adaptation_tasks.id"), unique=True)
    gpu_count: Mapped[int] = mapped_column(Integer, default=1)
    dtype: Mapped[str] = mapped_column(String(20), default="fp16")
    tp: Mapped[int] = mapped_column(Integer, default=1)  # tensor parallel
    pp: Mapped[int] = mapped_column(Integer, default=1)  # pipeline parallel
    max_model_len: Mapped[int] = mapped_column(Integer, default=2048)
    max_num_seqs: Mapped[int] = mapped_column(Integer, default=32)
    gpu_mem_util: Mapped[float] = mapped_column(Float, default=0.9)
    enforce_eager: Mapped[bool] = mapped_column(Boolean, default=False)
    trust_remote_code: Mapped[bool] = mapped_column(Boolean, default=False)
    all_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rationale: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    memory_allocation: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    task: Mapped["AdaptationTask"] = relationship("AdaptationTask", back_populates="param_calculation")
