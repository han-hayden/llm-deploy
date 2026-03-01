"""API wrapper injection — determines if OpenAI-compatible wrapper is needed."""


def should_inject_wrapper(engine_name: str, engine_spec: dict | None = None) -> bool:
    """Check if the engine needs an OpenAI-compatible API wrapper.

    Engines like vLLM already expose OpenAI-compatible endpoints.
    Others (MindIE, some vendor engines) may need a FastAPI wrapper.
    """
    # Engines with native OpenAI API support
    native_openai_engines = {"vllm", "vllm-ascend", "vllm-dcu", "maca-vllm", "ix-vllm", "tgi"}

    if engine_name in native_openai_engines:
        return False

    if engine_spec and engine_spec.get("openai_compatible"):
        return False

    # MindIE 1.0+ has native support
    if engine_name == "mindie":
        return False

    return True
