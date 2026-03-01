"""Tests for model parser service."""

import pytest

from llm_deploy.services.model_parser import (
    detect_source,
    parse_model_card,
    _estimate_param_count,
    DTYPE_BYTES,
)


def test_detect_source_huggingface_url():
    source, repo_id = detect_source("https://huggingface.co/Qwen/Qwen2-7B")
    assert source == "huggingface"
    assert repo_id == "Qwen/Qwen2-7B"


def test_detect_source_modelscope_url():
    source, repo_id = detect_source("https://modelscope.cn/models/Qwen/Qwen2-7B")
    assert source == "modelscope"
    assert repo_id == "Qwen/Qwen2-7B"


def test_detect_source_repo_id():
    source, repo_id = detect_source("Qwen/Qwen2-7B")
    assert source == "huggingface"
    assert repo_id == "Qwen/Qwen2-7B"


def test_detect_source_bare_name():
    source, repo_id = detect_source("SomeModel")
    assert source == "unknown"
    assert repo_id == "SomeModel"


def test_detect_source_hf_mirror():
    source, repo_id = detect_source("https://hf-mirror.com/Qwen/Qwen2-7B")
    assert source == "huggingface"
    assert repo_id == "Qwen/Qwen2-7B"


def test_parse_model_card_trust_remote_code():
    readme = """
    # Qwen2-7B
    Usage: Set `trust_remote_code=True` when loading.
    Requires 16GB VRAM for fp16.
    Works well with vLLM.
    """
    info = parse_model_card(readme)
    assert info["trust_remote_code"] is True
    assert info["recommended_framework"] == "vllm"
    assert info["vram_requirement"] == 16


def test_parse_model_card_no_flags():
    readme = "# Simple Model\nA basic language model."
    info = parse_model_card(readme)
    assert info["trust_remote_code"] is False
    assert info["recommended_framework"] is None


def test_estimate_param_count():
    result = {
        "hidden_size": 4096,
        "num_layers": 32,
        "vocab_size": 32000,
    }
    count = _estimate_param_count(result)
    # 12 * 32 * 4096^2 + 32000 * 4096 ≈ 6.58B
    assert count > 6_000_000_000
    assert count < 7_000_000_000


def test_dtype_bytes():
    assert DTYPE_BYTES["float16"] == 2
    assert DTYPE_BYTES["bfloat16"] == 2
    assert DTYPE_BYTES["float32"] == 4
    assert DTYPE_BYTES["int8"] == 1
    assert DTYPE_BYTES["int4"] == 0.5
