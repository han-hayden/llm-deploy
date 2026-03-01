"""Pydantic schemas for download operations."""

from pydantic import BaseModel, Field


class DownloadRequest(BaseModel):
    task_id: int
    source: str = Field("huggingface", description="huggingface or modelscope")
    target_type: str = Field("local", description="local or remote")
    target_env_id: int | None = None
    storage_path: str = Field("", description="下载目标路径，留空则自动生成")


class DownloadProgressResponse(BaseModel):
    id: int
    task_id: int
    source: str = ""
    target_type: str = "local"
    storage_path: str = ""
    total_size: int = 0
    downloaded_size: int = 0
    status: str = "pending"
    speed: float = 0.0
    eta: int = 0
    error_message: str = ""
    progress_percent: float = 0.0

    model_config = {"from_attributes": True}
