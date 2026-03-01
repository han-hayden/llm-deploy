"""Model parser service — parse config.json and Model Card from HuggingFace/ModelScope."""

import re
import math
import logging

from llm_deploy.adapters import huggingface as hf_adapter
from llm_deploy.adapters import modelscope_adapter as ms_adapter

logger = logging.getLogger(__name__)

# dtype -> bytes per parameter
DTYPE_BYTES = {
    "float32": 4,
    "float16": 2,
    "bfloat16": 2,
    "int8": 1,
    "int4": 0.5,
    "fp8": 1,
}


def detect_source(identifier: str) -> tuple[str, str]:
    """Detect source and extract repo_id from identifier.

    Returns: (source, repo_id)
    source: "huggingface" | "modelscope" | "unknown"
    """
    # Check ModelScope URL first
    ms_id = ms_adapter.parse_repo_id(identifier)
    if ms_id:
        return "modelscope", ms_id

    # Check HuggingFace URL or repo_id pattern
    hf_id = hf_adapter.parse_repo_id(identifier)
    if hf_id:
        return "huggingface", hf_id

    # Bare model name — default to HuggingFace
    return "unknown", identifier


async def parse_model(identifier: str, source_hint: str | None = None) -> dict:
    """Parse model metadata from config.json and README.

    Returns a dict with all parsed metadata.
    """
    source, repo_id = detect_source(identifier)

    if source_hint and source_hint != "auto":
        source = source_hint

    result = {
        "model_source": source,
        "repo_id": repo_id,
        "model_name": repo_id.split("/")[-1] if "/" in repo_id else repo_id,
        "architectures": [],
        "param_count": 0,
        "hidden_size": 0,
        "num_layers": 0,
        "num_heads": 0,
        "num_kv_heads": 0,
        "vocab_size": 0,
        "max_position_embeddings": 0,
        "torch_dtype": "",
        "quantization_config": None,
        "weight_files": [],
        "weight_total_size": 0,
        "model_card_info": None,
        "license": "",
    }

    # Fetch config.json
    config = await _fetch_config(source, repo_id)
    if config:
        _extract_config(config, result)

    # Fetch model info from API
    info = await _fetch_info(source, repo_id)
    if info:
        _extract_info(info, result, source)

    # Fetch README for model card parsing
    readme = await _fetch_readme(source, repo_id)
    if readme:
        result["model_card_info"] = parse_model_card(readme)

    # Estimate param count if not parsed
    if result["param_count"] == 0 and result["hidden_size"] > 0:
        result["param_count"] = _estimate_param_count(result)

    # Estimate weight size from param count
    if result["weight_total_size"] == 0 and result["param_count"] > 0:
        dtype = result["torch_dtype"] or "float16"
        bpp = DTYPE_BYTES.get(dtype, 2)
        result["weight_total_size"] = int(result["param_count"] * bpp)

    return result


async def _fetch_config(source: str, repo_id: str) -> dict | None:
    if source == "modelscope":
        return await ms_adapter.fetch_config_json(repo_id)
    return await hf_adapter.fetch_config_json(repo_id)


async def _fetch_info(source: str, repo_id: str) -> dict | None:
    if source == "modelscope":
        return await ms_adapter.fetch_model_info(repo_id)
    return await hf_adapter.fetch_model_info(repo_id)


async def _fetch_readme(source: str, repo_id: str) -> str | None:
    if source == "modelscope":
        return await ms_adapter.fetch_readme(repo_id)
    return await hf_adapter.fetch_readme(repo_id)


def _extract_config(config: dict, result: dict) -> None:
    """Extract fields from config.json."""
    result["architectures"] = config.get("architectures", [])
    result["hidden_size"] = config.get("hidden_size", 0)
    result["num_layers"] = config.get("num_hidden_layers", 0)
    result["num_heads"] = config.get("num_attention_heads", 0)
    result["num_kv_heads"] = config.get("num_key_value_heads", config.get("num_attention_heads", 0))
    result["vocab_size"] = config.get("vocab_size", 0)
    result["max_position_embeddings"] = config.get("max_position_embeddings", 0)
    result["torch_dtype"] = config.get("torch_dtype", "")
    result["quantization_config"] = config.get("quantization_config")


def _extract_info(info: dict, result: dict, source: str) -> None:
    """Extract fields from API model info."""
    if source == "huggingface":
        siblings = info.get("siblings", [])
        weight_files = []
        total_size = 0
        for s in siblings:
            fname = s.get("rfilename", "")
            size = s.get("size", 0)
            if _is_weight_file(fname):
                weight_files.append({"name": fname, "size": size})
                total_size += size
        result["weight_files"] = weight_files
        if total_size > 0:
            result["weight_total_size"] = total_size

        # License
        tags = info.get("tags", [])
        for tag in tags:
            if tag.startswith("license:"):
                result["license"] = tag.replace("license:", "")
                break
    elif source == "modelscope":
        result["license"] = info.get("License", "")


def _is_weight_file(filename: str) -> bool:
    """Check if a file is a model weight file."""
    weight_exts = {".bin", ".safetensors", ".pt", ".pth", ".gguf", ".ggml", ".sft"}
    for ext in weight_exts:
        if filename.endswith(ext):
            return True
    return False


def _estimate_param_count(result: dict) -> int:
    """Rough estimation of parameter count from model dimensions."""
    h = result["hidden_size"]
    l = result["num_layers"]
    v = result["vocab_size"]
    if h == 0 or l == 0:
        return 0
    # Approximate: 12*l*h^2 + v*h (transformer formula)
    return 12 * l * h * h + v * h


def parse_model_card(readme_text: str) -> dict:
    """Parse useful info from README/Model Card text."""
    info: dict = {
        "recommended_framework": None,
        "recommended_command": None,
        "vram_requirement": None,
        "trust_remote_code": False,
    }

    text_lower = readme_text.lower()

    # Detect trust-remote-code requirement
    if "trust_remote_code" in text_lower or "trust-remote-code" in text_lower:
        info["trust_remote_code"] = True

    # Detect recommended framework
    for fw in ["vllm", "mindie", "tgi", "lmdeploy"]:
        if fw in text_lower:
            if info["recommended_framework"] is None:
                info["recommended_framework"] = fw

    # Extract VRAM requirement
    vram_match = re.search(r"(\d+)\s*(?:GB|G)\s*(?:VRAM|GPU|显存|内存)", readme_text, re.IGNORECASE)
    if vram_match:
        info["vram_requirement"] = int(vram_match.group(1))

    return info
