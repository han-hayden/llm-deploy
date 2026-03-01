"""Tests for command builder."""

import pytest
from llm_deploy.services.command_builder import build_startup_command
from llm_deploy.knowledge.loader import kb


@pytest.fixture(autouse=True)
def load_kb():
    kb.load()


def test_build_vllm_command():
    params = {
        "dtype": "bf16",
        "tp": 4,
        "pp": 1,
        "max_model_len": 32768,
        "max_num_seqs": 32,
        "gpu_mem_util": 0.9,
        "enforce_eager": False,
        "trust_remote_code": True,
        "host": "0.0.0.0",
        "port": 8000,
    }
    cmd = build_startup_command("vllm", params, "/models/Qwen2-7B")
    assert "vllm.entrypoints.openai.api_server" in cmd
    assert "--model /models/Qwen2-7B" in cmd
    assert "--dtype bf16" in cmd
    assert "--tensor-parallel-size 4" in cmd
    assert "--max-model-len 32768" in cmd
    assert "--trust-remote-code" in cmd
    assert "--enforce-eager" not in cmd  # Should not appear when False


def test_build_vllm_command_enforce_eager():
    params = {"dtype": "fp16", "tp": 1, "pp": 1, "max_model_len": 4096,
              "max_num_seqs": 32, "gpu_mem_util": 0.9,
              "enforce_eager": True, "trust_remote_code": False}
    cmd = build_startup_command("vllm", params, "/models/test")
    assert "--enforce-eager" in cmd
    assert "--trust-remote-code" not in cmd


def test_build_mindie_command():
    params = {
        "dtype": "bf16",
        "tp": 4,
        "max_model_len": 32768,
        "max_num_seqs": 32,
        "trust_remote_code": True,
        "host": "0.0.0.0",
        "port": 8000,
    }
    cmd = build_startup_command("mindie", params, "/models/Qwen2-72B")
    assert "mindie-service" in cmd
    assert "--model /models/Qwen2-72B" in cmd
    assert "--npu 0,1,2,3" in cmd
    assert "--dtype bf16" in cmd
    assert "--max-seq-len 32768" in cmd
