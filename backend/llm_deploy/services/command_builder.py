"""Startup command builder — maps calculated params to engine CLI flags."""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from llm_deploy.knowledge.loader import kb

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def build_startup_command(
    engine_name: str,
    params: dict,
    model_path: str = "/models",
) -> str:
    """Build the startup command from calculated parameters."""
    engine_spec = kb.get_engine(engine_name)

    if engine_name in ("vllm", "vllm-ascend", "vllm-dcu", "maca-vllm", "ix-vllm"):
        return _build_vllm_command(params, model_path)
    elif engine_name == "mindie":
        return _build_mindie_command(params, model_path)
    else:
        # Generic: try template, fallback to vllm-style
        return _build_vllm_command(params, model_path)


def _build_vllm_command(params: dict, model_path: str) -> str:
    parts = ["python -m vllm.entrypoints.openai.api_server"]
    parts.append(f"  --model {model_path}")
    parts.append(f"  --dtype {params.get('dtype', 'auto')}")
    parts.append(f"  --tensor-parallel-size {params.get('tp', 1)}")

    if params.get("pp", 1) > 1:
        parts.append(f"  --pipeline-parallel-size {params['pp']}")

    parts.append(f"  --max-model-len {params.get('max_model_len', 4096)}")
    parts.append(f"  --max-num-seqs {params.get('max_num_seqs', 32)}")
    parts.append(f"  --gpu-memory-utilization {params.get('gpu_mem_util', 0.9)}")

    if params.get("enforce_eager"):
        parts.append("  --enforce-eager")
    if params.get("trust_remote_code"):
        parts.append("  --trust-remote-code")

    parts.append(f"  --host {params.get('host', '0.0.0.0')}")
    parts.append(f"  --port {params.get('port', 8000)}")

    return " \\\n".join(parts)


def _build_mindie_command(params: dict, model_path: str) -> str:
    parts = ["mindie-service"]
    parts.append(f"  --model {model_path}")

    tp = params.get("tp", 1)
    npu_list = ",".join(str(i) for i in range(tp))
    parts.append(f"  --npu {npu_list}")

    parts.append(f"  --dtype {params.get('dtype', 'bf16')}")
    parts.append(f"  --max-seq-len {params.get('max_model_len', 4096)}")
    parts.append(f"  --max-batch-size {params.get('max_num_seqs', 32)}")

    if params.get("trust_remote_code"):
        parts.append("  --trust-remote-code")

    parts.append(f"  --host {params.get('host', '0.0.0.0')}")
    parts.append(f"  --port {params.get('port', 8000)}")

    return " \\\n".join(parts)
