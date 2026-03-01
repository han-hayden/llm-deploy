"""Pydantic schemas for hardware knowledge base queries."""

from pydantic import BaseModel


class HardwareChipResponse(BaseModel):
    model: str
    display_name: str
    vendor: str
    vendor_cn: str
    memory_gb: int
    memory_type: str = ""
    compute_tflops_fp16: float = 0
    bf16_support: bool = False
    interconnect: str = ""


class HardwareVendorResponse(BaseModel):
    vendor: str
    vendor_cn: str
    chip_count: int
    chips: list[dict]


class HardwareCompatibilityResponse(BaseModel):
    vendors: list[HardwareVendorResponse]
    all_chips: list[HardwareChipResponse]
