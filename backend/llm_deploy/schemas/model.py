"""Pydantic schemas for model parsing."""

from pydantic import BaseModel


class ModelParseRequest(BaseModel):
    model_identifier: str
    source: str | None = None  # huggingface / modelscope / auto


class ModelParseResponse(BaseModel):
    model_name: str = ""
    model_source: str = ""
    architectures: list[str] = []
    param_count: int = 0
    hidden_size: int = 0
    num_layers: int = 0
    num_heads: int = 0
    num_kv_heads: int = 0
    vocab_size: int = 0
    max_position_embeddings: int = 0
    torch_dtype: str = ""
    quantization_config: dict | None = None
    weight_files: list[dict] = []
    weight_total_size: int = 0
    model_card_info: dict | None = None
    license: str = ""
