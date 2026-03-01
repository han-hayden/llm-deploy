"""Base container adapter protocol."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ContainerAdapter(Protocol):
    """Protocol for hardware-specific container configuration."""

    def get_device_args(self, gpu_ids: list[int]) -> str:
        """Return Docker device arguments."""
        ...

    def get_env_vars(self) -> dict[str, str]:
        """Return container environment variables."""
        ...

    def get_volumes(self) -> list[str]:
        """Return volume mount arguments."""
        ...

    def get_k8s_resources(self, gpu_count: int) -> dict:
        """Return K8s resource requests/limits."""
        ...
