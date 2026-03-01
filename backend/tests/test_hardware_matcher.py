"""Tests for hardware matcher service."""

import pytest

from llm_deploy.knowledge.loader import KnowledgeBase
from llm_deploy.services.hardware_matcher import (
    match_hardware,
    get_hardware_display_info,
    recommend_engine,
    detect_anomalies,
)
from llm_deploy.knowledge.loader import kb


@pytest.fixture(autouse=True)
def load_kb():
    kb.load()


def test_match_hardware_exact():
    chip = match_hardware("H100_80G")
    assert chip is not None
    assert chip["model"] == "H100_80G"


def test_match_hardware_fuzzy():
    chip = match_hardware("910B4")
    assert chip is not None
    assert chip["model"] == "910B4"


def test_match_hardware_not_found():
    chip = match_hardware("NonExistentGPU")
    assert chip is None


def test_get_hardware_display_info():
    chip = match_hardware("H100_80G")
    assert chip is not None
    info = get_hardware_display_info(chip)
    assert info["display_name"] == "H100 80G"
    assert info["vendor"] == "NVIDIA"
    assert info["memory_gb"] == 80


def test_recommend_engine_nvidia():
    chip = match_hardware("H100_80G")
    assert chip is not None
    rec = recommend_engine(chip)
    assert rec["engine"] == "vllm"
    assert "bf16" in rec["available_dtypes"]
    assert len(rec["available_engines"]) >= 2


def test_recommend_engine_ascend():
    chip = match_hardware("910B4")
    assert chip is not None
    rec = recommend_engine(chip)
    assert rec["engine"] == "mindie"
    assert rec["dtype"] == "bf16"


def test_detect_anomalies_large_model():
    model_meta = {
        "weight_total_size": 150 * 1024**3,  # 150 GB
        "model_card_info": None,
        "quantization_config": None,
    }
    chip = match_hardware("910B4")
    assert chip is not None
    rec = recommend_engine(chip)
    flags = detect_anomalies(model_meta, chip, rec)
    # 150GB > 64GB, should flag
    assert any("需至少" in f["message"] for f in flags)


def test_detect_anomalies_trust_remote_code():
    model_meta = {
        "weight_total_size": 10 * 1024**3,
        "model_card_info": {"trust_remote_code": True},
        "quantization_config": None,
    }
    chip = match_hardware("H100_80G")
    assert chip is not None
    rec = recommend_engine(chip)
    flags = detect_anomalies(model_meta, chip, rec)
    assert any("trust-remote-code" in f["message"] for f in flags)


def test_detect_anomalies_quantized():
    model_meta = {
        "weight_total_size": 5 * 1024**3,
        "model_card_info": None,
        "quantization_config": {"bits": 4, "group_size": 128},
    }
    chip = match_hardware("A100_80G")
    assert chip is not None
    rec = recommend_engine(chip)
    flags = detect_anomalies(model_meta, chip, rec)
    assert any("量化" in f["message"] for f in flags)
