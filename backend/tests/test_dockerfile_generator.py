"""Tests for Dockerfile generator."""

import pytest
from llm_deploy.services.dockerfile_generator import generate_dockerfile, generate_image_tag


def test_generate_dockerfile_vllm():
    result = generate_dockerfile(
        engine_name="vllm",
        base_image="vllm/vllm-openai:v0.6.0",
        model_name="Qwen2-7B",
    )
    assert "FROM vllm/vllm-openai:v0.6.0" in result
    assert "Qwen2-7B" in result
    assert "EXPOSE 8000" in result


def test_generate_dockerfile_with_wrapper():
    result = generate_dockerfile(
        engine_name="vllm",
        base_image="vllm/vllm-openai:v0.6.0",
        model_name="test",
        api_wrapper=True,
    )
    assert "api_wrapper" in result
    assert "fastapi" in result.lower()


def test_generate_dockerfile_extra_packages():
    result = generate_dockerfile(
        engine_name="vllm",
        base_image="vllm/vllm-openai:v0.6.0",
        model_name="test",
        extra_pip_packages=["sentencepiece", "protobuf"],
    )
    assert "sentencepiece" in result
    assert "protobuf" in result


def test_generate_image_tag():
    tag = generate_image_tag("Qwen2-7B", "vllm", "H100_80G")
    assert "llm-deploy/" in tag
    assert "qwen2-7b" in tag
    assert "vllm" in tag
    assert "h100" in tag.lower()


def test_generate_dockerfile_mindie():
    result = generate_dockerfile(
        engine_name="mindie",
        base_image="ascendhub.huawei.com/mindie:1.0-cann8.0",
        model_name="Qwen2-72B",
    )
    assert "FROM ascendhub.huawei.com/mindie" in result
