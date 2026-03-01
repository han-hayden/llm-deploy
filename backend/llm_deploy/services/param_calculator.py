"""Parameter calculation engine — computes TP/PP/max_model_len/dtype with rationale.

Core algorithm (SDD §4.3):
1. Determine dtype → check hardware support → fallback if needed
2. weight_memory = param_count × bytes_per_dtype
3. min_cards = ceil(weight_memory / (card_memory × 0.9))
4. tensor_parallel = min valid TP where TP ≥ min_cards and num_heads % TP == 0
5. available_memory → max_kv_memory → max_model_len
6. Merge Model Card recommended values
7. Every parameter includes rationale explaining calculation
8. User modifies gpu_count → recalculate all parameters
"""

import math
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from llm_deploy.models.task import AdaptationTask
from llm_deploy.models.model_metadata import ModelMetadata
from llm_deploy.models.image_build import ParamCalculation
from llm_deploy.knowledge.loader import kb

logger = logging.getLogger(__name__)

DTYPE_BYTES = {"fp32": 4, "fp16": 2, "bf16": 2, "int8": 1, "int4": 0.5, "fp8": 1}
DTYPE_MAP = {"float16": "fp16", "bfloat16": "bf16", "float32": "fp32"}

# KV cache bytes per token per layer per head
# For each head: key + value, each of size head_dim × dtype_bytes
# head_dim = hidden_size / num_heads


def _normalize_dtype(dtype: str) -> str:
    return DTYPE_MAP.get(dtype, dtype)


