"""Pydantic schemas for environment management."""

from pydantic import BaseModel, Field


class EnvironmentCreateRequest(BaseModel):
    name: str
    env_type: str = Field("docker", description="docker or k8s")
    connection_type: str = Field("ssh", description="ssh or kubeconfig")
    connection_config: dict = Field(default_factory=dict)
    hardware_info: dict | None = None


class EnvironmentResponse(BaseModel):
    id: int
    name: str
    env_type: str
    connection_type: str
    connection_config: dict | None = None
    hardware_info: dict | None = None

    model_config = {"from_attributes": True}


class EnvironmentListResponse(BaseModel):
    items: list[EnvironmentResponse]
    total: int
