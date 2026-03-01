"""NVIDIA container adapter."""


class NvidiaAdapter:
    def get_device_args(self, gpu_ids: list[int]) -> str:
        if not gpu_ids:
            return "--gpus all"
        ids = ",".join(str(i) for i in gpu_ids)
        return f'--gpus "device={ids}"'

    def get_env_vars(self) -> dict[str, str]:
        return {
            "NVIDIA_VISIBLE_DEVICES": "all",
            "NVIDIA_DRIVER_CAPABILITIES": "compute,utility",
        }

    def get_volumes(self) -> list[str]:
        return []

    def get_k8s_resources(self, gpu_count: int) -> dict:
        return {
            "limits": {"nvidia.com/gpu": gpu_count},
            "requests": {"nvidia.com/gpu": gpu_count},
        }
