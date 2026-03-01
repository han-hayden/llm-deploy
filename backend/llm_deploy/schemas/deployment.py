"""Pydantic schemas for deployment."""

from pydantic import BaseModel, Field


class DeployRequest(BaseModel):
    task_id: int
    environment_id: int
    deploy_mode: str = Field("docker", description="docker or k8s")


class PrecheckRequest(BaseModel):
    task_id: int
    environment_id: int


class VerifyRequest(BaseModel):
    task_id: int


class PrecheckItem(BaseModel):
    name: str
    status: str  # pass / fail / warning
    actual: str = ""
    expected: str = ""
    message: str = ""


class PrecheckResponse(BaseModel):
    passed: bool
    items: list[PrecheckItem]


class DeploymentResponse(BaseModel):
    id: int
    task_id: int
    environment_id: int
    deploy_mode: str
    status: str
    precheck_report: dict | None = None
    api_endpoint: str = ""
    deploy_config: dict | None = None
    verification_result: dict | None = None
    container_id: str = ""

    model_config = {"from_attributes": True}
