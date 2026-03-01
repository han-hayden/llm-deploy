"""Model parsing API routes."""

from fastapi import APIRouter

from llm_deploy.schemas.model import ModelParseRequest, ModelParseResponse
from llm_deploy.services import model_parser

router = APIRouter(prefix="/api/v1/models", tags=["Models"])


@router.post("/parse", response_model=ModelParseResponse)
async def parse_model(req: ModelParseRequest):
    """Parse model metadata from HuggingFace/ModelScope."""
    result = await model_parser.parse_model(req.model_identifier, req.source)
    return ModelParseResponse(**result)
