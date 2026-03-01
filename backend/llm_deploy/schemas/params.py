"""Pydantic schemas for parameter calculation."""

from pydantic import BaseModel, Field


class ParamCalculateRequest(BaseModel):
    task_id: int
    gpu_count: int | None = None  # If None, auto-calculate
    dtype: str | None = None  # Override dtype


class ParamRecalculateRequest(BaseModel):
    task_id: int
    gpu_count: int
    dtype: str | None = None


class MemoryAllocation(BaseModel):
    weight_gb: float = 0
    kv_cache_gb: float = 0
    runtime_gb: float = 0
    reserved_gb: float = 0
    total_per_card_gb: float = 0


class ParamRationale(BaseModel):
    param: str
    value: str
    reason: str


class ParamCalculateResponse(BaseModel):
    task_id: int
    gpu_count: int = 1
    dtype: str = "fp16"
    tp: int = 1
    pp: int = 1
    max_model_len: int = 2048
    max_num_seqs: int = 32
    gpu_mem_util: float = 0.9
    enforce_eager: bool = False
    trust_remote_code: bool = False
    all_params: dict = {}
    rationale: list[ParamRationale] = []
    memory_allocation: MemoryAllocation = MemoryAllocation()
