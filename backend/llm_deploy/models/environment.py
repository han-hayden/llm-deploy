"""Environment model — target deployment environments."""

from datetime import datetime

from sqlalchemy import String, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from llm_deploy.database import Base


class Environment(Base):
    __tablename__ = "environments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    env_type: Mapped[str] = mapped_column(String(50))  # docker / k8s
    connection_type: Mapped[str] = mapped_column(String(50))  # ssh / kubeconfig
    connection_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # e.g. {"host": "10.0.1.100", "port": 22, "username": "root", "auth_type": "password"}
    hardware_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # e.g. {"gpu_count": 8, "gpu_model": "910B4", "gpu_memory_gb": 64}
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
