"""Hardware matcher service — match hardware from knowledge base and recommend engine/dtype."""

import logging

from llm_deploy.knowledge.loader import kb

logger = logging.getLogger(__name__)


def match_hardware(hardware_model: str) -> dict | None:
    """Look up hardware in knowledge base. Returns chip info or None."""
    # Try exact match first
    chip = kb.get_chip(hardware_model)
    if chip:
        return chip

    # Try fuzzy match
    chip = kb.find_chip(hardware_model)
    return chip


def get_hardware_display_info(chip: dict) -> dict:
    """Build hardware display info from chip data."""
    return {
        "model": chip["model"],
        "display_name": chip["display_name"],
        "vendor": chip["_vendor"],
        "vendor_cn": chip["_vendor_cn"],
        "memory_gb": chip["memory_gb"],
        "memory_type": chip.get("memory_type", ""),
        "compute_tflops_fp16": chip.get("compute_tflops_fp16", 0),
        "bf16_support": chip.get("bf16_support", False),
        "interconnect": chip.get("interconnect", ""),
    }


def recommend_engine(chip: dict) -> dict:
    """Recommend engine + dtype based on hardware and model info.

    Returns dict with recommended engine, available options, and anomaly flags.
    """
    compatible_engines = chip.get("compatible_engines", [])

    if not compatible_engines:
        return {
            "engine": "",
            "engine_version": "",
            "dtype": "fp16",
            "available_engines": [],
            "available_dtypes": ["fp16"],
            "anomaly_flags": [{"type": "warning", "message": "该硬件暂无已知兼容推理引擎"}],
        }

    # First engine is recommended
    rec = compatible_engines[0]
    rec_version = rec["versions"][0] if rec.get("versions") else ""

    # Build available engines list
    available = []
    for eng in compatible_engines:
        ver = eng["versions"][0] if eng.get("versions") else ""
        available.append({
            "engine": eng["engine"],
            "version": ver,
            "base_images": eng.get("base_images", []),
        })

    # Determine available dtypes
    available_dtypes = ["fp16"]
    if chip.get("bf16_support"):
        available_dtypes.insert(0, "bf16")
    if chip.get("fp8_support"):
        available_dtypes.append("fp8")

    # Default dtype: bf16 if supported, else fp16
    default_dtype = "bf16" if chip.get("bf16_support") else "fp16"

    return {
        "engine": rec["engine"],
        "engine_version": rec_version,
        "dtype": default_dtype,
        "available_engines": available,
        "available_dtypes": available_dtypes,
        "anomaly_flags": [],
    }


def detect_anomalies(model_meta: dict, chip: dict, recommendation: dict) -> list[dict]:
    """Detect potential issues and generate anomaly flags."""
    flags = []

    # Check model size vs hardware memory
    weight_size_gb = model_meta.get("weight_total_size", 0) / (1024**3)
    card_memory = chip.get("memory_gb", 0)

    if weight_size_gb > 0 and card_memory > 0:
        if weight_size_gb > card_memory * 8:  # Even 8 cards can't fit
            flags.append({
                "type": "error",
                "message": f"模型权重 ({weight_size_gb:.1f} GB) 过大，即使 8 张 {chip['display_name']} 也无法容纳",
            })
        elif weight_size_gb > card_memory:
            min_cards = int(weight_size_gb / (card_memory * 0.9)) + 1
            flags.append({
                "type": "info",
                "message": f"模型权重 ({weight_size_gb:.1f} GB) 超过单卡显存 ({card_memory} GB)，需至少 {min_cards} 张卡",
            })

    # Check trust-remote-code
    model_card = model_meta.get("model_card_info") or {}
    if model_card.get("trust_remote_code"):
        flags.append({
            "type": "warning",
            "message": "需要 --trust-remote-code（自定义模型代码），已自动添加到启动参数",
        })

    # Quantized model detection
    if model_meta.get("quantization_config"):
        flags.append({
            "type": "info",
            "message": "检测到量化配置，将使用量化精度",
        })

    return flags
