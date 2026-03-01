"""Pydantic schemas for image build."""

from pydantic import BaseModel


class ImageBuildRequest(BaseModel):
    task_id: int


class ImageBuildResponse(BaseModel):
    id: int
    task_id: int
    engine_name: str = ""
    engine_version: str = ""
    base_image: str = ""
    image_tag: str = ""
    dockerfile_content: str = ""
    startup_command: str = ""
    api_wrapper_injected: bool = False
    status: str = "pending"
    build_log: str = ""

    model_config = {"from_attributes": True}
