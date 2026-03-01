"""Deployment model — tracks deployment state and results."""

import enum
from datetime import datetime

from sqlalchemy import String, Enum, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from llm_deploy.database import Base


class DeployStatus(str, enum.Enum):
    pending = "pending"
    prechecking = "prechecking"
    precheck_failed = "precheck_failed"
    deploying = "deploying"
    running = "running"
    verifying = "verifying"
    verified = "verified"
    failed = "failed"
    stopped = "stopped"


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("adaptation_tasks.id"), unique=True)
    environment_id: Mapped[int] = mapped_column(ForeignKey("environments.id"))
    deploy_mode: Mapped[str] = mapped_column(String(50), default="docker")  # docker / k8s
    status: Mapped[DeployStatus] = mapped_column(
        Enum(DeployStatus), default=DeployStatus.pending
    )
    precheck_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    api_endpoint: Mapped[str] = mapped_column(String(500), default="")
    deploy_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    verification_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    container_id: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    task: Mapped["AdaptationTask"] = relationship("AdaptationTask", back_populates="deployment")
    environment: Mapped["Environment"] = relationship("Environment")
