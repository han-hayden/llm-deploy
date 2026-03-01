"""DownloadTask — model weight download tracking."""

import enum
from datetime import datetime

from sqlalchemy import String, Integer, BigInteger, Float, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from llm_deploy.database import Base


class DownloadStatus(str, enum.Enum):
    pending = "pending"
    downloading = "downloading"
    paused = "paused"
    verifying = "verifying"
    completed = "completed"
    failed = "failed"


class DownloadTask(Base):
    __tablename__ = "download_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("adaptation_tasks.id"), unique=True)
    source: Mapped[str] = mapped_column(String(50), default="huggingface")  # huggingface / modelscope
    target_type: Mapped[str] = mapped_column(String(20), default="local")  # local / remote
    target_env_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_path: Mapped[str] = mapped_column(String(500), default="")
    total_size: Mapped[int] = mapped_column(BigInteger, default=0)
    downloaded_size: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[DownloadStatus] = mapped_column(
        Enum(DownloadStatus), default=DownloadStatus.pending
    )
    speed: Mapped[float] = mapped_column(Float, default=0.0)  # bytes/sec
    eta: Mapped[int] = mapped_column(Integer, default=0)  # seconds
    error_message: Mapped[str] = mapped_column(String(1000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    task: Mapped["AdaptationTask"] = relationship("AdaptationTask", back_populates="download_task")