async def calculate_params(
    db: AsyncSession,
    task_id: int,
    gpu_count: int | None = None,
    dtype_override: str | None = None,
) -> dict:
    """Calculate optimal inference parameters."""
    # Load task and metadata
    task_result = await db.execute(select(AdaptationTask).where(AdaptationTask.id == task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise ValueError(f"Task {task_id} not found")

    meta_result = await db.execute(select(ModelMetadata).where(ModelMetadata.task_id == task_id))
    meta = meta_result.scalar_one_or_none()
    if not meta:
        raise ValueError(f"No metadata for task {task_id}")

    # Get hardware info
    chip = kb.get_chip(task.hardware_model) or kb.find_chip(task.hardware_model)
    if not chip:
        raise ValueError(f"Hardware {task.hardware_model} not found in knowledge base")

    card_memory_gb = chip["memory_gb"]
    card_memory_bytes = card_memory_gb * (1024**3)
    rationale = []

    # Step 1: Determine dtype
    model_dtype = _normalize_dtype(meta.torch_dtype) if meta.torch_dtype else "fp16"
    if dtype_override:
        dtype = _normalize_dtype(dtype_override)
    elif task.dtype:
        dtype = _normalize_dtype(task.dtype)
    else:
        dtype = model_dtype

    # Check hardware dtype support
    if dtype == "bf16" and not chip.get("bf16_support", False):
        rationale.append({"param": "dtype", "value": "fp16",
                         "reason": f"硬件 {chip['display_name']} 不支持 BF16，降级为 FP16"})
        dtype = "fp16"
    else:
        rationale.append({"param": "dtype", "value": dtype,
                         "reason": f"模型原生精度 {meta.torch_dtype or 'auto'}，硬件支持 {dtype.upper()}"})

    bytes_per_param = DTYPE_BYTES.get(dtype, 2)

    # Step 2: Calculate weight memory
    param_count = meta.param_count or 0
    weight_memory_bytes = param_count * bytes_per_param
    weight_memory_gb = weight_memory_bytes / (1024**3)

    # Step 3: Minimum cards needed
    usable_memory = card_memory_gb * 0.9  # 90% utilization
    min_cards = max(1, math.ceil(weight_memory_gb / usable_memory))

    rationale.append({"param": "min_cards", "value": str(min_cards),
                     "reason": f"权重 {weight_memory_gb:.1f} GB / 每卡可用 {usable_memory:.1f} GB = 最少 {min_cards} 张卡"})

    # Step 4: Determine TP (tensor parallel)
    num_heads = meta.num_heads or 1
    num_kv_heads = meta.num_kv_heads or num_heads

    if gpu_count is not None:
        # User specified
        tp = gpu_count
        if num_heads % tp != 0:
            # Find nearest valid TP
            for candidate in [gpu_count, gpu_count + 1, gpu_count - 1, gpu_count + 2]:
                if candidate > 0 and num_heads % candidate == 0:
                    tp = candidate
                    break
        rationale.append({"param": "tensor-parallel-size", "value": str(tp),
                         "reason": f"用户指定 {gpu_count} 张卡，TP={tp} (num_heads={num_heads} 可整除)"})
    else:
        # Auto: find smallest valid TP >= min_cards
        tp = min_cards
        valid_tps = [t for t in [1, 2, 4, 8, 16] if t >= min_cards and num_heads % t == 0]
        tp = valid_tps[0] if valid_tps else min_cards
        rationale.append({"param": "tensor-parallel-size", "value": str(tp),
                         "reason": f"权重需最少 {min_cards} 卡, 从 [1,2,4,8,16] 中选最小可整除 num_heads={num_heads} 的值"})

    actual_gpu_count = gpu_count or tp
    pp = 1  # Pipeline parallel not used in single-node

    # Step 5: Calculate available memory for KV cache
    weight_per_card_gb = weight_memory_gb / tp
    runtime_overhead_gb = min(card_memory_gb * 0.05, 3.0)
    reserved_gb = card_memory_gb * 0.05
    available_for_kv_gb = card_memory_gb * 0.9 - weight_per_card_gb - runtime_overhead_gb - reserved_gb

    if available_for_kv_gb < 0:
        available_for_kv_gb = 0

    # KV cache size per token per layer:
    # 2 (key+value) × head_dim × num_kv_heads / tp × dtype_bytes
    hidden_size = meta.hidden_size or 4096
    head_dim = hidden_size // max(num_heads, 1)
    num_layers = meta.num_layers or 1
    kv_heads_per_tp = max(1, num_kv_heads // tp)
    kv_per_token_bytes = 2 * head_dim * kv_heads_per_tp * num_layers * bytes_per_param
    kv_per_token_gb = kv_per_token_bytes / (1024**3)

    # max_model_len from KV cache budget
    if kv_per_token_gb > 0:
        max_model_len_from_kv = int(available_for_kv_gb / kv_per_token_gb)
    else:
        max_model_len_from_kv = 4096

    # Cap at model's max position embeddings
    model_max_len = meta.max_position_embeddings or 4096
    max_model_len = min(max_model_len_from_kv, model_max_len)

    # Round down to nearest power of 2 or nice number
    nice_lengths = [512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]
    for nl in reversed(nice_lengths):
        if nl <= max_model_len:
            max_model_len = nl
            break

    rationale.append({"param": "max-model-len", "value": str(max_model_len),
                     "reason": f"KV Cache 可用 {available_for_kv_gb:.1f} GB, 每 token {kv_per_token_gb*1024*1024:.2f} KB, "
                               f"模型最大 {model_max_len}, 取 {max_model_len}"})

    # Step 6: max_num_seqs
    kv_for_max_seqs = available_for_kv_gb * 0.8  # Leave 20% headroom
    if kv_per_token_gb > 0 and max_model_len > 0:
        avg_seq_len = max_model_len // 4  # Assume average sequence is 1/4 of max
        kv_per_seq_gb = kv_per_token_gb * avg_seq_len
        max_num_seqs = max(1, int(kv_for_max_seqs / max(kv_per_seq_gb, 1e-10)))
        max_num_seqs = min(max_num_seqs, 256)
    else:
        max_num_seqs = 32

    rationale.append({"param": "max-num-seqs", "value": str(max_num_seqs),
                     "reason": f"基于 KV Cache 容量推算，假设平均序列长度 {max_model_len // 4}"})

    # Step 7: enforce-eager (non-NVIDIA usually needs this)
    vendor = chip.get("_vendor", "")
    enforce_eager = vendor != "NVIDIA"
    if enforce_eager:
        rationale.append({"param": "enforce-eager", "value": "true",
                         "reason": f"{chip['display_name']} 不支持 CUDA Graph，使用 eager 模式"})

    # trust-remote-code from model card
    model_card = meta.model_card_parsed or {}
    trust_remote_code = model_card.get("trust_remote_code", False)
    if trust_remote_code:
        rationale.append({"param": "trust-remote-code", "value": "true",
                         "reason": "Model Card 明确要求 trust-remote-code"})

    # Build memory allocation
    memory_allocation = {
        "weight_gb": round(weight_per_card_gb, 1),
        "kv_cache_gb": round(available_for_kv_gb, 1),
        "runtime_gb": round(runtime_overhead_gb, 1),
        "reserved_gb": round(reserved_gb, 1),
        "total_per_card_gb": card_memory_gb,
    }

    gpu_mem_util = 0.9

    # Build all_params dict
    all_params = {
        "model": f"/models/{meta.model_name}",
        "dtype": dtype,
        "tensor-parallel-size": tp,
        "pipeline-parallel-size": pp,
        "max-model-len": max_model_len,
        "max-num-seqs": max_num_seqs,
        "gpu-memory-utilization": gpu_mem_util,
        "enforce-eager": enforce_eager,
        "trust-remote-code": trust_remote_code,
        "host": "0.0.0.0",
        "port": 8000,
    }

    result = {
        "task_id": task_id,
        "gpu_count": actual_gpu_count,
        "dtype": dtype,
        "tp": tp,
        "pp": pp,
        "max_model_len": max_model_len,
        "max_num_seqs": max_num_seqs,
        "gpu_mem_util": gpu_mem_util,
        "enforce_eager": enforce_eager,
        "trust_remote_code": trust_remote_code,
        "all_params": all_params,
        "rationale": rationale,
        "memory_allocation": memory_allocation,
    }

    # Save to DB
    calc_result = await db.execute(
        select(ParamCalculation).where(ParamCalculation.task_id == task_id)
    )
    calc = calc_result.scalar_one_or_none()
    if calc:
        for k, v in result.items():
            if k != "task_id" and hasattr(calc, k):
                setattr(calc, k, v)
    else:
        calc = ParamCalculation(**result)
        db.add(calc)

    await db.flush()
    return result
