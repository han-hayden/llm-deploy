"""Pydantic schemas for task API."""

from datetime import datetime

from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    model_identifier: str = Field(..., description="模型名称或 HuggingFace/ModelScope 链接")
    hardware_model: str = Field(..., description="硬件型号，如 910B4, H100_80G")
    task_name: str | None = Field(None, description="任务名称，留空则自动生成")


class ModelMetadataResponse(BaseModel):
    model_name: str = ""
    architectures: str = ""
    param_count: int = 0
    hidden_size: int = 0
    num_layers: int = 0
    num_heads: int = 0
    num_kv_heads: int = 0
    vocab_size: int = 0
    max_position_embeddings: int = 0
    torch_dtype: str = ""
    quantization_config: dict | None = None
    weight_total_size: int = 0
    license: str = ""

    model_config = {"from_attributes": True}


class HardwareInfoResponse(BaseModel):
    model: str = ""
    display_name: str = ""
    vendor: str = ""
    vendor_cn: str = ""
    memory_gb: int = 0
    memory_type: str = ""
    compute_tflops_fp16: float = 0
    bf16_support: bool = False
    interconnect: str = ""


class RecommendedPlanResponse(BaseModel):
    engine: str = ""
    engine_version: str = ""
    dtype: str = ""
    available_engines: list[dict] = []
    available_dtypes: list[str] = []
    anomaly_flags: list[dict] = []


class TaskResponse(BaseModel):
    id: int
    task_name: str
    model_identifier: str
    model_source: str = ""
    hardware_model: str
    engine: str = ""
    dtype: str = ""
    status: str
    anomaly_flags: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Populated when fetching detail
    metadata_info: ModelMetadataResponse | None = None
    hardware_info: HardwareInfoResponse | None = None
    recommended_plan: RecommendedPlanResponse | None = None

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
