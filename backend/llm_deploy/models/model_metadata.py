"""ModelMetadata — parsed config.json + Model Card information."""

from sqlalchemy import String, Integer, BigInteger, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from llm_deploy.database import Base


class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("adaptation_tasks.id"), unique=True)

    model_name: Mapped[str] = mapped_column(String(255), default="")
    architectures: Mapped[str] = mapped_column(String(500), default="")  # comma-separated
    param_count: Mapped[int] = mapped_column(BigInteger, default=0)
    hidden_size: Mapped[int] = mapped_column(Integer, default=0)
    num_layers: Mapped[int] = mapped_column(Integer, default=0)
    num_heads: Mapped[int] = mapped_column(Integer, default=0)
    num_kv_heads: Mapped[int] = mapped_column(Integer, default=0)
    vocab_size: Mapped[int] = mapped_column(Integer, default=0)
    max_position_embeddings: Mapped[int] = mapped_column(Integer, default=0)
    torch_dtype: Mapped[str] = mapped_column(String(20), default="")
    quantization_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_card_parsed: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    weight_files: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # [{name, size, sha256}]
    weight_total_size: Mapped[int] = mapped_column(BigInteger, default=0)
    license: Mapped[str] = mapped_column(String(100), default="")

    task: Mapped["AdaptationTask"] = relationship("AdaptationTask", back_populates="metadata_info")
