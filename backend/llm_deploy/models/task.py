"""AdaptationTask model — the main entity with status state machine."""

import enum
from datetime import datetime

from sqlalchemy import String, Text, Enum, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from llm_deploy.database import Base


class TaskStatus(str, enum.Enum):
    created = "created"
    parsing = "parsing"
    parsed = "parsed"
    downloading = "downloading"
    downloaded = "downloaded"
    download_failed = "download_failed"
    building = "building"
    built = "built"
    build_failed = "build_failed"
    deploying = "deploying"
    deployed = "deployed"
    deploy_failed = "deploy_failed"
    failed = "failed"


class AdaptationTask(Base):
    __tablename__ = "adaptation_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    model_identifier: Mapped[str] = mapped_column(String(500))
    model_source: Mapped[str] = mapped_column(String(50), default="")  # huggingface / modelscope / name
    hardware_model: Mapped[str] = mapped_column(String(100))
    engine: Mapped[str] = mapped_column(String(100), default="")
    dtype: Mapped[str] = mapped_column(String(20), default="")
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.created, index=True
    )
    anomaly_flags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    metadata_info: Mapped["ModelMetadata | None"] = relationship(
        "ModelMetadata", back_populates="task", uselist=False, cascade="all, delete-orphan"
    )
    download_task: Mapped["DownloadTask | None"] = relationship(
        "DownloadTask", back_populates="task", uselist=False, cascade="all, delete-orphan"
    )
    image_build_task: Mapped["ImageBuildTask | None"] = relationship(
        "ImageBuildTask", back_populates="task", uselist=False, cascade="all, delete-orphan"
    )
    param_calculation: Mapped["ParamCalculation | None"] = relationship(
        "ParamCalculation", back_populates="task", uselist=False, cascade="all, delete-orphan"
    )
    deployment: Mapped["Deployment | None"] = relationship(
        "Deployment", back_populates="task", uselist=False, cascade="all, delete-orphan"
    )
