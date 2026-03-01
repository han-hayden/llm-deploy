"""Tests for YAML knowledge base loader."""

import pytest
from pathlib import Path

from llm_deploy.knowledge.loader import KnowledgeBase


@pytest.fixture
def kb():
    """Load knowledge base from default location."""
    knowledge_base = KnowledgeBase()
    knowledge_base.load()
    return knowledge_base


def test_vendors_loaded(kb: KnowledgeBase):
    vendors = kb.get_all_vendors()
    assert len(vendors) >= 2
    vendor_names = [v["vendor"] for v in vendors]
    assert "NVIDIA" in vendor_names
    assert "Huawei_Ascend" in vendor_names


def test_chips_loaded(kb: KnowledgeBase):
    chips = kb.get_all_chips()
    assert len(chips) >= 5  # 3 NVIDIA + 3 Ascend (at minimum)
    models = [c["model"] for c in chips]
    assert "H100_80G" in models
    assert "910B4" in models


def test_get_chip(kb: KnowledgeBase):
    chip = kb.get_chip("H100_80G")
    assert chip is not None
    assert chip["memory_gb"] == 80
    assert chip["bf16_support"] is True
    assert chip["_vendor"] == "NVIDIA"


def test_get_chip_ascend(kb: KnowledgeBase):
    chip = kb.get_chip("910B4")
    assert chip is not None
    assert chip["memory_gb"] == 64
    assert chip["_vendor"] == "Huawei_Ascend"
    assert chip["_vendor_cn"] == "华为昇腾"


def test_find_chip_fuzzy(kb: KnowledgeBase):
    # Should find by partial match
    chip = kb.find_chip("910B4")
    assert chip is not None
    assert chip["model"] == "910B4"

    chip2 = kb.find_chip("H100")
    assert chip2 is not None
    assert chip2["model"] == "H100_80G"

    chip3 = kb.find_chip("A100_80G")
    assert chip3 is not None


def test_find_chip_not_found(kb: KnowledgeBase):
    chip = kb.find_chip("NonExistentChip12345")
    assert chip is None


def test_compatible_engines(kb: KnowledgeBase):
    engines = kb.get_compatible_engines("H100_80G")
    assert len(engines) >= 2
    engine_names = [e["engine"] for e in engines]
    assert "vllm" in engine_names


def test_compatible_engines_ascend(kb: KnowledgeBase):
    engines = kb.get_compatible_engines("910B4")
    assert len(engines) >= 1
    engine_names = [e["engine"] for e in engines]
    assert "mindie" in engine_names


def test_recommended_engine(kb: KnowledgeBase):
    engine = kb.get_recommended_engine("910B4")
    assert engine is not None
    assert engine["engine"] == "mindie"


def test_get_engine(kb: KnowledgeBase):
    engine = kb.get_engine("vllm")
    assert engine is not None
    assert engine["openai_compatible"] is True
    assert len(engine["parameters"]) > 0


def test_container_config(kb: KnowledgeBase):
    config = kb.get_container_config("H100_80G")
    assert config is not None
    assert config["runtime"] == "nvidia"
    assert "NVIDIA_VISIBLE_DEVICES" in config["env_vars"]


def test_container_config_ascend(kb: KnowledgeBase):
    config = kb.get_container_config("910B4")
    assert config is not None
    assert config["runtime"] == "ascend"
    assert "davinci" in config["device_args"]


def test_chip_driver_info(kb: KnowledgeBase):
    drivers = kb.get_chip_driver_info("H100_80G")
    assert len(drivers) >= 1
    assert "version" in drivers[0]


def test_empty_knowledge_base():
    """Test that an empty KB returns empty results."""
    empty_kb = KnowledgeBase()
    assert empty_kb.get_all_vendors() == []
    assert empty_kb.get_all_chips() == []
    assert empty_kb.get_chip("anything") is None
    assert empty_kb.get_engine("anything") is None
