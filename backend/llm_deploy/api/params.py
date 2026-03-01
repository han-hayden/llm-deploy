"""Parameter calculation API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from llm_deploy.api.deps import get_db
from llm_deploy.schemas.params import (
    ParamCalculateRequest,
    ParamRecalculateRequest,
    ParamCalculateResponse,
    ParamRationale,
    MemoryAllocation,
)
from llm_deploy.services import param_calculator

router = APIRouter(prefix="/api/v1/params", tags=["Parameters"])


@router.post("/calculate", response_model=ParamCalculateResponse)
async def calculate_params(req: ParamCalculateRequest, db: AsyncSession = Depends(get_db)):
    """Calculate optimal inference parameters for a task."""
    try:
        result = await param_calculator.calculate_params(
            db=db,
            task_id=req.task_id,
            gpu_count=req.gpu_count,
            dtype_override=req.dtype,
        )
        return _build_response(result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/calculate", response_model=ParamCalculateResponse)
async def recalculate_params(req: ParamRecalculateRequest, db: AsyncSession = Depends(get_db)):
    """Recalculate parameters with user-modified GPU count."""
    try:
        result = await param_calculator.calculate_params(
            db=db,
            task_id=req.task_id,
            gpu_count=req.gpu_count,
            dtype_override=req.dtype,
        )
        return _build_response(result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def _build_response(result: dict) -> ParamCalculateResponse:
    rationale_items = [
        ParamRationale(param=r["param"], value=r["value"], reason=r["reason"])
        for r in result.get("rationale", [])
    ]
    mem = result.get("memory_allocation", {})
    memory = MemoryAllocation(
        weight_gb=mem.get("weight_gb", 0),
        kv_cache_gb=mem.get("kv_cache_gb", 0),
        runtime_gb=mem.get("runtime_gb", 0),
        reserved_gb=mem.get("reserved_gb", 0),
        total_per_card_gb=mem.get("total_per_card_gb", 0),
    )
    return ParamCalculateResponse(
        task_id=result["task_id"],
        gpu_count=result["gpu_count"],
        dtype=result["dtype"],
        tp=result["tp"],
        pp=result["pp"],
        max_model_len=result["max_model_len"],
        max_num_seqs=result["max_num_seqs"],
        gpu_mem_util=result["gpu_mem_util"],
        enforce_eager=result["enforce_eager"],
        trust_remote_code=result["trust_remote_code"],
        all_params=result.get("all_params", {}),
        rationale=rationale_items,
        memory_allocation=memory,
    )
