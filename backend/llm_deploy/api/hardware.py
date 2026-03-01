"""Hardware knowledge base API routes."""

from fastapi import APIRouter

from llm_deploy.schemas.hardware import (
    HardwareCompatibilityResponse,
    HardwareVendorResponse,
    HardwareChipResponse,
)
from llm_deploy.knowledge.loader import kb

router = APIRouter(prefix="/api/v1/hardware", tags=["Hardware"])


@router.get("/compatibility", response_model=HardwareCompatibilityResponse)
async def get_hardware_compatibility():
    """Get all hardware vendors and chips with compatibility info."""
    vendors = kb.get_all_vendors()
    chips = kb.get_all_chips()

    return HardwareCompatibilityResponse(
        vendors=[HardwareVendorResponse(**v) for v in vendors],
        all_chips=[HardwareChipResponse(**c) for c in chips],
    )


@router.get("/chips/{chip_model}")
async def get_chip_detail(chip_model: str):
    """Get detailed chip information including compatible engines."""
    chip = kb.get_chip(chip_model) or kb.find_chip(chip_model)
    if not chip:
        return {"error": "Chip not found"}

    engines = kb.get_compatible_engines(chip_model) or []
    container = kb.get_container_config(chip_model)
    drivers = kb.get_chip_driver_info(chip_model)

    return {
        "model": chip["model"],
        "display_name": chip["display_name"],
        "vendor": chip.get("_vendor", ""),
        "vendor_cn": chip.get("_vendor_cn", ""),
        "memory_gb": chip["memory_gb"],
        "memory_type": chip.get("memory_type", ""),
        "compute_tflops_fp16": chip.get("compute_tflops_fp16", 0),
        "bf16_support": chip.get("bf16_support", False),
        "interconnect": chip.get("interconnect", ""),
        "compatible_engines": engines,
        "container_config": container,
        "driver_versions": drivers,
    }
