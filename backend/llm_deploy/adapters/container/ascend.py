"""Huawei Ascend container adapter."""


class AscendAdapter:
    def get_device_args(self, gpu_ids: list[int]) -> str:
        parts = []
        for gid in (gpu_ids or [0]):
            parts.append(f"--device /dev/davinci{gid}")
        parts.extend([
            "--device /dev/davinci_manager",
            "--device /dev/hisi_hdc",
        ])
        return " ".join(parts)

    def get_env_vars(self) -> dict[str, str]:
        return {"ASCEND_VISIBLE_DEVICES": "all"}

    def get_volumes(self) -> list[str]:
        return [
            "-v /usr/local/dcmi:/usr/local/dcmi",
            "-v /usr/local/Ascend/driver:/usr/local/Ascend/driver",
        ]

    def get_k8s_resources(self, gpu_count: int) -> dict:
        return {
            "limits": {"huawei.com/Ascend910": gpu_count},
            "requests": {"huawei.com/Ascend910": gpu_count},
        }
